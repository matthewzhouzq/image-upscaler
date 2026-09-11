//
//  MockLeaderboardService.swift
//  ember
//

import Foundation

final class MockLeaderboardService: LeaderboardServicing {
    private let allEntries: [LeaderboardEntry] = MockLeaderboardService.makeMockEntries()

    func fetchLeaderboard(category: StreakCategory?) async throws -> [LeaderboardEntry] {
        try? await Task.sleep(nanoseconds: 250_000_000)
        let filtered = category.map { cat in allEntries.filter { $0.category == cat } } ?? allEntries
        return filtered.sorted { $0.currentStreak > $1.currentStreak }
    }

    private static func makeMockEntries() -> [LeaderboardEntry] {
        [
            LeaderboardEntry(displayName: "Ava Chen", category: .fitness, currentStreak: 182),
            LeaderboardEntry(displayName: "Marcus Reid", category: .mindfulness, currentStreak: 164),
            LeaderboardEntry(displayName: "Priya Nair", category: .learning, currentStreak: 151),
            LeaderboardEntry(displayName: "Leo Fontaine", category: .fitness, currentStreak: 139),
            LeaderboardEntry(displayName: "Sofia Marquez", category: .health, currentStreak: 128),
            LeaderboardEntry(displayName: "Noah Kim", category: .productivity, currentStreak: 117),
            LeaderboardEntry(displayName: "Isla Thompson", category: .creativity, currentStreak: 109),
            LeaderboardEntry(displayName: "Ethan Brooks", category: .social, currentStreak: 98),
            LeaderboardEntry(displayName: "Zara Ahmed", category: .finance, currentStreak: 92),
            LeaderboardEntry(displayName: "Dylan Ortiz", category: .fitness, currentStreak: 87),
            LeaderboardEntry(displayName: "Maya Lindqvist", category: .mindfulness, currentStreak: 81),
            LeaderboardEntry(displayName: "Oliver Grant", category: .learning, currentStreak: 74),
            LeaderboardEntry(displayName: "Chloe Bennett", category: .health, currentStreak: 68),
            LeaderboardEntry(displayName: "Hana Suzuki", category: .productivity, currentStreak: 61),
            LeaderboardEntry(displayName: "Gabriel Silva", category: .creativity, currentStreak: 55)
        ]
    }
}
