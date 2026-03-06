import SwiftUI

@main
struct LowBandwidthAssistantApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView(viewModel: FeedViewModel())
        }
    }
}
