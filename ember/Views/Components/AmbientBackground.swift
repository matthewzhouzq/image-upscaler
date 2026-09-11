//
//  AmbientBackground.swift
//  ember
//

import SwiftUI

struct AmbientBackground: View {
    var body: some View {
        ZStack {
            AppTheme.background.ignoresSafeArea()
            Circle()
                .fill(AppTheme.flameGradient)
                .frame(width: 320, height: 320)
                .blur(radius: 90)
                .opacity(0.18)
                .offset(x: -140, y: -260)
                .ignoresSafeArea()
            Circle()
                .fill(AppTheme.learning)
                .frame(width: 280, height: 280)
                .blur(radius: 100)
                .opacity(0.12)
                .offset(x: 160, y: 300)
                .ignoresSafeArea()
        }
    }
}
