//
//  HomeView.swift
//  ember
//

import SwiftUI

struct HomeView: View {
    @Environment(\.streakRepository) private var repository
    @State private var viewModel: HomeViewModel?
    @State private var showingAddStreak = false
    @State private var streakForRestore: Streak?

    var body: some View {
        NavigationStack {
            ZStack {
                AmbientBackground()

                ScrollView {
                    if let viewModel, viewModel.streaks.isEmpty {
                        EmptyStreaksView { showingAddStreak = true }
                            .padding(.top, 80)
                    } else if let viewModel {
                        LazyVStack(spacing: 14) {
                            ForEach(viewModel.streaks) { streak in
                                NavigationLink(value: streak) {
                                    StreakCardView(
                                        streak: streak,
                                        onCheckIn: { viewModel.checkIn(streak) },
                                        onRestore: { streakForRestore = streak }
                                    )
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.top, 12)
                        .padding(.bottom, 32)
                    }
                }
            }
            .navigationTitle("Ember")
            .navigationDestination(for: Streak.self) { streak in
                if let repository {
                    StreakDetailView(streak: streak, repository: repository)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showingAddStreak = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 22))
                    }
                }
            }
            .sheet(isPresented: $showingAddStreak) {
                if let repository {
                    AddEditStreakView(repository: repository) {
                        viewModel?.load()
                    }
                }
            }
            .sheet(item: $streakForRestore) { streak in
                if let repository {
                    RestoreStreakSheet(streak: streak, repository: repository) {
                        viewModel?.load()
                    }
                }
            }
            .task {
                if viewModel == nil, let repository {
                    viewModel = HomeViewModel(repository: repository)
                }
                viewModel?.load()
            }
        }
    }
}
