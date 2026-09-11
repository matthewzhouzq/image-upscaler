//
//  CategoryPickerGrid.swift
//  ember
//

import SwiftUI

struct CategoryPickerGrid: View {
    @Binding var selectedCategory: StreakCategory
    private let columns = [GridItem(.adaptive(minimum: 100), spacing: 10)]

    var body: some View {
        LazyVGrid(columns: columns, spacing: 10) {
            ForEach(StreakCategory.allCases) { category in
                Button {
                    selectedCategory = category
                } label: {
                    Label(category.rawValue, systemImage: category.iconName)
                        .font(.system(.subheadline, design: .rounded).weight(.medium))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            Capsule().fill(selectedCategory == category ? category.tint.opacity(0.18) : Color.gray.opacity(0.08))
                        )
                        .foregroundStyle(selectedCategory == category ? category.tint : AppTheme.textSecondary)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(.vertical, 6)
    }
}
