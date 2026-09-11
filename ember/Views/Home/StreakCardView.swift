//
//  StreakCardView.swift
//  ember
//

import SwiftUI
import UIKit

struct StreakCardView: View {
    let streak: Streak
    var onCheckIn: () -> Void
    var onRestore: () -> Void

    @State private var pulse = false

    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(streak.category.tint.opacity(0.16))
                    .frame(width: 52, height: 52)
                Image(systemName: streak.iconName)
                    .font(.system(size: 22, weight: .medium))
                    .foregroundStyle(streak.category.tint)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(streak.name)
                    .font(.system(.headline, design: .rounded))
                    .foregroundStyle(AppTheme.textPrimary)
                Text(streak.category.rawValue)
                    .font(.system(.subheadline, design: .rounded))
                    .foregroundStyle(AppTheme.textSecondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 8) {
                FlameBadge(count: streak.currentStreakCount, isBroken: streak.isBroken)
                    .scaleEffect(pulse ? 1.18 : 1.0)

                if streak.isBroken {
                    Button(action: onRestore) {
                        Text("Restore")
                            .font(.system(.caption, design: .rounded).weight(.semibold))
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(AppTheme.dangerRed.opacity(0.12), in: Capsule())
                            .foregroundStyle(AppTheme.dangerRed)
                    }
                    .buttonStyle(.plain)
                } else {
                    Button {
                        triggerCheckIn()
                    } label: {
                        Image(systemName: streak.isCheckedInToday ? "checkmark.circle.fill" : "circle")
                            .font(.system(size: 26))
                            .foregroundStyle(streak.isCheckedInToday ? AppTheme.successGreen : AppTheme.textSecondary.opacity(0.5))
                    }
                    .buttonStyle(.plain)
                    .disabled(streak.isCheckedInToday)
                }
            }
        }
        .padding(16)
        .glassCard()
    }

    private func triggerCheckIn() {
        let generator = UIImpactFeedbackGenerator(style: .medium)
        generator.impactOccurred()
        withAnimation(.spring(response: 0.3, dampingFraction: 0.5)) {
            pulse = true
        }
        onCheckIn()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.6)) {
                pulse = false
            }
        }
    }
}
