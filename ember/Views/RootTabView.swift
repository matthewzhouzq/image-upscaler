//
//  RootTabView.swift
//  ember
//

import SwiftUI

struct RootTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Streaks", systemImage: "flame.fill") }

            EventsListView()
                .tabItem { Label("Events", systemImage: "person.3.fill") }

            LeaderboardView()
                .tabItem { Label("Leaderboard", systemImage: "trophy.fill") }

            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.fill") }
        }
        .tint(AppTheme.flame)
    }
}
