//
//  AppTheme.swift
//  ember
//

import SwiftUI

enum AppTheme {
    static let background = Color(red: 0.97, green: 0.97, blue: 0.98)
    static let surface = Color.white
    static let textPrimary = Color(red: 0.11, green: 0.11, blue: 0.13)
    static let textSecondary = Color(red: 0.45, green: 0.45, blue: 0.48)

    static let flame = Color(red: 1.0, green: 0.38, blue: 0.13)
    static let flameSecondary = Color(red: 1.0, green: 0.62, blue: 0.13)
    static var flameGradient: LinearGradient {
        LinearGradient(colors: [flame, flameSecondary], startPoint: .topLeading, endPoint: .bottomTrailing)
    }

    static let fitness = Color(red: 0.98, green: 0.31, blue: 0.32)
    static let mindfulness = Color(red: 0.42, green: 0.63, blue: 0.98)
    static let learning = Color(red: 0.58, green: 0.42, blue: 0.93)
    static let health = Color(red: 0.98, green: 0.42, blue: 0.62)
    static let productivity = Color(red: 0.24, green: 0.72, blue: 0.58)
    static let creativity = Color(red: 0.96, green: 0.66, blue: 0.24)
    static let social = Color(red: 0.32, green: 0.75, blue: 0.86)
    static let finance = Color(red: 0.36, green: 0.64, blue: 0.42)

    static let successGreen = Color(red: 0.20, green: 0.70, blue: 0.45)
    static let dangerRed = Color(red: 0.90, green: 0.28, blue: 0.28)
}
