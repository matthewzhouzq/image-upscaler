//
//  UserDirectoryServicing.swift
//  ember
//
//  Seam for the real-user search/lookup a backend would provide: searching
//  by name, and matching a phone-book contact against an existing account.
//  MockUserDirectoryService fakes both against a fixed roster for now.
//

import Foundation

protocol UserDirectoryServicing {
    func search(query: String) async throws -> [AppUser]
    func matchedUser(phoneNumbers: [String], name: String) -> AppUser?
}

final class MockUserDirectoryService: UserDirectoryServicing {
    private let users = MockUserDirectory.users

    func search(query: String) async throws -> [AppUser] {
        try? await Task.sleep(nanoseconds: 200_000_000)
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return [] }
        return users.filter { $0.displayName.localizedCaseInsensitiveContains(trimmed) }
    }

    func matchedUser(phoneNumbers: [String], name: String) -> AppUser? {
        let normalizedPhones = Set(phoneNumbers.map(Self.normalize))
        if let phoneMatch = users.first(where: { user in
            guard let phone = user.phoneNumber else { return false }
            return normalizedPhones.contains(Self.normalize(phone))
        }) {
            return phoneMatch
        }
        return users.first { $0.displayName.caseInsensitiveCompare(name) == .orderedSame }
    }

    private static func normalize(_ phone: String) -> String {
        phone.filter(\.isNumber)
    }
}
