//
//  LeaderboardView.swift
//  ember
//

import SwiftUI
import GameKit

struct LeaderboardView: View {
    @Environment(\.gameCenterManager) private var gameCenterManager
    @Environment(\.streakRepository) private var streakRepository
    @State private var viewModel: LeaderboardViewModel?

    var body: some View {
        NavigationStack {
            ZStack {
                AmbientBackground()
                content
            }
            .navigationTitle("Leaderboard")
            .task {
                if viewModel == nil {
                    viewModel = LeaderboardViewModel(gameCenter: gameCenterManager, streakRepository: streakRepository)
                }
                viewModel?.signIn()
            }
            .onChange(of: gameCenterManager.isAuthenticated) { _, isAuthenticated in
                if isAuthenticated {
                    Task { await viewModel?.load() }
                }
            }
            .background(GameCenterAuthPresenter(viewControllerToPresent: gameCenterManager.authViewController))
        }
    }

    @ViewBuilder
    private var content: some View {
        if let viewModel {
            if !viewModel.isAuthenticated {
                signInPrompt(viewModel)
            } else {
                VStack(spacing: 0) {
                    scopePicker(viewModel)

                    if viewModel.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if viewModel.entries.isEmpty {
                        emptyState(viewModel)
                    } else {
                        ScrollView {
                            LazyVStack(spacing: 10) {
                                ForEach(Array(viewModel.entries.enumerated()), id: \.element.id) { index, entry in
                                    LeaderboardRowView(rank: index + 1, entry: entry)
                                }
                            }
                            .padding(.horizontal, 20)
                            .padding(.vertical, 16)
                        }
                    }
                }
            }
        }
    }

    private func scopePicker(_ viewModel: LeaderboardViewModel) -> some View {
        Picker("Scope", selection: Binding(
            get: { viewModel.scope },
            set: { viewModel.setScope($0) }
        )) {
            Text("Global").tag(GKLeaderboard.PlayerScope.global)
            Text("Friends").tag(GKLeaderboard.PlayerScope.friendsOnly)
        }
        .pickerStyle(.segmented)
        .padding()
    }

    private func signInPrompt(_ viewModel: LeaderboardViewModel) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "gamecontroller.fill")
                .font(.system(size: 44, weight: .light))
                .foregroundStyle(AppTheme.flameGradient)
            Text("Sign in to Game Center")
                .font(.system(.title3, design: .rounded).weight(.semibold))
                .foregroundStyle(AppTheme.textPrimary)
            Text("See how your longest streak stacks up against friends and everyone else on Ember.")
                .font(.system(.subheadline, design: .rounded))
                .foregroundStyle(AppTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.system(.caption, design: .rounded))
                    .foregroundStyle(AppTheme.dangerRed)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }

            Button {
                viewModel.signIn()
            } label: {
                Text("Sign In")
                    .font(.system(.subheadline, design: .rounded).weight(.semibold))
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(AppTheme.flameGradient, in: Capsule())
                    .foregroundStyle(.white)
            }
            .buttonStyle(.plain)
        }
        .padding(40)
        .glassCard()
        .padding(.horizontal, 24)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func emptyState(_ viewModel: LeaderboardViewModel) -> some View {
        VStack(spacing: 12) {
            Image(systemName: "trophy")
                .font(.system(size: 36))
                .foregroundStyle(AppTheme.textSecondary)
            Text("No scores yet")
                .font(.system(.subheadline, design: .rounded).weight(.semibold))
                .foregroundStyle(AppTheme.textPrimary)
            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.system(.caption, design: .rounded))
                    .foregroundStyle(AppTheme.textSecondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
