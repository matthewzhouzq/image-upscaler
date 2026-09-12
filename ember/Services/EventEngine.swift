//
//  EventEngine.swift
//  ember
//
//  Pure event-participant streak logic. Deliberately has no restore path —
//  unlike a personal streak, a competitive event streak can't be bought back.
//

import Foundation

enum EventEngine {
    static func checkIn(_ participant: EventParticipant, photoFileName: String?, referenceDate: Date = .now) {
        guard !participant.isCheckedInToday else { return }

        participant.currentStreakCount += 1
        participant.longestStreakCount = max(participant.longestStreakCount, participant.currentStreakCount)
        participant.lastCheckInDate = referenceDate
        participant.isBroken = false

        let checkIn = EventCheckIn(date: Calendar.current.startOfDay(for: referenceDate), photoFileName: photoFileName)
        participant.checkIns.append(checkIn)
    }

    @discardableResult
    static func evaluateForBreak(_ participant: EventParticipant, referenceDate: Date = .now) -> Bool {
        let calendar = Calendar.current
        guard let lastCheckInDate = participant.lastCheckInDate, participant.currentStreakCount > 0 else { return false }

        let daysSinceLastCheckIn = calendar.dateComponents(
            [.day],
            from: calendar.startOfDay(for: lastCheckInDate),
            to: calendar.startOfDay(for: referenceDate)
        ).day ?? 0

        guard daysSinceLastCheckIn > 1 else { return false }

        participant.currentStreakCount = 0
        participant.isBroken = true
        return true
    }
}
