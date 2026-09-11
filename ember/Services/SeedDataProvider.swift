//
//  SeedDataProvider.swift
//  ember
//

import Foundation

enum SeedDataProvider {
    @MainActor
    static func seedIfNeeded(repository: StreakRepository) {
        guard let existing = try? repository.fetchAll(), existing.isEmpty else { return }

        let calendar = Calendar.current
        let today = Date()

        func days(ago: Int) -> Date {
            calendar.startOfDay(for: calendar.date(byAdding: .day, value: -ago, to: today) ?? today)
        }

        let run = Streak(
            name: "Run 5km",
            iconName: "figure.run",
            category: .fitness,
            currentStreakCount: 6,
            longestStreakCount: 14,
            completedDates: (0..<6).map { days(ago: $0) },
            lastCheckInDate: days(ago: 0)
        )

        let read = Streak(
            name: "Read 20 pages",
            iconName: "book.fill",
            category: .learning,
            currentStreakCount: 3,
            longestStreakCount: 21,
            completedDates: (0..<3).map { days(ago: $0) },
            lastCheckInDate: days(ago: 0)
        )

        let meditate = Streak(
            name: "Meditate",
            iconName: "brain.head.profile",
            category: .mindfulness,
            currentStreakCount: 0,
            longestStreakCount: 9,
            completedDates: (3..<10).map { days(ago: $0) },
            lastCheckInDate: days(ago: 3),
            isBroken: true
        )
        meditate.preBreakStreakCount = 7

        let sugar = Streak(
            name: "No Sugar",
            iconName: "leaf.fill",
            category: .health
        )

        for streak in [run, read, meditate, sugar] {
            try? repository.add(streak)
        }
    }
}
