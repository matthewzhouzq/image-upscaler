//
//  LeaderboardViewModel.swift
//  ember
//

import Foundation
import GameKit
import Observation

@Observable
@MainActor
final class LeaderboardViewModel {
    private(set) var entries: [LeaderboardEntry] = []
    private(set) var isLoading = false
    var scope: GKLeaderboard.PlayerScope = .global

    private let gameCenter: GameCenterManager
    private let streakRepository: StreakRepository?

    var isAuthenticated: Bool { gameCenter.isAuthenticated }
    var errorMessage: String? { gameCenter.lastError }

    init(gameCenter: GameCenterManager, streakRepository: StreakRepository?) {
        self.gameCenter = gameCenter
        self.streakRepository = streakRepository
    }

    func signIn() {
        if gameCenter.isAuthenticated {
            Task { await load() }
        } else {
            gameCenter.authenticate()
        }
    }

    func setScope(_ newScope: GKLeaderboard.PlayerScope) {
        scope = newScope
        Task { await load() }
    }

    func load() async {
        guard gameCenter.isAuthenticated else { return }
        isLoading = true
        defer { isLoading = false }

        if let bestStreak = bestLocalStreak() {
            await gameCenter.submitScore(bestStreak)
        }
        entries = await gameCenter.loadEntries(scope: scope)
    }

    private func bestLocalStreak() -> Int? {
        guard let streaks = try? streakRepository?.fetchAll(), !streaks.isEmpty else { return nil }
        return streaks.map(\.currentStreakCount).max()
    }
}
