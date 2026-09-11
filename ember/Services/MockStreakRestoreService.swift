//
//  MockStreakRestoreService.swift
//  ember
//

import Foundation

final class MockStreakRestoreService: StreakRestoreServicing {
    let price = "$0.99"

    func purchaseRestore(for streak: Streak) async -> RestoreOutcome {
        guard streak.restoreEligible else {
            if let next = streak.nextRestoreAvailableDate {
                return .alreadyRestoredRecently(nextAvailable: next)
            }
            return .failed(reason: "This streak isn't eligible for restore right now.")
        }

        try? await Task.sleep(nanoseconds: 900_000_000)
        return .success
    }
}
