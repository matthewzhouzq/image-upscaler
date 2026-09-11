//
//  LeaderboardServicing.swift
//  ember
//
//  Seam for the leaderboard data source. MockLeaderboardService fills this
//  with realistic dummy data for the prototype; a Firebase/Supabase-backed
//  implementation can conform later without changing LeaderboardViewModel.
//

import Foundation

protocol LeaderboardServicing {
    func fetchLeaderboard(category: StreakCategory?) async throws -> [LeaderboardEntry]
}
