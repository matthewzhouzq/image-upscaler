//
//  LeaderboardEntry.swift
//  ember
//

import Foundation

struct LeaderboardEntry: Identifiable, Hashable {
    let id: UUID
    let displayName: String
    let initials: String
    let category: StreakCategory
    let currentStreak: Int
    let isCurrentUser: Bool

    init(
        id: UUID = UUID(),
        displayName: String,
        category: StreakCategory,
        currentStreak: Int,
        isCurrentUser: Bool = false
    ) {
        self.id = id
        self.displayName = displayName
        self.initials = LeaderboardEntry.makeInitials(from: displayName)
        self.category = category
        self.currentStreak = currentStreak
        self.isCurrentUser = isCurrentUser
    }

    private static func makeInitials(from name: String) -> String {
        let parts = name.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }
        return String(letters).uppercased()
    }
}
