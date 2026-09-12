//
//  InviteFriendsView.swift
//  ember
//

import SwiftUI
import MessageUI

struct InviteFriendsView: View {
    @State private var viewModel: InviteFriendsViewModel
    @Environment(\.dismiss) private var dismiss
    var onDone: ([EventInvitee]) -> Void

    init(initialInvitees: [EventInvitee], onDone: @escaping ([EventInvitee]) -> Void) {
        _viewModel = State(initialValue: InviteFriendsViewModel(
            contactsProvider: SystemContactsProvider(),
            directoryService: MockUserDirectoryService(),
            initialInvitees: initialInvitees
        ))
        self.onDone = onDone
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                Picker("Source", selection: $viewModel.mode) {
                    ForEach(InviteSourceMode.allCases, id: \.self) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .padding()

                switch viewModel.mode {
                case .contacts: contactsSection
                case .search: searchSection
                }
            }
            .background(AmbientBackground())
            .navigationTitle("Add Friends")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        onDone(viewModel.selectedInvitees)
                        dismiss()
                    }
                    .fontWeight(.semibold)
                }
            }
            .sheet(item: $viewModel.pendingInvite) { invite in
                MessageComposeView(recipients: [invite.phoneNumber], body: invite.messageBody) { result in
                    if result == .sent {
                        viewModel.confirmPendingInvite()
                    } else {
                        viewModel.cancelPendingInvite()
                    }
                }
                .ignoresSafeArea()
            }
        }
    }

    private var contactsSection: some View {
        Group {
            if viewModel.contactsAccessDenied {
                statusMessage("Contacts access is off. Enable it in Settings > Privacy > Contacts to invite friends from your address book.")
            } else if viewModel.isLoadingContacts {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if viewModel.contacts.isEmpty {
                statusMessage("No contacts found.")
            } else {
                List(viewModel.contacts) { contact in
                    ContactRow(
                        contact: contact,
                        matchedUser: viewModel.matchedUser(for: contact),
                        isSelected: viewModel.isSelected(name: contact.name),
                        onAdd: { viewModel.addContact(contact) }
                    )
                }
                .listStyle(.plain)
                .scrollContentBackground(.hidden)
            }
        }
        .task { await viewModel.loadContactsIfNeeded() }
    }

    private var searchSection: some View {
        VStack(spacing: 0) {
            TextField("Search by name", text: $viewModel.searchQuery)
                .textFieldStyle(.roundedBorder)
                .padding(.horizontal)
                .padding(.bottom, 8)
                .onChange(of: viewModel.searchQuery) { _, _ in
                    Task { await viewModel.search() }
                }

            if viewModel.searchQuery.isEmpty {
                statusMessage("Search for a friend already on Ember.")
            } else if viewModel.searchResults.isEmpty {
                statusMessage("No one found. Try Contacts to invite them instead.")
            } else {
                List(viewModel.searchResults) { user in
                    HStack {
                        Text(user.displayName)
                            .foregroundStyle(AppTheme.textPrimary)
                        Spacer()
                        if viewModel.isSelected(name: user.displayName) {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(AppTheme.flame)
                        } else {
                            Button("Add") { viewModel.addAppUser(user) }
                                .buttonStyle(.borderless)
                                .font(.system(.subheadline, design: .rounded).weight(.semibold))
                        }
                    }
                }
                .listStyle(.plain)
                .scrollContentBackground(.hidden)
            }
        }
    }

    private func statusMessage(_ text: String) -> some View {
        Text(text)
            .font(.system(.subheadline, design: .rounded))
            .foregroundStyle(AppTheme.textSecondary)
            .multilineTextAlignment(.center)
            .padding(.horizontal, 32)
            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
            .padding(.top, 40)
    }
}

private struct ContactRow: View {
    let contact: PhoneContact
    let matchedUser: AppUser?
    let isSelected: Bool
    let onAdd: () -> Void

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(contact.name)
                    .foregroundStyle(AppTheme.textPrimary)
                Text(matchedUser != nil ? "On Ember" : "Not on Ember yet")
                    .font(.system(.caption, design: .rounded))
                    .foregroundStyle(matchedUser != nil ? AppTheme.successGreen : AppTheme.textSecondary)
            }

            Spacer()

            if isSelected {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(AppTheme.flame)
            } else {
                Button(matchedUser != nil ? "Add" : "Invite") {
                    onAdd()
                }
                .buttonStyle(.borderless)
                .font(.system(.subheadline, design: .rounded).weight(.semibold))
            }
        }
        .padding(.vertical, 4)
    }
}
