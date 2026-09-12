//
//  CreateEventViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class CreateEventViewModel {
    var name: String = ""
    var iconName: String = StreakIconLibrary.defaultIcon
    var category: StreakCategory = .fitness
    var startDate: Date = Calendar.current.startOfDay(for: .now)
    var selectedInvitees: [EventInvitee] = []

    private let repository: EventRepository

    var canSave: Bool { !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    init(repository: EventRepository) {
        self.repository = repository
    }

    func removeInvitee(_ invitee: EventInvitee) {
        selectedInvitees.removeAll { $0.id == invitee.id }
    }

    @discardableResult
    func save() -> StreakEvent? {
        try? repository.createEvent(
            name: name.trimmingCharacters(in: .whitespacesAndNewlines),
            iconName: iconName,
            category: category,
            startDate: startDate,
            invitees: selectedInvitees
        )
    }
}
