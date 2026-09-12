//
//  GameCenterManager.swift
//  ember
//
//  Real backend for the Leaderboard tab: Game Center identity, score
//  submission, and global/friends ranking. Requires the Game Center
//  capability (ember/ember.entitlements) and a leaderboard with this ID
//  created in App Store Connect before scores/entries will actually work —
//  until then this degrades gracefully (empty state + error text), it won't crash.
//

import Foundation
import GameKit
import Observation
import UIKit

@Observable
@MainActor
final class GameCenterManager {
    static let longestStreakLeaderboardID = "com.mwd.ember.longeststreak"

    private(set) var isAuthenticated = false
    private(set) var authViewController: UIViewController?
    private(set) var lastError: String?

    var localPlayer: GKLocalPlayer { GKLocalPlayer.local }

    func authenticate() {
        localPlayer.authenticateHandler = { [weak self] viewController, error in
            guard let self else { return }
            Task { @MainActor in
                if let viewController {
                    self.authViewController = viewController
                    return
                }
                self.authViewController = nil
                self.isAuthenticated = self.localPlayer.isAuthenticated
                self.lastError = error?.localizedDescription
            }
        }
    }

    func submitScore(_ score: Int) async {
        guard isAuthenticated else { return }
        do {
            try await GKLeaderboard.submitScore(
                score,
                context: 0,
                player: localPlayer,
                leaderboardIDs: [Self.longestStreakLeaderboardID]
            )
        } catch {
            lastError = error.localizedDescription
        }
    }

    func loadEntries(scope: GKLeaderboard.PlayerScope) async -> [LeaderboardEntry] {
        guard isAuthenticated else { return [] }
        do {
            let leaderboards = try await GKLeaderboard.loadLeaderboards(IDs: [Self.longestStreakLeaderboardID])
            guard let leaderboard = leaderboards.first else {
                lastError = "Leaderboard not set up yet in App Store Connect."
                return []
            }

            let (localEntry, entries, _) = try await leaderboard.loadEntries(
                for: scope,
                timeScope: .allTime,
                range: NSRange(location: 1, length: 25)
            )

            var results = entries.map { entry in
                LeaderboardEntry(
                    displayName: entry.player.displayName,
                    currentStreak: entry.score,
                    isCurrentUser: entry.player.gamePlayerID == localPlayer.gamePlayerID
                )
            }

            if let localEntry, !results.contains(where: { $0.isCurrentUser }) {
                results.append(LeaderboardEntry(
                    displayName: localEntry.player.displayName,
                    currentStreak: localEntry.score,
                    isCurrentUser: true
                ))
            }

            lastError = nil
            return results
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }
}
