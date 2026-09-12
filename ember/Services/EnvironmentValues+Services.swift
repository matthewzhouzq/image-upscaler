//
//  EnvironmentValues+Services.swift
//  ember
//

import SwiftUI

private struct StreakRepositoryKey: EnvironmentKey {
    static let defaultValue: StreakRepository? = nil
}

private struct GameCenterManagerKey: EnvironmentKey {
    static let defaultValue = GameCenterManager()
}

private struct StreakRestoreServiceKey: EnvironmentKey {
    static let defaultValue: StreakRestoreServicing = MockStreakRestoreService()
}

private struct EventRepositoryKey: EnvironmentKey {
    static let defaultValue: EventRepository? = nil
}

private struct PhotoStoreKey: EnvironmentKey {
    static let defaultValue: PhotoStoring = FileSystemPhotoStore()
}

extension EnvironmentValues {
    var streakRepository: StreakRepository? {
        get { self[StreakRepositoryKey.self] }
        set { self[StreakRepositoryKey.self] = newValue }
    }

    var gameCenterManager: GameCenterManager {
        get { self[GameCenterManagerKey.self] }
        set { self[GameCenterManagerKey.self] = newValue }
    }

    var streakRestoreService: StreakRestoreServicing {
        get { self[StreakRestoreServiceKey.self] }
        set { self[StreakRestoreServiceKey.self] = newValue }
    }

    var eventRepository: EventRepository? {
        get { self[EventRepositoryKey.self] }
        set { self[EventRepositoryKey.self] = newValue }
    }

    var photoStore: PhotoStoring {
        get { self[PhotoStoreKey.self] }
        set { self[PhotoStoreKey.self] = newValue }
    }
}
