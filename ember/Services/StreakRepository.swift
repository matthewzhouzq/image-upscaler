//
//  StreakRepository.swift
//  ember
//
//  Data-layer seam: today this is backed by SwiftData (see
//  SwiftDataStreakRepository), but the view/view-model layer only ever talks
//  to this protocol, so a Firebase/Supabase-backed implementation can be
//  swapped in later without touching any view code.
//

import Foundation

@MainActor
protocol StreakRepository {
    func fetchAll() throws -> [Streak]
    func add(_ streak: Streak) throws
    func delete(_ streak: Streak) throws
    func save() throws
    func checkIn(_ streak: Streak) throws
    func restore(_ streak: Streak) throws
    func refreshBreakStates() throws
}
