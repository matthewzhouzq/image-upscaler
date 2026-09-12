//
//  StreakEvent.swift
//  ember
//

import Foundation
import SwiftData

@Model
final class StreakEvent {
    var id: UUID
    var name: String
    var iconName: String
    var categoryRawValue: String
    var startDate: Date
    var createdAt: Date
    var inviteCode: String

    @Relationship(deleteRule: .cascade, inverse: \EventParticipant.event)
    var participants: [EventParticipant] = []

    init(
        name: String,
        iconName: String,
        category: StreakCategory,
        startDate: Date,
        createdAt: Date = .now
    ) {
        self.id = UUID()
        self.name = name
        self.iconName = iconName
        self.categoryRawValue = category.rawValue
        self.startDate = Calendar.current.startOfDay(for: startDate)
        self.createdAt = createdAt
        self.inviteCode = StreakEvent.makeInviteCode()
    }

    var category: StreakCategory {
        get { StreakCategory(rawValue: categoryRawValue) ?? .productivity }
        set { categoryRawValue = newValue.rawValue }
    }

    var hasStarted: Bool {
        Calendar.current.startOfDay(for: .now) >= startDate
    }

    /// 1-indexed day count since the event began (Day 1 on the start date).
    var dayNumber: Int {
        let days = Calendar.current.dateComponents([.day], from: startDate, to: Calendar.current.startOfDay(for: .now)).day ?? 0
        return max(days + 1, 1)
    }

    private static func makeInviteCode() -> String {
        let characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        return String((0..<6).map { _ in characters.randomElement()! })
    }
}
