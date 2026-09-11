//
//  AddEditStreakView.swift
//  ember
//

import SwiftUI

struct AddEditStreakView: View {
    @State private var viewModel: AddEditStreakViewModel
    @Environment(\.dismiss) private var dismiss
    var onSave: () -> Void

    init(repository: StreakRepository, editing streak: Streak? = nil, onSave: @escaping () -> Void) {
        _viewModel = State(initialValue: AddEditStreakViewModel(repository: repository, editing: streak))
        self.onSave = onSave
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Name") {
                    TextField("e.g. Run 5km", text: $viewModel.name)
                }

                Section("Icon") {
                    IconPickerGrid(selectedIcon: $viewModel.iconName)
                }

                Section("Category") {
                    CategoryPickerGrid(selectedCategory: $viewModel.category)
                }
            }
            .scrollContentBackground(.hidden)
            .background(AmbientBackground())
            .navigationTitle(viewModel.isEditing ? "Edit Streak" : "New Streak")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        viewModel.save()
                        onSave()
                        dismiss()
                    }
                    .disabled(!viewModel.canSave)
                    .fontWeight(.semibold)
                }
            }
        }
    }
}
