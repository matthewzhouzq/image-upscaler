//
//  CreateEventView.swift
//  ember
//

import SwiftUI

struct CreateEventView: View {
    @State private var viewModel: CreateEventViewModel
    @Environment(\.dismiss) private var dismiss
    @State private var showingInviteFriends = false
    var onSave: () -> Void

    init(repository: EventRepository, onSave: @escaping () -> Void) {
        _viewModel = State(initialValue: CreateEventViewModel(repository: repository))
        self.onSave = onSave
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Name") {
                    TextField("e.g. 30-Day Fitness Challenge", text: $viewModel.name)
                }

                Section("Icon") {
                    IconPickerGrid(selectedIcon: $viewModel.iconName)
                }

                Section("Category") {
                    CategoryPickerGrid(selectedCategory: $viewModel.category)
                }

                Section("Start Date") {
                    DatePicker(
                        "Starts",
                        selection: $viewModel.startDate,
                        in: Calendar.current.startOfDay(for: .now)...,
                        displayedComponents: .date
                    )
                }

                Section {
                    if viewModel.selectedInvitees.isEmpty {
                        Text("No friends added yet")
                            .foregroundStyle(AppTheme.textSecondary)
                    } else {
                        ForEach(viewModel.selectedInvitees) { invitee in
                            HStack {
                                Text(invitee.displayName)
                                    .foregroundStyle(AppTheme.textPrimary)
                                if invitee.isPending {
                                    Text("Invited")
                                        .font(.system(.caption2, design: .rounded).weight(.semibold))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 3)
                                        .background(Color.gray.opacity(0.15), in: Capsule())
                                        .foregroundStyle(AppTheme.textSecondary)
                                }
                                Spacer()
                                Button {
                                    viewModel.removeInvitee(invitee)
                                } label: {
                                    Image(systemName: "minus.circle.fill")
                                        .foregroundStyle(AppTheme.dangerRed)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    Button {
                        showingInviteFriends = true
                    } label: {
                        Label("Add Friends", systemImage: "person.badge.plus")
                    }
                } header: {
                    Text("Invite Friends")
                } footer: {
                    Text("Everyone you invite starts at day one, same as you. Friends not on Ember yet get invited by text.")
                }
            }
            .scrollContentBackground(.hidden)
            .background(AmbientBackground())
            .navigationTitle("New Event")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        viewModel.save()
                        onSave()
                        dismiss()
                    }
                    .disabled(!viewModel.canSave)
                    .fontWeight(.semibold)
                }
            }
            .sheet(isPresented: $showingInviteFriends) {
                InviteFriendsView(initialInvitees: viewModel.selectedInvitees) { invitees in
                    viewModel.selectedInvitees = invitees
                }
            }
        }
    }
}
