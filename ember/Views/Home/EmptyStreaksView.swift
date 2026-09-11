//
//  EmptyStreaksView.swift
//  ember
//

import SwiftUI

struct EmptyStreaksView: View {
    var onAdd: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "flame")
                .font(.system(size: 48, weight: .light))
                .foregroundStyle(AppTheme.flameGradient)
            Text("No streaks yet")
                .font(.system(.title3, design: .rounded).weight(.semibold))
                .foregroundStyle(AppTheme.textPrimary)
            Text("Start something small today. Consistency beats intensity.")
                .font(.system(.subheadline, design: .rounded))
                .foregroundStyle(AppTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Button(action: onAdd) {
                Label("New Streak", systemImage: "plus")
                    .font(.system(.subheadline, design: .rounded).weight(.semibold))
                    .padding(.horizontal, 20)
                    .padding(.vertical, 12)
                    .background(AppTheme.flameGradient, in: Capsule())
                    .foregroundStyle(.white)
            }
            .buttonStyle(.plain)
            .padding(.top, 4)
        }
        .padding(40)
        .glassCard()
        .padding(.horizontal, 24)
    }
}
