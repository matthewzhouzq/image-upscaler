//
//  LeaderboardView.swift
//  ember
//

import SwiftUI

struct LeaderboardView: View {
    @Environment(\.leaderboardService) private var leaderboardService
    @Environment(\.streakRepository) private var streakRepository
    @State private var viewModel: LeaderboardViewModel?

    var body: some View {
        NavigationStack {
            ZStack {
                AmbientBackground()
                VStack(spacing: 0) {
                    categoryFilterBar
                    if let viewModel {
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
            .navigationTitle("Leaderboard")
            .task {
                if viewModel == nil, let streakRepository {
                    viewModel = LeaderboardViewModel(service: leaderboardService, streakRepository: streakRepository)
                }
                await viewModel?.load()
            }
        }
    }

    private var categoryFilterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                filterChip(title: "All", isSelected: viewModel?.selectedCategory == nil) {
                    viewModel?.selectedCategory = nil
                    Task { await viewModel?.load() }
                }
                ForEach(StreakCategory.allCases) { category in
                    filterChip(title: category.rawValue, isSelected: viewModel?.selectedCategory == category) {
                        viewModel?.selectedCategory = category
                        Task { await viewModel?.load() }
                    }
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 12)
        }
    }

    private func filterChip(title: String, isSelected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(.subheadline, design: .rounded).weight(.medium))
                .padding(.horizontal, 14)
                .padding(.vertical, 8)
                .background(
                    Capsule().fill(isSelected ? AnyShapeStyle(AppTheme.flameGradient) : AnyShapeStyle(Color.gray.opacity(0.08)))
                )
                .foregroundStyle(isSelected ? AnyShapeStyle(.white) : AnyShapeStyle(AppTheme.textSecondary))
        }
        .buttonStyle(.plain)
    }
}
