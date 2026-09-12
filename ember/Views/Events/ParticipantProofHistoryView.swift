//
//  ParticipantProofHistoryView.swift
//  ember
//

import SwiftUI

struct ParticipantProofHistoryView: View {
    let participant: EventParticipant
    @Environment(\.dismiss) private var dismiss

    private var sortedCheckIns: [EventCheckIn] {
        participant.checkIns.sorted { $0.date > $1.date }
    }

    private let columns = [GridItem(.adaptive(minimum: 100), spacing: 10)]

    var body: some View {
        NavigationStack {
            ZStack {
                AmbientBackground()
                ScrollView {
                    if sortedCheckIns.isEmpty {
                        Text("No check-ins yet")
                            .font(.system(.subheadline, design: .rounded))
                            .foregroundStyle(AppTheme.textSecondary)
                            .padding(.top, 60)
                    } else {
                        LazyVGrid(columns: columns, spacing: 10) {
                            ForEach(sortedCheckIns) { checkIn in
                                VStack(spacing: 6) {
                                    ZStack {
                                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                                            .fill(Color.gray.opacity(0.08))
                                        if let fileName = checkIn.photoFileName {
                                            ProofThumbnail(fileName: fileName)
                                                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                                        } else {
                                            Image(systemName: "checkmark.circle.fill")
                                                .foregroundStyle(AppTheme.successGreen)
                                        }
                                    }
                                    .frame(height: 100)

                                    Text(checkIn.date.formatted(date: .abbreviated, time: .omitted))
                                        .font(.system(.caption2, design: .rounded))
                                        .foregroundStyle(AppTheme.textSecondary)
                                }
                            }
                        }
                        .padding(20)
                    }
                }
            }
            .navigationTitle(participant.isCurrentUser ? "Your Check-Ins" : "\(participant.displayName)'s Check-Ins")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
        }
    }
}
