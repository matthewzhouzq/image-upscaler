//
//  RestoreStreakViewModel.swift
//  ember
//

import Foundation
import Observation

enum RestorePhase: Equatable {
    case idle
    case purchasing
    case success
    case ineligible(nextAvailable: Date)
    case failed(String)
}

@Observable
@MainActor
final class RestoreStreakViewModel {
    let streak: Streak
    private(set) var phase: RestorePhase = .idle

    private let restoreService: StreakRestoreServicing
    private let repository: StreakRepository

    var price: String { restoreService.price }

    init(streak: Streak, restoreService: StreakRestoreServicing, repository: StreakRepository) {
        self.streak = streak
        self.restoreService = restoreService
        self.repository = repository
    }

    func purchaseRestore() async {
        phase = .purchasing
        let outcome = await restoreService.purchaseRestore(for: streak)
        switch outcome {
        case .success:
            try? repository.restore(streak)
            phase = .success
        case .alreadyRestoredRecently(let next):
            phase = .ineligible(nextAvailable: next)
        case .failed(let reason):
            phase = .failed(reason)
        }
    }
}
