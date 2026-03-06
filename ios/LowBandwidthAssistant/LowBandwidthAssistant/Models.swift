import Foundation

struct FeedResponse: Codable {
    let items: [FeedItem]
}

struct FeedItem: Codable, Identifiable {
    let id: String
    let source: String
    let account: String
    let kind: String
    let title: String
    let body: String
    let summary: String
    let previewURL: String?
    let receivedAt: Date

    enum CodingKeys: String, CodingKey {
        case id, source, account, kind, title, body, summary
        case previewURL = "preview_url"
        case receivedAt = "received_at"
    }
}

struct ActionRequest: Codable {
    let action: String
    let target: String?
    let body: String?
}

struct VoiceCommandRequest: Codable {
    let transcript: String
}

struct VoiceCommandResponse: Codable {
    let command: String
    let itemID: String?
    let target: String?
    let body: String?
    let confidence: Double

    enum CodingKeys: String, CodingKey {
        case command, target, body, confidence
        case itemID = "item_id"
    }
}
