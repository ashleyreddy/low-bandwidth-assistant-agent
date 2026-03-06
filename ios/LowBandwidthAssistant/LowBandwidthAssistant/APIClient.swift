import Foundation

final class APIClient {
    static let shared = APIClient()

    // Replace with your deployed backend URL.
    private let baseURL = URL(string: "http://127.0.0.1:8000/v1")!
    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .iso8601
        return d
    }()

    func fetchFeed() async throws -> [FeedItem] {
        let (data, _) = try await URLSession.shared.data(from: baseURL.appending(path: "feed"))
        return try decoder.decode(FeedResponse.self, from: data).items
    }

    func sendAction(itemID: String, action: String, target: String? = nil, body: String? = nil) async throws {
        var request = URLRequest(url: baseURL.appending(path: "items/\(itemID)/action"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(ActionRequest(action: action, target: target, body: body))

        _ = try await URLSession.shared.data(for: request)
    }

    func parseVoiceCommand(transcript: String) async throws -> VoiceCommandResponse {
        var request = URLRequest(url: baseURL.appending(path: "voice/command"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(VoiceCommandRequest(transcript: transcript))

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(VoiceCommandResponse.self, from: data)
    }
}
