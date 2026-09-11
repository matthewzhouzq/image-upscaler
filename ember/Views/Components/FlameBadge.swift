//
//  FlameBadge.swift
//  ember
//

import SwiftUI

struct FlameBadge: View {
    let count: Int
    var isBroken: Bool = false
    var size: CGFloat = 18

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: isBroken ? "flame" : "flame.fill")
                .font(.system(size: size, weight: .semibold))
                .foregroundStyle(isBroken ? AnyShapeStyle(AppTheme.textSecondary) : AnyShapeStyle(AppTheme.flameGradient))
            Text("\(count)")
                .font(.system(size: size, weight: .bold, design: .rounded))
                .foregroundStyle(isBroken ? AppTheme.textSecondary : AppTheme.textPrimary)
        }
    }
}
