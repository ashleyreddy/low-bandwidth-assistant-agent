#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox, ttk
from urllib import error, request


@dataclass
class FeedItem:
    id: str
    source: str
    account: str
    kind: str
    title: str
    body: str
    summary: str
    received_at: str


class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _do_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        data = None
        headers = {"Accept": "application/json"}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url=url, method=method, data=data, headers=headers)
        try:
            with request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8")
                if not body:
                    return {}
                return json.loads(body)
        except error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {text}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Connection error: {exc.reason}") from exc

    def feed(self) -> list[FeedItem]:
        payload = self._do_json("GET", "/v1/feed")
        items = []
        for raw in payload.get("items", []):
            items.append(
                FeedItem(
                    id=raw.get("id", ""),
                    source=raw.get("source", ""),
                    account=raw.get("account", ""),
                    kind=raw.get("kind", ""),
                    title=raw.get("title", ""),
                    body=raw.get("body", ""),
                    summary=raw.get("summary", ""),
                    received_at=raw.get("received_at", ""),
                )
            )
        return items

    def action(self, item_id: str, action: str, target: str = "", body: str = "") -> dict:
        payload = {"action": action, "target": target or None, "body": body or None}
        return self._do_json("POST", f"/v1/items/{item_id}/action", payload)

    def parse_voice(self, transcript: str) -> dict:
        return self._do_json("POST", "/v1/voice/command", {"transcript": transcript})


class DesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Low Bandwidth Assistant Desktop")
        self.root.geometry("980x680")

        self.client = APIClient("http://127.0.0.1:8000")
        self.items: list[FeedItem] = []
        self.index_by_id: dict[str, int] = {}

        self.server_url = tk.StringVar(value="http://127.0.0.1:8000")
        self.reply_text = tk.StringVar()
        self.forward_target = tk.StringVar()
        self.move_target = tk.StringVar()
        self.voice_text = tk.StringVar()
        self.status_text = tk.StringVar(value="Ready")

        self._build_ui()
        self._refresh_async()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Server URL").pack(side=tk.LEFT)
        ttk.Entry(top, textvariable=self.server_url, width=42).pack(side=tk.LEFT, padx=8)
        ttk.Button(top, text="Connect", command=self._connect).pack(side=tk.LEFT)
        ttk.Button(top, text="Refresh", command=self._refresh_async).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Auto Refresh 30s", command=self._start_auto_refresh).pack(side=tk.LEFT)

        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        left = ttk.Frame(main)
        right = ttk.Frame(main)
        main.add(left, weight=1)
        main.add(right, weight=2)

        self.listbox = tk.Listbox(left, exportselection=False)
        self.listbox.pack(fill=tk.BOTH, expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)

        details = ttk.LabelFrame(right, text="Item", padding=8)
        details.pack(fill=tk.BOTH, expand=True)

        self.item_meta = ttk.Label(details, text="No selection", justify=tk.LEFT)
        self.item_meta.pack(anchor="w", pady=(0, 8))

        self.item_text = tk.Text(details, height=12, wrap=tk.WORD)
        self.item_text.pack(fill=tk.BOTH, expand=True)

        actions = ttk.LabelFrame(right, text="Actions", padding=8)
        actions.pack(fill=tk.X, pady=(8, 0))

        row1 = ttk.Frame(actions)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Reply").pack(side=tk.LEFT)
        ttk.Entry(row1, textvariable=self.reply_text).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row1, text="Send", command=lambda: self._action_async("reply")).pack(side=tk.LEFT)

        row2 = ttk.Frame(actions)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Forward To").pack(side=tk.LEFT)
        ttk.Entry(row2, textvariable=self.forward_target).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row2, text="Forward", command=lambda: self._action_async("forward")).pack(side=tk.LEFT)

        row3 = ttk.Frame(actions)
        row3.pack(fill=tk.X, pady=2)
        ttk.Button(row3, text="Mark Spam", command=lambda: self._action_async("mark_spam")).pack(side=tk.LEFT)
        ttk.Button(row3, text="Archive", command=lambda: self._action_async("archive")).pack(side=tk.LEFT, padx=6)
        ttk.Button(
            row3,
            text="Send To Ramp",
            command=lambda: self._action_async("forward_to_ramp", target="receipts@ramp.com"),
        ).pack(side=tk.LEFT)

        row4 = ttk.Frame(actions)
        row4.pack(fill=tk.X, pady=2)
        ttk.Label(row4, text="Move Account").pack(side=tk.LEFT)
        ttk.Entry(row4, textvariable=self.move_target).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(row4, text="Move", command=lambda: self._action_async("move_account")).pack(side=tk.LEFT)

        voice = ttk.LabelFrame(right, text="Voice Command", padding=8)
        voice.pack(fill=tk.X, pady=(8, 0))
        ttk.Entry(voice, textvariable=self.voice_text).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(voice, text="Run", command=self._run_voice_async).pack(side=tk.LEFT, padx=6)

        status = ttk.Label(self.root, textvariable=self.status_text, anchor="w", relief=tk.SUNKEN)
        status.pack(fill=tk.X, side=tk.BOTTOM)

    def _connect(self) -> None:
        self.client = APIClient(self.server_url.get().strip())
        self.status_text.set(f"Connected to {self.client.base_url}")
        self._refresh_async()

    def _selected_item(self) -> FeedItem | None:
        if not self.listbox.curselection():
            return None
        idx = self.listbox.curselection()[0]
        if idx >= len(self.items):
            return None
        return self.items[idx]

    def _on_select(self, _event: tk.Event) -> None:
        item = self._selected_item()
        if not item:
            return

        ts = item.received_at
        try:
            ts = datetime.fromisoformat(item.received_at.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S %Z")
        except Exception:
            pass

        self.item_meta.config(text=f"{item.id}\n{item.source.upper()}  {item.account}\n{item.kind}  {ts}")
        self.item_text.delete("1.0", tk.END)
        self.item_text.insert(tk.END, item.summary if item.summary else item.body)

    def _refresh_async(self) -> None:
        self.status_text.set("Refreshing feed...")

        def worker() -> None:
            try:
                items = self.client.feed()
                self.root.after(0, lambda: self._set_items(items))
            except Exception as exc:
                self.root.after(0, lambda: self._error(f"Refresh failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _set_items(self, items: list[FeedItem]) -> None:
        self.items = items
        self.listbox.delete(0, tk.END)
        self.index_by_id.clear()
        for idx, item in enumerate(items):
            label = f"[{item.source}] {item.title}"
            self.listbox.insert(tk.END, label)
            self.index_by_id[item.id] = idx

        if items:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.event_generate("<<ListboxSelect>>")
        self.status_text.set(f"Loaded {len(items)} items")

    def _action_async(self, action: str, target: str | None = None, body: str | None = None) -> None:
        item = self._selected_item()
        if not item:
            messagebox.showwarning("No selection", "Select a feed item first.")
            return

        action_target = target if target is not None else self.forward_target.get().strip()
        if action == "move_account":
            action_target = self.move_target.get().strip()
        action_body = body if body is not None else self.reply_text.get().strip()

        self.status_text.set(f"Sending action {action} for {item.id}...")

        def worker() -> None:
            try:
                result = self.client.action(item.id, action, action_target, action_body)
                detail = result.get("detail", "Action completed")
                self.root.after(0, lambda: self.status_text.set(detail))
            except Exception as exc:
                self.root.after(0, lambda: self._error(f"Action failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _run_voice_async(self) -> None:
        transcript = self.voice_text.get().strip()
        if not transcript:
            messagebox.showwarning("Missing transcript", "Enter a voice transcript first.")
            return

        self.status_text.set("Parsing voice command...")

        def worker() -> None:
            try:
                parsed = self.client.parse_voice(transcript)
                command = parsed.get("command", "unknown")
                item_id = parsed.get("item_id")
                target = parsed.get("target") or ""
                body = parsed.get("body") or ""
                if command == "unknown" or not item_id:
                    self.root.after(0, lambda: self.status_text.set(f"Voice parsed as '{command}', no executable item"))
                    return
                if item_id not in self.index_by_id:
                    self.root.after(0, lambda: self.status_text.set(f"Voice item not in feed: {item_id}"))
                    return
                self.root.after(0, lambda: self._execute_voice(item_id, command, target, body))
            except Exception as exc:
                self.root.after(0, lambda: self._error(f"Voice parse failed: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _execute_voice(self, item_id: str, command: str, target: str, body: str) -> None:
        idx = self.index_by_id[item_id]
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.event_generate("<<ListboxSelect>>")
        self._action_async(command, target=target, body=body)

    def _start_auto_refresh(self) -> None:
        self.status_text.set("Auto refresh enabled (30s)")

        def tick() -> None:
            self._refresh_async()
            self.root.after(30_000, tick)

        self.root.after(30_000, tick)

    def _error(self, msg: str) -> None:
        self.status_text.set(msg)
        messagebox.showerror("Desktop Client", msg)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    DesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
