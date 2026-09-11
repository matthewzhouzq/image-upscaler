//
//  StreakDetailView.swift
//  ember
//

import SwiftUI
import UIKit

struct StreakDetailView: View {
    @State private var viewModel: StreakDetailViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var showingDeleteConfirm = false
    @State private var showingEdit = false
    @State private var showingRestore = false

    private let repository: StreakRepository

    init(streak: Streak, repository: StreakRepository) {
        _viewModel = State(initialValue: StreakDetailViewModel(streak: streak, repository: repository))
        self.repository = repository
    }

    var body: some View {
        ZStack {
            AmbientBackground()
            ScrollView {
                VStack(spacing: 20) {
                    header
                    statsRow
                    HeatmapCalendarView(completedDates: viewModel.streak.completedDates)
                        .glassCard()
                    if viewModel.streak.isBroken {
                        restoreBanner
                    }
                }
                .padding(20)
            }
        }
        .navigationTitle(viewModel.streak.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Menu {
                    Button("Edit", systemImage: "pencil") { showingEdit = true }
                    Button("Delete", systemImage: "trash", role: .destructive) { showingDeleteConfirm = true }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
        .confirmationDialog("Delete this streak?", isPresented: $showingDeleteConfirm, titleVisibility: .visible) {
            Button("Delete", role: .destructive) {
                viewModel.delete()
                dismiss()
            }
        }
        .sheet(isPresented: $showingEdit) {
            AddEditStreakView(repository: repository, editing: viewModel.streak) {}
        }
        .sheet(isPresented: $showingRestore) {
            RestoreStreakSheet(streak: viewModel.streak, repository: repository) {}
        }
    }

    private var header: some View {
        VStack(spacing: 12) {
            ZStack {
                Circle()
                    .fill(viewModel.streak.category.tint.opacity(0.16))
                    .frame(width: 84, height: 84)
                Image(systemName: viewModel.streak.iconName)
                    .font(.system(size: 34, weight: .medium))
                    .foregroundStyle(viewModel.streak.category.tint)
            }
            Text(viewModel.streak.category.rawValue)
                .font(.system(.subheadline, design: .rounded).weight(.medium))
                .foregroundStyle(AppTheme.textSecondary)

            Button {
                let generator = UIImpactFeedbackGenerator(style: .medium)
                generator.impactOccurred()
                withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                    viewModel.checkIn()
                }
            } label: {
                Label(
                    viewModel.streak.isCheckedInToday ? "Checked In Today" : "Check In",
                    systemImage: viewModel.streak.isCheckedInToday ? "checkmark.circle.fill" : "flame.fill"
                )
                .font(.system(.headline, design: .rounded))
                .padding(.horizontal, 24)
                .padding(.vertical, 12)
                .background(
                    viewModel.streak.isCheckedInToday ? AnyShapeStyle(AppTheme.successGreen.opacity(0.15)) : AnyShapeStyle(AppTheme.flameGradient),
                    in: Capsule()
                )
                .foregroundStyle(viewModel.streak.isCheckedInToday ? AppTheme.successGreen : .white)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.streak.isCheckedInToday || viewModel.streak.isBroken)
        }
        .padding(.top, 12)
    }

    private var statsRow: some View {
        HStack(spacing: 12) {
            StatTile(title: "Current", value: "\(viewModel.streak.currentStreakCount)", icon: "flame.fill", tint: AppTheme.flame)
            StatTile(title: "Longest", value: "\(viewModel.streak.longestStreakCount)", icon: "trophy.fill", tint: AppTheme.creativity)
        }
    }

    private var restoreBanner: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Streak broken", systemImage: "flame")
                .font(.system(.headline, design: .rounded))
                .foregroundStyle(AppTheme.dangerRed)
            Text("You missed a day. Restore to pick up right where you left off.")
                .font(.system(.subheadline, design: .rounded))
                .foregroundStyle(AppTheme.textSecondary)
            Button {
                showingRestore = true
            } label: {
                Text("Restore Streak")
                    .font(.system(.subheadline, design: .rounded).weight(.semibold))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 10)
                    .background(AppTheme.dangerRed.opacity(0.12), in: Capsule())
                    .foregroundStyle(AppTheme.dangerRed)
            }
            .buttonStyle(.plain)
        }
        .padding(16)
        .glassCard()
    }
}

private struct StatTile: View {
    let title: String
    let value: String
    let icon: String
    let tint: Color

    var body: some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .foregroundStyle(tint)
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
}
