import SwiftUI

struct ContentView: View {
    @StateObject var viewModel: FeedViewModel
    @StateObject private var recognizer = VoiceRecognizer()

    @State private var replyText = ""
    @State private var forwardTarget = ""
    @State private var moveTarget = ""

    var body: some View {
        NavigationStack {
            List(viewModel.items) { item in
                VStack(alignment: .leading, spacing: 8) {
                    Text(item.title).font(.headline)
                    Text("\(item.source.uppercased()) • \(item.account)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(item.summary)
                        .font(.body)

                    if item.kind == "message" {
                        HStack {
                            Button("Reply") {
                                Task { await viewModel.applyAction(item: item, action: "reply", body: replyText) }
                            }
                            Button("Forward") {
                                Task { await viewModel.applyAction(item: item, action: "forward", target: forwardTarget) }
                            }
                            Button("Spam") {
                                Task { await viewModel.applyAction(item: item, action: "mark_spam") }
                            }
                        }
                        TextField("Reply text", text: $replyText)
                            .textFieldStyle(.roundedBorder)
                        TextField("Forward to email", text: $forwardTarget)
                            .textFieldStyle(.roundedBorder)
                    } else {
                        HStack {
                            Button("Send to Ramp") {
                                Task {
                                    await viewModel.applyAction(item: item, action: "forward_to_ramp", target: "receipts@ramp.com")
                                }
                            }
                            Button("Move") {
                                Task { await viewModel.applyAction(item: item, action: "move_account", target: moveTarget) }
                            }
                        }
                        TextField("Move to account email", text: $moveTarget)
                            .textFieldStyle(.roundedBorder)
                    }
                }
                .padding(.vertical, 4)
            }
            .navigationTitle("Low Bandwidth Inbox")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Refresh") { Task { await viewModel.refresh() } }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button(recognizer.isRecording ? "Stop Voice" : "Voice") {
                        recognizer.toggleRecording()
                    }
                }
            }
            .safeAreaInset(edge: .bottom) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Voice: \(recognizer.transcript)")
                        .font(.caption)
                        .lineLimit(2)
                    Button("Run Voice Command") {
                        Task { await viewModel.handleVoice(transcript: recognizer.transcript) }
                    }
                    .buttonStyle(.borderedProminent)
                    if let status = viewModel.statusText {
                        Text(status).font(.caption).foregroundStyle(.green)
                    }
                    if let err = viewModel.errorText {
                        Text(err).font(.caption).foregroundStyle(.red)
                    }
                }
                .padding(10)
                .background(.ultraThinMaterial)
            }
            .task {
                _ = await recognizer.requestPermission()
                await viewModel.refresh()
            }
        }
    }
}

#Preview {
    ContentView(viewModel: FeedViewModel())
}
