//
//  InviteFriendsViewModel.swift
//  ember
//

import Foundation
import Observation
import MessageUI

enum InviteSourceMode: String, CaseIterable, Hashable {
    case contacts = "Contacts"
    case search = "Search"
}

struct PendingInvite: Identifiable {
    let id = UUID()
    let contactName: String
    let phoneNumber: String
    let messageBody: String
}

@Observable
@MainActor
final class InviteFriendsViewModel {
    var mode: InviteSourceMode = .contacts
    var searchQuery: String = ""

    private(set) var contacts: [PhoneContact] = []
    private(set) var searchResults: [AppUser] = []
    private(set) var contactsAccessDenied = false
    private(set) var isLoadingContacts = false
    private(set) var selectedInvitees: [EventInvitee]

    var pendingInvite: PendingInvite?

    private let contactsProvider: ContactsProviding
    private let directoryService: UserDirectoryServicing

    init(contactsProvider: ContactsProviding, directoryService: UserDirectoryServicing, initialInvitees: [EventInvitee]) {
        self.contactsProvider = contactsProvider
        self.directoryService = directoryService
        self.selectedInvitees = initialInvitees
    }

    func loadContactsIfNeeded() async {
        guard contacts.isEmpty, !contactsAccessDenied else { return }
        isLoadingContacts = true
        defer { isLoadingContacts = false }

        let granted = await contactsProvider.requestAccess()
        guard granted else {
            contactsAccessDenied = true
            return
        }
        contacts = (try? await contactsProvider.fetchContacts()) ?? []
    }

    func search() async {
        searchResults = (try? await directoryService.search(query: searchQuery)) ?? []
    }

    func matchedUser(for contact: PhoneContact) -> AppUser? {
        directoryService.matchedUser(phoneNumbers: contact.phoneNumbers, name: contact.name)
    }

    func isSelected(name: String) -> Bool {
        selectedInvitees.contains { $0.displayName == name }
    }

    func addAppUser(_ user: AppUser) {
        guard !isSelected(name: user.displayName) else { return }
        selectedInvitees.append(EventInvitee(displayName: user.displayName, phoneNumber: user.phoneNumber, isPending: false))
    }

    /// Adds a contact who already has an account, or kicks off an SMS invite for one who doesn't.
    func addContact(_ contact: PhoneContact) {
        guard !isSelected(name: contact.name) else { return }

        if let matched = matchedUser(for: contact) {
            addAppUser(matched)
            return
        }

        guard let phoneNumber = contact.phoneNumbers.first else {
            selectedInvitees.append(EventInvitee(displayName: contact.name, phoneNumber: nil, isPending: true))
            return
        }

        let messageBody = "Join my streak challenge on Ember! Download the app to jump in: \(AppLinks.inviteURL)"

        if MFMessageComposeViewController.canSendText() {
            pendingInvite = PendingInvite(contactName: contact.name, phoneNumber: phoneNumber, messageBody: messageBody)
        } else {
            // No Messages capability here (e.g. Simulator) — still record the invite so the flow is testable end-to-end.
            selectedInvitees.append(EventInvitee(displayName: contact.name, phoneNumber: phoneNumber, isPending: true))
        }
    }

    func confirmPendingInvite() {
        guard let pendingInvite else { return }
        selectedInvitees.append(EventInvitee(displayName: pendingInvite.contactName, phoneNumber: pendingInvite.phoneNumber, isPending: true))
        self.pendingInvite = nil
    }

    func cancelPendingInvite() {
        pendingInvite = nil
    }

    func remove(_ invitee: EventInvitee) {
        selectedInvitees.removeAll { $0.id == invitee.id }
    }
}
