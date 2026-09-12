//
//  EventDetailView.swift
//  ember
//

import SwiftUI
import UIKit

struct EventDetailView: View {
    @State private var viewModel: EventDetailViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var showingCheckIn = false
    @State private var showingDeleteConfirm = false
    @State private var selectedParticipant: EventParticipant?
    @State private var copiedCode = false

    init(event: StreakEvent, repository: EventRepository) {
        _viewModel = State(initialValue: EventDetailViewModel(event: event, repository: repository, photoStore: FileSystemPhotoStore()))
    }

    var body: some View {
        ZStack {
            AmbientBackground()
            ScrollView {
                VStack(spacing: 20) {
                    header
                    checkInCard
                    participantList
                }
                .padding(20)
            }
        }
        .navigationTitle(viewModel.event.name)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Menu {
                    Button {
                        UIPasteboard.general.string = viewModel.event.inviteCode
                        withAnimation { copiedCode = true }
                    } label: {
                        Label("Copy Invite Code", systemImage: "doc.on.doc")
                    }
                    Button("Delete Event", systemImage: "trash", role: .destructive) {
                        showingDeleteConfirm = true
                    }
                } label: {
                    Image(systemName: "ellipsis.circle")
                }
            }
        }
        .confirmationDialog("Delete this event?", isPresented: $showingDeleteConfirm, titleVisibility: .visible) {
            Button("Delete", role: .destructive) {
                viewModel.delete()
                dismiss()
            }
        }
        .sheet(isPresented: $showingCheckIn) {
            EventCheckInSheet { photoData in
                viewModel.checkIn(photoData: photoData)
            }
        }
        .sheet(item: $selectedParticipant) { participant in
            ParticipantProofHistoryView(participant: participant)
        }
        .overlay(alignment: .top) {
            if copiedCode {
                Text("Invite code copied")
                    .font(.system(.caption, design: .rounded).weight(.semibold))
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(.ultraThinMaterial, in: Capsule())
                    .padding(.top, 8)
                    .transition(.move(edge: .top).combined(with: .opacity))
                    .onAppear {
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.6) {
                            withAnimation { copiedCode = false }
                        }
                    }
            }
        }
        .task { viewModel.refresh() }
    }

    private var header: some View {
        VStack(spacing: 10) {
            ZStack {
                Circle()
                    .fill(viewModel.event.category.tint.opacity(0.16))
                    .frame(width: 76, height: 76)
                Image(systemName: viewModel.event.iconName)
                    .font(.system(size: 30, weight: .medium))
                    .foregroundStyle(viewModel.event.category.tint)
            }
            Text(viewModel.event.hasStarted ? "Day \(viewModel.event.dayNumber)" : "Starts \(viewModel.event.startDate.formatted(date: .abbreviated, time: .omitted))")
                .font(.system(.subheadline, design: .rounded).weight(.medium))
                .foregroundStyle(AppTheme.textSecondary)
            Text("Invite code: \(viewModel.event.inviteCode)")
                .font(.system(.caption, design: .rounded))
                .foregroundStyle(AppTheme.textSecondary.opacity(0.7))
        }
        .padding(.top, 12)
    }

    private var checkInCard: some View {
        VStack(spacing: 12) {
            if let you = viewModel.currentUserParticipant {
                FlameBadge(count: you.currentStreakCount, isBroken: you.isBroken, size: 28)

                Button {
                    showingCheckIn = true
                } label: {
                    Label(
                        you.isCheckedInToday ? "Checked In Today" : "Check In with Photo",
                        systemImage: you.isCheckedInToday ? "checkmark.circle.fill" : "camera.fill"
                    )
                    .font(.system(.headline, design: .rounded))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(
                        you.isCheckedInToday ? AnyShapeStyle(AppTheme.successGreen.opacity(0.15)) : AnyShapeStyle(AppTheme.flameGradient),
                        in: RoundedRectangle(cornerRadius: 18, style: .continuous)
                    )
                    .foregroundStyle(you.isCheckedInToday ? AppTheme.successGreen : .white)
                }
                .buttonStyle(.plain)
                .disabled(you.isCheckedInToday || !viewModel.event.hasStarted)

                if !viewModel.event.hasStarted {
                    Text("Check-ins open on \(viewModel.event.startDate.formatted(date: .abbreviated, time: .omitted))")
                        .font(.system(.caption, design: .rounded))
                        .foregroundStyle(AppTheme.textSecondary)
                }
            }
        }
        .padding(20)
        .glassCard()
    }

    private var participantList: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Standings")
                .font(.system(.headline, design: .rounded))
                .foregroundStyle(AppTheme.textPrimary)

            VStack(spacing: 10) {
                ForEach(Array(viewModel.rankedParticipants.enumerated()), id: \.element.id) { index, participant in
                    Button {
                        selectedParticipant = participant
                    } label: {
                        ParticipantRankRow(rank: index + 1, participant: participant)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }
}

private struct ParticipantRankRow: View {
    let rank: Int
    let participant: EventParticipant

    var body: some View {
        HStack(spacing: 14) {
            Text("\(rank)")
                .font(.system(.subheadline, design: .rounded).weight(.bold))
                .foregroundStyle(rank == 1 ? AppTheme.flame : AppTheme.textSecondary)
                .frame(width: 20)

            ZStack {
                Circle()
                    .fill(AppTheme.flame.opacity(0.14))
                    .frame(width: 44, height: 44)
                if let latest = participant.latestCheckIn, let fileName = latest.photoFileName {
                    ProofThumbnail(fileName: fileName)
                        .frame(width: 44, height: 44)
                        .clipShape(Circle())
                } else {
                    Text(participant.initials)
                        .font(.system(.caption, design: .rounded).weight(.bold))
                        .foregroundStyle(AppTheme.flame)
                }
            }

            VStack(alignment: .leading, spacing: 2) {
                Text(participant.isCurrentUser ? "You" : participant.displayName)
                    .font(.system(.subheadline, design: .rounded).weight(.semibold))
                    .foregroundStyle(AppTheme.textPrimary)
                Text(statusText)
                    .font(.system(.caption, design: .rounded))
                    .foregroundStyle(participant.isBroken ? AppTheme.dangerRed : AppTheme.textSecondary)
            }

            Spacer()

            FlameBadge(count: participant.currentStreakCount, isBroken: participant.isBroken, size: 15)
        }
        .padding(14)
        .background(participant.isCurrentUser ? AppTheme.flame.opacity(0.08) : Color.clear, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
        .glassCard(cornerRadius: 18)
    }

    private var statusText: String {
        if participant.isPending {
            return "Invited — hasn't joined yet"
        } else if participant.isCheckedInToday {
            return "Checked in today"
        } else if participant.isBroken {
            return "Streak broken"
        } else {
            return "Not checked in yet"
        }
    }
}
