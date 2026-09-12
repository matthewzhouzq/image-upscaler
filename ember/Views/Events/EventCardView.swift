//
//  EventCardView.swift
//  ember
//

import SwiftUI

struct EventCardView: View {
    let event: StreakEvent

    private var you: EventParticipant? {
        event.participants.first { $0.isCurrentUser }
    }

    private var rank: Int? {
        guard let you else { return nil }
        let sorted = event.participants.sorted { $0.currentStreakCount > $1.currentStreakCount }
        guard let index = sorted.firstIndex(where: { $0.id == you.id }) else { return nil }
        return index + 1
    }

    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(event.category.tint.opacity(0.16))
                    .frame(width: 52, height: 52)
                Image(systemName: event.iconName)
                    .font(.system(size: 22, weight: .medium))
                    .foregroundStyle(event.category.tint)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(event.name)
                    .font(.system(.headline, design: .rounded))
                    .foregroundStyle(AppTheme.textPrimary)
                Text(subtitle)
                    .font(.system(.subheadline, design: .rounded))
                    .foregroundStyle(AppTheme.textSecondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 6) {
                if let you {
                    FlameBadge(count: you.currentStreakCount, isBroken: you.isBroken)
                }
                if let rank {
                    Text("Rank #\(rank)")
                        .font(.system(.caption, design: .rounded).weight(.semibold))
                        .foregroundStyle(AppTheme.textSecondary)
                }
            }
        }
        .padding(16)
        .glassCard()
    }

    private var subtitle: String {
        if event.hasStarted {
            return "Day \(event.dayNumber) · \(event.participants.count) racing"
        } else {
            return "Starts \(event.startDate.formatted(date: .abbreviated, time: .omitted))"
        }
    }
}
