//
//  PhoneContact.swift
//  ember
//

import Foundation

struct PhoneContact: Identifiable, Hashable {
    let id: String
    let name: String
    let phoneNumbers: [String]
}
