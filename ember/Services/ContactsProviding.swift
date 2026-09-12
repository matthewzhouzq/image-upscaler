//
//  ContactsProviding.swift
//  ember
//

import Foundation
import Contacts

protocol ContactsProviding {
    nonisolated func requestAccess() async -> Bool
    nonisolated func fetchContacts() async throws -> [PhoneContact]
}

final class SystemContactsProvider: ContactsProviding {
    nonisolated func requestAccess() async -> Bool {
        await withCheckedContinuation { continuation in
            CNContactStore().requestAccess(for: .contacts) { granted, _ in
                continuation.resume(returning: granted)
            }
        }
    }

    nonisolated func fetchContacts() async throws -> [PhoneContact] {
        let store = CNContactStore()
        // CNContactFormatter reads more than givenName/familyName internally (nickname, name
        // prefix/suffix, etc.) — fetching only those two crashes with CNPropertyNotFetchedException
        // the moment the formatter touches a key we didn't request. Its own descriptor covers
        // everything it needs.
        let keys: [CNKeyDescriptor] = [
            CNContactFormatter.descriptorForRequiredKeys(for: .fullName),
            CNContactPhoneNumbersKey as CNKeyDescriptor
        ]
        let request = CNContactFetchRequest(keysToFetch: keys)

        var results: [PhoneContact] = []
        try store.enumerateContacts(with: request) { contact, _ in
            let name = CNContactFormatter.string(from: contact, style: .fullName)
                ?? "\(contact.givenName) \(contact.familyName)".trimmingCharacters(in: .whitespaces)
            guard !name.isEmpty else { return }
            let phones = contact.phoneNumbers.map { $0.value.stringValue }
            results.append(PhoneContact(id: contact.identifier, name: name, phoneNumbers: phones))
        }
        return results.sorted { $0.name < $1.name }
    }
}
