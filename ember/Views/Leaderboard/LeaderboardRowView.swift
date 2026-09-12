//
//  LeaderboardRowView.swift
//  ember
//

import SwiftUI

struct LeaderboardRowView: View {
    let rank: Int
    let entry: LeaderboardEntry

    var body: some View {
        HStack(spacing: 14) {
            Text("\(rank)")
                .font(.system(.subheadline, design: .rounded).weight(.bold))
                .foregroundStyle(rank <= 3 ? AppTheme.flame : AppTheme.textSecondary)
                .frame(width: 24)

            ZStack {
                Circle()
                    .fill(AppTheme.flame.opacity(0.16))
                    .frame(width: 40, height: 40)
                Text(entry.initials)
                    .font(.system(.caption, design: .rounded).weight(.bold))
                    .foregroundStyle(AppTheme.flame)
            }

            Text(entry.displayName)
                .font(.system(.subheadline, design: .rounded).weight(.semibold))
                .foregroundStyle(AppTheme.textPrimary)

            Spacer()

            FlameBadge(count: entry.currentStreak, size: 15)
        }
        .padding(14)
        .background(entry.isCurrentUser ? AppTheme.flame.opacity(0.08) : Color.clear, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .glassCard(cornerRadius: 18)
    }
}
