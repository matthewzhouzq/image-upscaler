//
//  EventInvitee.swift
//  ember
//
//  A person selected to join an event before it's created: either a real
//  AppUser (matched from contacts or search) or a contact who isn't on the
//  app yet and has been sent an SMS invite (isPending).
//

import Foundation

struct EventInvitee: Identifiable, Hashable {
    var id: String { displayName }
    let displayName: String
    let phoneNumber: String?
    let isPending: Bool
}
