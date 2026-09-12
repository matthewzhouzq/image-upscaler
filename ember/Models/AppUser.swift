//
//  AppUser.swift
//  ember
//
//  Stand-in for a real backend's user directory. Once accounts exist for
//  real, MockUserDirectoryService's search/match logic is replaced by an
//  actual server lookup — nothing above the service layer needs to change.
//

import Foundation

struct AppUser: Identifiable, Hashable {
    let id: UUID
    let displayName: String
    let phoneNumber: String?

    init(displayName: String, phoneNumber: String?) {
        self.id = UUID()
        self.displayName = displayName
        self.phoneNumber = phoneNumber
    }
}

enum MockUserDirectory {
    static let users: [AppUser] = [
        AppUser(displayName: "Jordan Blake", phoneNumber: "+15550101"),
        AppUser(displayName: "Riya Kapoor", phoneNumber: "+15550102"),
        AppUser(displayName: "Sam Whitfield", phoneNumber: "+15550103"),
        AppUser(displayName: "Talia Osei", phoneNumber: "+15550104"),
        AppUser(displayName: "Mateo Navarro", phoneNumber: "+15550105"),
        AppUser(displayName: "Devon Park", phoneNumber: "+15550106"),
        AppUser(displayName: "Ines Farah", phoneNumber: "+15550107"),
        AppUser(displayName: "Casey Lindgren", phoneNumber: "+15550108")
    ]
}
