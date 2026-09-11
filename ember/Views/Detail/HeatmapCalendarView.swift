//
//  HeatmapCalendarView.swift
//  ember
//

import SwiftUI

struct HeatmapCalendarView: View {
    let completedDates: [Date]
    private let weeksToShow = 12
    private let columns = Array(repeating: GridItem(.flexible(), spacing: 4), count: 7)

    private var completedDaySet: Set<DateComponents> {
        Set(completedDates.map { Calendar.current.dateComponents([.year, .month, .day], from: $0) })
    }

    private var days: [Date] {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: .now)
        let totalDays = weeksToShow * 7
        return (0..<totalDays).reversed().compactMap {
            calendar.date(byAdding: .day, value: -$0, to: today)
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("History")
                .font(.system(.headline, design: .rounded))
                .foregroundStyle(AppTheme.textPrimary)

            LazyVGrid(columns: columns, spacing: 4) {
                ForEach(days, id: \.self) { day in
                    RoundedRectangle(cornerRadius: 4, style: .continuous)
                        .fill(isCompleted(day) ? AnyShapeStyle(AppTheme.flameGradient) : AnyShapeStyle(AppTheme.textSecondary.opacity(0.08)))
                        .aspectRatio(1, contentMode: .fit)
                }
            }
        }
        .padding(16)
    }

    private func isCompleted(_ day: Date) -> Bool {
        completedDaySet.contains(Calendar.current.dateComponents([.year, .month, .day], from: day))
    }
}
