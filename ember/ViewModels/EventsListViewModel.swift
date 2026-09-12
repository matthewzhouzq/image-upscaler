//
//  EventsListViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class EventsListViewModel {
    private(set) var events: [StreakEvent] = []

    private let repository: EventRepository

    init(repository: EventRepository) {
        self.repository = repository
    }

    func load() {
        try? repository.refreshAllBreakStates()
        events = (try? repository.fetchAll()) ?? []
    }

    func delete(_ event: StreakEvent) {
        try? repository.delete(event)
        load()
    }
}
