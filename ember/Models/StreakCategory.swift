//
//  StreakCategory.swift
//  ember
//

import SwiftUI

enum StreakCategory: String, CaseIterable, Identifiable, Codable {
    case fitness = "Fitness"
    case mindfulness = "Mindfulness"
    case learning = "Learning"
    case health = "Health"
    case productivity = "Productivity"
    case creativity = "Creativity"
    case social = "Social"
    case finance = "Finance"

    var id: String { rawValue }

    var iconName: String {
        switch self {
        case .fitness: return "figure.run"
        case .mindfulness: return "leaf"
        case .learning: return "book"
        case .health: return "heart"
        case .productivity: return "checkmark.circle"
        case .creativity: return "paintbrush"
        case .social: return "person.2"
        case .finance: return "banknote"
        }
    }

    var tint: Color {
        switch self {
        case .fitness: return AppTheme.fitness
        case .mindfulness: return AppTheme.mindfulness
        case .learning: return AppTheme.learning
        case .health: return AppTheme.health
        case .productivity: return AppTheme.productivity
        case .creativity: return AppTheme.creativity
        case .social: return AppTheme.social
        case .finance: return AppTheme.finance
        }
    }
}
