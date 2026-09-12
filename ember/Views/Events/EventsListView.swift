//
//  EventsListView.swift
//  ember
//

import SwiftUI

struct EventsListView: View {
    @Environment(\.eventRepository) private var repository
    @State private var viewModel: EventsListViewModel?
    @State private var showingCreateEvent = false

    var body: some View {
        NavigationStack {
            ZStack {
                AmbientBackground()

                ScrollView {
                    if let viewModel, viewModel.events.isEmpty {
                        EmptyEventsView { showingCreateEvent = true }
                            .padding(.top, 80)
                    } else if let viewModel {
                        LazyVStack(spacing: 14) {
                            ForEach(viewModel.events) { event in
                                NavigationLink(value: event) {
                                    EventCardView(event: event)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.top, 12)
                        .padding(.bottom, 32)
                    }
                }
            }
            .navigationTitle("Events")
            .navigationDestination(for: StreakEvent.self) { event in
                if let repository {
                    EventDetailView(event: event, repository: repository)
                }
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showingCreateEvent = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.system(size: 22))
                    }
                }
            }
            .sheet(isPresented: $showingCreateEvent) {
                if let repository {
                    CreateEventView(repository: repository) {
                        viewModel?.load()
                    }
                }
            }
            .task {
                if viewModel == nil, let repository {
                    viewModel = EventsListViewModel(repository: repository)
                }
                viewModel?.load()
            }
        }
    }
}
