//
//  IconPickerGrid.swift
//  ember
//

import SwiftUI

struct IconPickerGrid: View {
    @Binding var selectedIcon: String
    private let columns = Array(repeating: GridItem(.flexible(), spacing: 10), count: 6)

    var body: some View {
        LazyVGrid(columns: columns, spacing: 10) {
            ForEach(StreakIconLibrary.icons, id: \.self) { icon in
                Button {
                    selectedIcon = icon
                } label: {
                    Image(systemName: icon)
                        .font(.system(size: 18, weight: .medium))
                        .frame(width: 40, height: 40)
                        .background(
                            Circle().fill(selectedIcon == icon ? AppTheme.flame.opacity(0.18) : Color.clear)
                        )
                        .foregroundStyle(selectedIcon == icon ? AppTheme.flame : AppTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.vertical, 6)
    }
}
