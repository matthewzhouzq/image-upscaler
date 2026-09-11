//
//  LeaderboardViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class LeaderboardViewModel {
    private(set) var entries: [LeaderboardEntry] = []
    private(set) var isLoading = false
    var selectedCategory: StreakCategory?

    private let service: LeaderboardServicing
    private let streakRepository: StreakRepository

    init(service: LeaderboardServicing, streakRepository: StreakRepository) {
        self.service = service
        self.streakRepository = streakRepository
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        var fetched = (try? await service.fetchLeaderboard(category: selectedCategory)) ?? []
        if let you = currentUserEntry() {
            fetched.append(you)
        }
        entries = fetched.sorted { $0.currentStreak > $1.currentStreak }
    }

    private func currentUserEntry() -> LeaderboardEntry? {
        guard let streaks = try? streakRepository.fetchAll(), !streaks.isEmpty else { return nil }
        let relevant = selectedCategory.map { cat in streaks.filter { $0.category == cat } } ?? streaks
        guard let best = relevant.max(by: { $0.currentStreakCount < $1.currentStreakCount }) else { return nil }
        return LeaderboardEntry(displayName: "You", category: best.category, currentStreak: best.currentStreakCount, isCurrentUser: true)
    }
}
