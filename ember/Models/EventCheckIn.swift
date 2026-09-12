//
//  EventCheckIn.swift
//  ember
//

import Foundation
import SwiftData

@Model
final class EventCheckIn {
    var id: UUID
    var date: Date
    var photoFileName: String?

    var participant: EventParticipant?

    init(date: Date, photoFileName: String? = nil) {
        self.id = UUID()
        self.date = date
        self.photoFileName = photoFileName
    }
}
