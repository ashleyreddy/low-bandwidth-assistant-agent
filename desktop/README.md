# Desktop Client

This desktop client is a lightweight Tkinter GUI that talks to the FastAPI server.

## Run

```bash
cd /home/ros2/low-bandwidth-assistant
python3 desktop/client.py
```

Default server URL is `http://127.0.0.1:8000`.

## Supported Actions

- Message: `reply`, `forward`, `mark_spam`, `archive`
- Image: `forward_to_ramp`, `move_account`
- Voice transcript command execution through `/v1/voice/command`
