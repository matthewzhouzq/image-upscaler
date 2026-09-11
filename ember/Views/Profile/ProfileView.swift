//
//  ProfileView.swift
//  ember
//

import SwiftUI

struct ProfileView: View {
    @Environment(\.streakRepository) private var repository
    @State private var viewModel: ProfileViewModel?
    @State private var appearance = "System"

    var body: some View {
        NavigationStack {
            ZStack {
                AmbientBackground()
                ScrollView {
                    VStack(spacing: 20) {
                        profileHeader
                        statsSection
                        streaksSection
                        settingsSection
                    }
                    .padding(20)
                }
            }
            .navigationTitle("Profile")
            .task {
                if viewModel == nil, let repository {
                    viewModel = ProfileViewModel(repository: repository)
                }
                viewModel?.load()
            }
        }
    }

    private var profileHeader: some View {
        VStack(spacing: 10) {
            ZStack {
                Circle()
                    .fill(AppTheme.flameGradient)
                    .frame(width: 76, height: 76)
                Text(viewModel?.initials ?? "Y")
                    .font(.system(.title, design: .rounded).weight(.bold))
                    .foregroundStyle(.white)
            }
            Text(viewModel?.displayName ?? "You")
                .font(.system(.title3, design: .rounded).weight(.semibold))
                .foregroundStyle(AppTheme.textPrimary)
        }
        .padding(.top, 12)
    }

    private var statsSection: some View {
        HStack(spacing: 12) {
            profileStat(title: "Active Streaks", value: "\(viewModel?.totalActiveStreaks ?? 0)")
            profileStat(title: "Best Ever", value: "\(viewModel?.longestEver ?? 0)")
        }
    }

    private func profileStat(title: String, value: String) -> some View {
        VStack(spacing: 6) {
            Text(value)
                .font(.system(.title2, design: .rounded).weight(.bold))
                .foregroundStyle(AppTheme.textPrimary)
            Text(title)
                .font(.system(.caption, design: .rounded))
                .foregroundStyle(AppTheme.textSecondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .glassCard()
    }

    private var streaksSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Your Streaks")
                .font(.system(.headline, design: .rounded))
                .foregroundStyle(AppTheme.textPrimary)

            VStack(spacing: 8) {
                ForEach(viewModel?.streaks ?? []) { streak in
                    HStack {
                        Image(systemName: streak.iconName)
                            .foregroundStyle(streak.category.tint)
                            .frame(width: 24)
                        Text(streak.name)
                            .font(.system(.subheadline, design: .rounded))
                            .foregroundStyle(AppTheme.textPrimary)
                        Spacer()
                        FlameBadge(count: streak.currentStreakCount, size: 14)
                    }
                    .padding(.vertical, 4)
                }
            }
            .padding(16)
            .glassCard()
        }
    }

    private var settingsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Settings")
                .font(.system(.headline, design: .rounded))
                .foregroundStyle(AppTheme.textPrimary)

            HStack {
                Label("Appearance", systemImage: "circle.lefthalf.filled")
                Spacer()
                Text(appearance)
                    .foregroundStyle(AppTheme.textSecondary)
                Text("Soon")
                    .font(.system(.caption2, design: .rounded).weight(.semibold))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.gray.opacity(0.15), in: Capsule())
                    .foregroundStyle(AppTheme.textSecondary)
            }
            .font(.system(.subheadline, design: .rounded))
            .foregroundStyle(AppTheme.textPrimary)
            .padding(16)
            .opacity(0.6)
            .glassCard()
        }
    }
}
