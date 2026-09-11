//
//  HomeViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class HomeViewModel {
    private(set) var streaks: [Streak] = []

    private let repository: StreakRepository

    init(repository: StreakRepository) {
        self.repository = repository
    }

    func load() {
        try? repository.refreshBreakStates()
        streaks = (try? repository.fetchAll()) ?? []
    }

    func checkIn(_ streak: Streak) {
        try? repository.checkIn(streak)
        load()
    }

    func delete(_ streak: Streak) {
        try? repository.delete(streak)
        load()
    }
}
