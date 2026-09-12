//
//  SwiftDataEventRepository.swift
//  ember
//

import Foundation
import SwiftData

@MainActor
final class SwiftDataEventRepository: EventRepository {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func fetchAll() throws -> [StreakEvent] {
        let descriptor = FetchDescriptor<StreakEvent>(sortBy: [SortDescriptor(\.createdAt, order: .forward)])
        return try modelContext.fetch(descriptor)
    }

    @discardableResult
    func createEvent(name: String, iconName: String, category: StreakCategory, startDate: Date, invitees: [EventInvitee]) throws -> StreakEvent {
        let event = StreakEvent(name: name, iconName: iconName, category: category, startDate: startDate)
        event.participants.append(EventParticipant(displayName: "You", isCurrentUser: true))
        for invitee in invitees {
            event.participants.append(EventParticipant(
                displayName: invitee.displayName,
                phoneNumber: invitee.phoneNumber,
                isPending: invitee.isPending
            ))
        }
        modelContext.insert(event)
        try save()
        return event
    }

    func delete(_ event: StreakEvent) throws {
        modelContext.delete(event)
        try save()
    }

    func save() throws {
        try modelContext.save()
    }

    func checkIn(_ participant: EventParticipant, photoFileName: String?) throws {
        EventEngine.checkIn(participant, photoFileName: photoFileName)
        try save()
    }

    func refreshBreakStates(_ event: StreakEvent) throws {
        for participant in event.participants {
            EventEngine.evaluateForBreak(participant)
        }
        try save()
    }

    func refreshAllBreakStates() throws {
        for event in try fetchAll() {
            for participant in event.participants {
                EventEngine.evaluateForBreak(participant)
            }
        }
        try save()
    }
}
