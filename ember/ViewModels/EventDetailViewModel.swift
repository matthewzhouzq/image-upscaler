//
//  EventDetailViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class EventDetailViewModel {
    let event: StreakEvent
    private(set) var participants: [EventParticipant] = []

    private let repository: EventRepository
    private let photoStore: PhotoStoring

    init(event: StreakEvent, repository: EventRepository, photoStore: PhotoStoring) {
        self.event = event
        self.repository = repository
        self.photoStore = photoStore
        self.participants = event.participants
    }

    var rankedParticipants: [EventParticipant] {
        participants.sorted { $0.currentStreakCount > $1.currentStreakCount }
    }

    var currentUserParticipant: EventParticipant? {
        participants.first { $0.isCurrentUser }
    }

    func refresh() {
        try? repository.refreshBreakStates(event)
        participants = event.participants
    }

    func checkIn(photoData: Data?) {
        guard let participant = currentUserParticipant else { return }
        var fileName: String?
        if let photoData {
            fileName = try? photoStore.save(photoData)
        }
        try? repository.checkIn(participant, photoFileName: fileName)
        participants = event.participants
    }

    func delete() {
        try? repository.delete(event)
    }
}
