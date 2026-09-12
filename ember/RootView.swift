//
//  RootView.swift
//  ember
//

import SwiftUI
import SwiftData

struct RootView: View {
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        RootTabView()
            .environment(\.streakRepository, SwiftDataStreakRepository(modelContext: modelContext))
            .environment(\.eventRepository, SwiftDataEventRepository(modelContext: modelContext))
            .task {
                let repository = SwiftDataStreakRepository(modelContext: modelContext)
                SeedDataProvider.seedIfNeeded(repository: repository)

                let eventRepository = SwiftDataEventRepository(modelContext: modelContext)
                SeedDataProvider.seedEventsIfNeeded(repository: eventRepository)
            }
    }
}
