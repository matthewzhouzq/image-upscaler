//
//  EventRepository.swift
//  ember
//
//  Data-layer seam for streak events, mirroring StreakRepository. Backed by
//  SwiftData today; a Firebase/Supabase-backed implementation can replace it
//  later so events actually sync between friends' devices.
//

import Foundation

@MainActor
protocol EventRepository {
    func fetchAll() throws -> [StreakEvent]
    @discardableResult
    func createEvent(name: String, iconName: String, category: StreakCategory, startDate: Date, invitees: [EventInvitee]) throws -> StreakEvent
    func delete(_ event: StreakEvent) throws
    func save() throws
    func checkIn(_ participant: EventParticipant, photoFileName: String?) throws
    func refreshBreakStates(_ event: StreakEvent) throws
    func refreshAllBreakStates() throws
}
