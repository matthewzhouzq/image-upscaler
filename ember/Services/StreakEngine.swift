//
//  StreakEngine.swift
//  ember
//

import Foundation

/// Pure streak business logic: check-ins, daily-miss resets, and restores.
enum StreakEngine {
    static func checkIn(_ streak: Streak, referenceDate: Date = .now) {
        let calendar = Calendar.current
        guard !streak.isCheckedInToday else { return }

        streak.currentStreakCount += 1
        streak.longestStreakCount = max(streak.longestStreakCount, streak.currentStreakCount)
        streak.completedDates.append(calendar.startOfDay(for: referenceDate))
        streak.lastCheckInDate = referenceDate
        streak.isBroken = false
    }

    @discardableResult
    static func evaluateForBreak(_ streak: Streak, referenceDate: Date = .now) -> Bool {
        let calendar = Calendar.current
        guard let lastCheckInDate = streak.lastCheckInDate, streak.currentStreakCount > 0 else { return false }

        let daysSinceLastCheckIn = calendar.dateComponents(
            [.day],
            from: calendar.startOfDay(for: lastCheckInDate),
            to: calendar.startOfDay(for: referenceDate)
        ).day ?? 0

        guard daysSinceLastCheckIn > 1 else { return false }

        streak.preBreakStreakCount = streak.currentStreakCount
        streak.currentStreakCount = 0
        streak.isBroken = true
        return true
    }

    static func restore(_ streak: Streak, referenceDate: Date = .now) {
        let calendar = Calendar.current
        streak.currentStreakCount = max(streak.preBreakStreakCount, 1)
        streak.longestStreakCount = max(streak.longestStreakCount, streak.currentStreakCount)
        streak.completedDates.append(calendar.startOfDay(for: referenceDate))
        streak.lastCheckInDate = referenceDate
        streak.isBroken = false
        streak.lastRestoreDate = referenceDate
    }
}
