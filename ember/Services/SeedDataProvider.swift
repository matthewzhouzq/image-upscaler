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

    @MainActor
    static func seedEventsIfNeeded(repository: EventRepository) {
        guard let existing = try? repository.fetchAll(), existing.isEmpty else { return }

        let calendar = Calendar.current
        let startDate = calendar.date(byAdding: .day, value: -6, to: Date()) ?? Date()

        let invitees = ["Jordan Blake", "Riya Kapoor", "Talia Osei"].map {
            EventInvitee(displayName: $0, phoneNumber: nil, isPending: false)
        }
        guard let event = try? repository.createEvent(
            name: "30-Day Fitness Challenge",
            iconName: "flame.fill",
            category: .fitness,
            startDate: startDate,
            invitees: invitees
        ) else { return }

        func days(ago: Int) -> Date {
            calendar.startOfDay(for: calendar.date(byAdding: .day, value: -ago, to: Date()) ?? Date())
        }

        for participant in event.participants {
            switch participant.displayName {
            case "You":
                participant.currentStreakCount = 4
                participant.longestStreakCount = 4
                participant.lastCheckInDate = days(ago: 0)
                participant.checkIns = (0..<4).map { EventCheckIn(date: days(ago: $0)) }
            case "Jordan Blake":
                participant.currentStreakCount = 6
                participant.longestStreakCount = 6
                participant.lastCheckInDate = days(ago: 0)
                participant.checkIns = (0..<6).map { EventCheckIn(date: days(ago: $0)) }
            case "Riya Kapoor":
                participant.currentStreakCount = 0
                participant.longestStreakCount = 3
                participant.lastCheckInDate = days(ago: 3)
                participant.isBroken = true
                participant.checkIns = (3..<6).map { EventCheckIn(date: days(ago: $0)) }
            case "Talia Osei":
                participant.currentStreakCount = 2
                participant.longestStreakCount = 2
                participant.lastCheckInDate = days(ago: 0)
                participant.checkIns = (0..<2).map { EventCheckIn(date: days(ago: $0)) }
            default:
                break
            }
        }

        try? repository.save()
    }
}
