//
//  EventCheckInSheet.swift
//  ember
//

import SwiftUI
import PhotosUI
import UIKit

struct EventCheckInSheet: View {
    @Environment(\.dismiss) private var dismiss
    var onSubmit: (Data?) -> Void

    @State private var selectedPhotoItem: PhotosPickerItem?
    @State private var selectedImageData: Data?
    @State private var showingCamera = false

    private var cameraAvailable: Bool {
        UIImagePickerController.isSourceTypeAvailable(.camera)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                preview
                    .padding(.horizontal, 20)

                HStack(spacing: 12) {
                    if cameraAvailable {
                        Button {
                            showingCamera = true
                        } label: {
                            Label("Camera", systemImage: "camera.fill")
                                .font(.system(.subheadline, design: .rounded).weight(.semibold))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 12)
                                .background(Color.gray.opacity(0.08), in: Capsule())
                                .foregroundStyle(AppTheme.textPrimary)
                        }
                        .buttonStyle(.plain)
                    }

                    PhotosPicker(selection: $selectedPhotoItem, matching: .images) {
                        Label("Library", systemImage: "photo.on.rectangle")
                            .font(.system(.subheadline, design: .rounded).weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 12)
                            .background(Color.gray.opacity(0.08), in: Capsule())
                            .foregroundStyle(AppTheme.textPrimary)
                    }
                }
                .padding(.horizontal, 20)

                Spacer()

                Button {
                    onSubmit(selectedImageData)
                    dismiss()
                } label: {
                    Text(selectedImageData == nil ? "Check In Without Photo" : "Submit Check-In")
                        .font(.system(.headline, design: .rounded))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(AppTheme.flameGradient, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
                        .foregroundStyle(.white)
                }
                .buttonStyle(.plain)
                .padding(.horizontal, 20)
                .padding(.bottom, 12)
            }
            .padding(.top, 12)
            .background(AmbientBackground())
            .navigationTitle("Check In")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
            .onChange(of: selectedPhotoItem) { _, newItem in
                Task {
                    if let data = try? await newItem?.loadTransferable(type: Data.self),
                       let uiImage = UIImage(data: data) {
                        selectedImageData = uiImage.jpegData(compressionQuality: 0.8)
                    }
                }
            }
            .fullScreenCover(isPresented: $showingCamera) {
                CameraCaptureView(
                    onCapture: { data in
                        selectedImageData = data
                        showingCamera = false
                    },
                    onCancel: {
                        showingCamera = false
                    }
                )
                .ignoresSafeArea()
            }
        }
    }

    @ViewBuilder
    private var preview: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .fill(Color.gray.opacity(0.08))
                .frame(height: 320)

            if let selectedImageData, let uiImage = UIImage(data: selectedImageData) {
                Image(uiImage: uiImage)
                    .resizable()
                    .scaledToFill()
                    .frame(height: 320)
                    .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            } else {
                VStack(spacing: 10) {
                    Image(systemName: "camera.fill")
                        .font(.system(size: 36))
                        .foregroundStyle(AppTheme.textSecondary)
                    Text("Add a photo as proof")
                        .font(.system(.subheadline, design: .rounded))
                        .foregroundStyle(AppTheme.textSecondary)
                }
            }
        }
    }
}
