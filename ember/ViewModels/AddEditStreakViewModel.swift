//
//  AddEditStreakViewModel.swift
//  ember
//

import Foundation
import Observation

@Observable
@MainActor
final class AddEditStreakViewModel {
    var name: String
    var iconName: String
    var category: StreakCategory

    private let repository: StreakRepository
    private let editingStreak: Streak?

    var isEditing: Bool { editingStreak != nil }
    var canSave: Bool { !name.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

    init(repository: StreakRepository, editing streak: Streak? = nil) {
        self.repository = repository
        self.editingStreak = streak
        self.name = streak?.name ?? ""
        self.iconName = streak?.iconName ?? StreakIconLibrary.defaultIcon
        self.category = streak?.category ?? .productivity
    }

    func save() {
        let trimmedName = name.trimmingCharacters(in: .whitespacesAndNewlines)
        if let editingStreak {
            editingStreak.name = trimmedName
            editingStreak.iconName = iconName
            editingStreak.category = category
            try? repository.save()
        } else {
            let streak = Streak(name: trimmedName, iconName: iconName, category: category)
            try? repository.add(streak)
        }
    }
}
