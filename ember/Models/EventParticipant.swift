//
//  EventParticipant.swift
//  ember
//

import Foundation
import SwiftData

@Model
final class EventParticipant {
    var id: UUID
    var displayName: String
    var phoneNumber: String?
    var isCurrentUser: Bool
    /// True when this person was invited by SMS and hasn't installed/joined yet — they sit in
    /// standings with no streak until a real backend can tell us they've accepted.
    var isPending: Bool = false
    var currentStreakCount: Int
    var longestStreakCount: Int
    var lastCheckInDate: Date?
    var isBroken: Bool

    var event: StreakEvent?

    @Relationship(deleteRule: .cascade, inverse: \EventCheckIn.participant)
    var checkIns: [EventCheckIn] = []

    init(displayName: String, phoneNumber: String? = nil, isCurrentUser: Bool = false, isPending: Bool = false) {
        self.id = UUID()
        self.displayName = displayName
        self.phoneNumber = phoneNumber
        self.isCurrentUser = isCurrentUser
        self.isPending = isPending
        self.currentStreakCount = 0
        self.longestStreakCount = 0
        self.lastCheckInDate = nil
        self.isBroken = false
    }

    var initials: String {
        let parts = displayName.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }
        return String(letters).uppercased()
    }

    var isCheckedInToday: Bool {
        guard let lastCheckInDate else { return false }
        return Calendar.current.isDateInToday(lastCheckInDate)
    }

    var latestCheckIn: EventCheckIn? {
        checkIns.sorted { $0.date > $1.date }.first
    }
}
