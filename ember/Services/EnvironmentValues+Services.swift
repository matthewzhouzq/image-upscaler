//
//  EnvironmentValues+Services.swift
//  ember
//

import SwiftUI

private struct StreakRepositoryKey: EnvironmentKey {
    static let defaultValue: StreakRepository? = nil
}

private struct LeaderboardServiceKey: EnvironmentKey {
    static let defaultValue: LeaderboardServicing = MockLeaderboardService()
}

private struct StreakRestoreServiceKey: EnvironmentKey {
    static let defaultValue: StreakRestoreServicing = MockStreakRestoreService()
}

extension EnvironmentValues {
    var streakRepository: StreakRepository? {
        get { self[StreakRepositoryKey.self] }
        set { self[StreakRepositoryKey.self] = newValue }
    }

    var leaderboardService: LeaderboardServicing {
        get { self[LeaderboardServiceKey.self] }
        set { self[LeaderboardServiceKey.self] = newValue }
    }

    var streakRestoreService: StreakRestoreServicing {
        get { self[StreakRestoreServiceKey.self] }
        set { self[StreakRestoreServiceKey.self] = newValue }
    }
}
