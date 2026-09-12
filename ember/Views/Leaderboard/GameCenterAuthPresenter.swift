//
//  GameCenterAuthPresenter.swift
//  ember
//
//  Presents the view controller GameKit hands back when it needs the user
//  to sign in interactively — GameKit's auth UI is UIKit-only, so this is
//  the standard bridge for surfacing it from SwiftUI.
//

import SwiftUI
import UIKit

struct GameCenterAuthPresenter: UIViewControllerRepresentable {
    let viewControllerToPresent: UIViewController?

    func makeUIViewController(context: Context) -> UIViewController {
        UIViewController()
    }

    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {
        guard let viewControllerToPresent, uiViewController.presentedViewController == nil else { return }
        uiViewController.present(viewControllerToPresent, animated: true)
    }
}
