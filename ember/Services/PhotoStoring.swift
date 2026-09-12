//
//  PhotoStoring.swift
//  ember
//
//  Seam for proof-photo storage. FileSystemPhotoStore keeps files on-disk for
//  the prototype; a cloud-backed implementation (Firebase Storage, S3, etc.)
//  can conform later so event check-in photos sync across devices.
//

import Foundation

protocol PhotoStoring {
    func save(_ data: Data) throws -> String
    func url(for fileName: String) -> URL
    func delete(fileName: String) throws
}

final class FileSystemPhotoStore: PhotoStoring {
    private let directory: URL

    init() {
        let appSupport = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        directory = appSupport.appendingPathComponent("EventProofPhotos", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    func save(_ data: Data) throws -> String {
        let fileName = "\(UUID().uuidString).jpg"
        try data.write(to: url(for: fileName), options: .atomic)
        return fileName
    }

    func url(for fileName: String) -> URL {
        directory.appendingPathComponent(fileName)
    }

    func delete(fileName: String) throws {
        try FileManager.default.removeItem(at: url(for: fileName))
    }
}
