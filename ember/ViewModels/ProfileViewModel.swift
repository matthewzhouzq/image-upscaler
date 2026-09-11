//
//  ProfileViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class ProfileViewModel {
    private(set) var streaks: [Streak] = []
    private let repository: StreakRepository

    let displayName = "You"
    let initials = "Y"

    init(repository: StreakRepository) {
        self.repository = repository
    }

    func load() {
        streaks = (try? repository.fetchAll()) ?? []
    }

    var totalActiveStreaks: Int {
        streaks.filter { $0.currentStreakCount > 0 }.count
    }

    var longestEver: Int {
        streaks.map(\.longestStreakCount).max() ?? 0
    }
}
