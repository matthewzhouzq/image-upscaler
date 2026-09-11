//
//  SwiftDataStreakRepository.swift
//  ember
//

import Foundation
import SwiftData

@MainActor
final class SwiftDataStreakRepository: StreakRepository {
    private let modelContext: ModelContext

    init(modelContext: ModelContext) {
        self.modelContext = modelContext
    }

    func fetchAll() throws -> [Streak] {
        let descriptor = FetchDescriptor<Streak>(sortBy: [SortDescriptor(\.createdAt, order: .forward)])
        return try modelContext.fetch(descriptor)
    }

    func add(_ streak: Streak) throws {
        modelContext.insert(streak)
        try save()
    }

    func delete(_ streak: Streak) throws {
        modelContext.delete(streak)
        try save()
    }

    func save() throws {
        try modelContext.save()
    }

    func checkIn(_ streak: Streak) throws {
        StreakEngine.checkIn(streak)
        try save()
    }

    func restore(_ streak: Streak) throws {
        StreakEngine.restore(streak)
        try save()
    }

    func refreshBreakStates() throws {
        for streak in try fetchAll() {
            StreakEngine.evaluateForBreak(streak)
        }
        try save()
    }
}
