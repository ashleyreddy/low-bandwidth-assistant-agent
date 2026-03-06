import Foundation

@MainActor
final class FeedViewModel: ObservableObject {
    @Published var items: [FeedItem] = []
    @Published var errorText: String?
    @Published var statusText: String?

    func refresh() async {
        do {
            items = try await APIClient.shared.fetchFeed()
        } catch {
            errorText = "Failed to load feed: \(error.localizedDescription)"
        }
    }

    func applyAction(item: FeedItem, action: String, target: String? = nil, body: String? = nil) async {
        do {
            try await APIClient.shared.sendAction(itemID: item.id, action: action, target: target, body: body)
            statusText = "Action '\(action)' sent for \(item.id)"
        } catch {
            errorText = "Action failed: \(error.localizedDescription)"
        }
    }

    func handleVoice(transcript: String) async {
        do {
            let cmd = try await APIClient.shared.parseVoiceCommand(transcript: transcript)
            guard let itemID = cmd.itemID, let item = items.first(where: { $0.id == itemID }) else {
                statusText = "Parsed command: \(cmd.command). No matching item id."
                return
            }
            await applyAction(item: item, action: cmd.command, target: cmd.target, body: cmd.body)
        } catch {
            errorText = "Voice parse failed: \(error.localizedDescription)"
        }
    }
}
