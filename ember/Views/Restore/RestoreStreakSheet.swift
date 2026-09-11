//
//  RestoreStreakSheet.swift
//  ember
//

import SwiftUI

struct RestoreStreakSheet: View {
    @State private var viewModel: RestoreStreakViewModel
    @Environment(\.dismiss) private var dismiss
    var onComplete: () -> Void

    init(streak: Streak, repository: StreakRepository, onComplete: @escaping () -> Void) {
        _viewModel = State(initialValue: RestoreStreakViewModel(streak: streak, restoreService: MockStreakRestoreService(), repository: repository))
        self.onComplete = onComplete
    }

    var body: some View {
        ZStack {
            AmbientBackground()
            VStack(spacing: 24) {
                Capsule()
                    .fill(Color.gray.opacity(0.3))
                    .frame(width: 40, height: 5)
                    .padding(.top, 8)

                Image(systemName: "flame.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(AppTheme.flameGradient)

                VStack(spacing: 8) {
                    Text("Restore Your Streak")
                        .font(.system(.title2, design: .rounded).weight(.bold))
                        .foregroundStyle(AppTheme.textPrimary)
                    Text("\(viewModel.streak.name) had a \(viewModel.streak.preBreakStreakCount)-day streak. Restore it now and keep your momentum.")
                        .font(.system(.subheadline, design: .rounded))
                        .foregroundStyle(AppTheme.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 24)
                }

                VStack(alignment: .leading, spacing: 12) {
                    benefitRow(icon: "arrow.counterclockwise", text: "Continue from day \(viewModel.streak.preBreakStreakCount)")
                    benefitRow(icon: "calendar.badge.clock", text: "One restore per streak every 30 days")
                    benefitRow(icon: "checkmark.seal", text: "One-time purchase, no subscription")
                }
                .padding(20)
                .glassCard()
                .padding(.horizontal, 20)

                Spacer()

                actionArea
            }
            .padding(.bottom, 24)
        }
        .presentationDetents([.height(520)])
        .presentationDragIndicator(.hidden)
    }

    private func benefitRow(icon: String, text: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .foregroundStyle(AppTheme.flame)
                .frame(width: 24)
            Text(text)
                .font(.system(.subheadline, design: .rounded))
                .foregroundStyle(AppTheme.textPrimary)
        }
    }

    @ViewBuilder
    private var actionArea: some View {
        switch viewModel.phase {
        case .idle, .purchasing:
            Button {
                Task {
                    await viewModel.purchaseRestore()
                    if case .success = viewModel.phase {
                        onComplete()
                    }
                }
            } label: {
                HStack {
                    if viewModel.phase == .purchasing {
                        ProgressView().tint(.white)
                    } else {
                        Text("Restore Streak — \(viewModel.price)")
                            .font(.system(.headline, design: .rounded))
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(AppTheme.flameGradient, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                .foregroundStyle(.white)
            }
            .buttonStyle(.plain)
            .disabled(viewModel.phase == .purchasing)
            .padding(.horizontal, 20)

        case .success:
            VStack(spacing: 12) {
                Image(systemName: "checkmark.circle.fill")
                    .font(.system(size: 32))
                    .foregroundStyle(AppTheme.successGreen)
                Text("Streak restored!")
                    .font(.system(.headline, design: .rounded))
                    .foregroundStyle(AppTheme.textPrimary)
                Button("Done") { dismiss() }
                    .buttonStyle(.plain)
                    .font(.system(.subheadline, design: .rounded).weight(.semibold))
                    .foregroundStyle(AppTheme.flame)
            }

        case .ineligible(let next):
            VStack(spacing: 10) {
                Text("Already restored recently")
                    .font(.system(.headline, design: .rounded))
                    .foregroundStyle(AppTheme.textPrimary)
                Text("Next restore available \(next.formatted(date: .abbreviated, time: .omitted)).")
                    .font(.system(.subheadline, design: .rounded))
                    .foregroundStyle(AppTheme.textSecondary)
                Button("Close") { dismiss() }
                    .buttonStyle(.plain)
                    .padding(.top, 4)
            }
            .padding(.horizontal, 20)

        case .failed(let reason):
            VStack(spacing: 10) {
                Text("Couldn't restore")
                    .font(.system(.headline, design: .rounded))
                    .foregroundStyle(AppTheme.textPrimary)
                Text(reason)
                    .font(.system(.subheadline, design: .rounded))
                    .foregroundStyle(AppTheme.textSecondary)
                Button("Close") { dismiss() }
                    .buttonStyle(.plain)
                    .padding(.top, 4)
            }
            .padding(.horizontal, 20)
        }
    }
}
