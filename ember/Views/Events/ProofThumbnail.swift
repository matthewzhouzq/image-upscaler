//
//  ProofThumbnail.swift
//  ember
//

import SwiftUI

struct ProofThumbnail: View {
    let fileName: String
    private let photoStore: PhotoStoring = FileSystemPhotoStore()

    var body: some View {
        if let uiImage = UIImage(contentsOfFile: photoStore.url(for: fileName).path) {
            Image(uiImage: uiImage)
                .resizable()
                .scaledToFill()
        } else {
            Image(systemName: "photo")
                .foregroundStyle(AppTheme.textSecondary)
        }
    }
}
