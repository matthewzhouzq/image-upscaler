//
//  EmptyEventsView.swift
//  ember
//

import SwiftUI

struct EmptyEventsView: View {
    var onCreate: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "person.3.fill")
                .font(.system(size: 44, weight: .light))
                .foregroundStyle(AppTheme.flameGradient)
            Text("No events yet")
                .font(.system(.title3, design: .rounded).weight(.semibold))
                .foregroundStyle(AppTheme.textPrimary)
            Text("Start a challenge with friends. Everyone begins on day one — longest streak wins.")
                .font(.system(.subheadline, design: .rounded))
                .foregroundStyle(AppTheme.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Button(action: onCreate) {
                Label("Start an Event", systemImage: "plus")
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
