//
//  StreakDetailViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class StreakDetailViewModel {
    let streak: Streak
    private let repository: StreakRepository

    init(streak: Streak, repository: StreakRepository) {
        self.streak = streak
        self.repository = repository
    }

    func checkIn() {
        try? repository.checkIn(streak)
    }

    func delete() {
        try? repository.delete(streak)
    }
}
