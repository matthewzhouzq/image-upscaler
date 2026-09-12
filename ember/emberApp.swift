//
//  emberApp.swift
//  ember
//
//  Created by Matthew Zhou on 2026-09-11.
//

import SwiftUI
import SwiftData

@main
struct emberApp: App {
    var body: some Scene {
        WindowGroup {
            RootView()
        }
        .modelContainer(for: [Streak.self, StreakEvent.self, EventParticipant.self, EventCheckIn.self])
    }
}
