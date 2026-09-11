//
//  StreakRestoreServicing.swift
//  ember
//
//  Purchase seam for the streak-restore IAP. MockStreakRestoreService only
//  simulates a transaction (delay + eligibility check); once real money is
//  involved, a StoreKit2-backed implementation drops in here and the
//  restore application logic in StreakEngine/StreakRepository is unchanged.
//

import Foundation

enum RestoreOutcome {
    case success
    case alreadyRestoredRecently(nextAvailable: Date)
    case failed(reason: String)
}

protocol StreakRestoreServicing {
    var price: String { get }
    func purchaseRestore(for streak: Streak) async -> RestoreOutcome
}
