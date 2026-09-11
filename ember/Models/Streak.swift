//
//  Streak.swift
//  ember
//

import Foundation
import SwiftData

@Model
final class Streak {
    var id: UUID
    var name: String
    var iconName: String
    var categoryRawValue: String
    var currentStreakCount: Int
    var longestStreakCount: Int
    var preBreakStreakCount: Int
    var completedDates: [Date]
    var lastCheckInDate: Date?
    var isBroken: Bool
    var lastRestoreDate: Date?
    var createdAt: Date

    init(
        name: String,
        iconName: String,
        category: StreakCategory,
        currentStreakCount: Int = 0,
        longestStreakCount: Int = 0,
        completedDates: [Date] = [],
        lastCheckInDate: Date? = nil,
        isBroken: Bool = false,
        lastRestoreDate: Date? = nil,
        createdAt: Date = .now
    ) {
        self.id = UUID()
        self.name = name
        self.iconName = iconName
        self.categoryRawValue = category.rawValue
        self.currentStreakCount = currentStreakCount
        self.longestStreakCount = longestStreakCount
        self.preBreakStreakCount = 0
        self.completedDates = completedDates
        self.lastCheckInDate = lastCheckInDate
        self.isBroken = isBroken
        self.lastRestoreDate = lastRestoreDate
        self.createdAt = createdAt
    }

    var category: StreakCategory {
        get { StreakCategory(rawValue: categoryRawValue) ?? .productivity }
        set { categoryRawValue = newValue.rawValue }
    }

    var isCheckedInToday: Bool {
        guard let lastCheckInDate else { return false }
        return Calendar.current.isDateInToday(lastCheckInDate)
    }

    var restoreEligible: Bool {
        guard isBroken else { return false }
        guard let lastRestoreDate else { return true }
        let days = Calendar.current.dateComponents([.day], from: lastRestoreDate, to: .now).day ?? 0
        return days >= 30
    }

    var nextRestoreAvailableDate: Date? {
        guard let lastRestoreDate else { return nil }
        return Calendar.current.date(byAdding: .day, value: 30, to: lastRestoreDate)
    }
}
