# 🗄 Telegram File Vault Bot

Store files in Telegram — stream on demand. No local downloads. Zero device storage used.

## Features

✅ **Files stored on Telegram's CDN** — Never downloaded to your server  
✅ **Streaming on demand** — Only fetch files when you need them  
✅ **Lightweight index** — Just metadata, no file bytes cached  
✅ **Admin uploads** — Forward/send files to add to vault  
✅ **User-friendly** — Search, browse, and retrieve files easily  
✅ **Secure access** — Admin-only file management  

## How It Works

1. **Admin forwards/sends a file** to the bot  
2. **Bot stores the Telegram `file_id` + metadata** in a local JSON index (not the file itself)  
3. **Users send commands** like `/list` or `/get <name>`  
4. **Bot sends a direct Telegram link** to the file  
5. **File is streamed from Telegram's CDN** — never downloaded to your device

## Requirements

- Python 3.8+
- `python-telegram-bot==20.7`
- `python-dotenv==0.21.0`

## Installation

```bash
# Clone the repository
git clone https://github.com/Trenchbb/Tgbonkrrbot.git
cd Tgbonkrrbot

# Install dependencies
pip install -r requirements.txt
```

## Setup

1. Create a `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```
   BOT_TOKEN=your_bot_token_here
   VAULT_CHANNEL_ID=-100xxxxxxxxx
   ADMIN_IDS=123456789,987654321
   ```

3. Run the bot:
   ```bash
   python telegram_vault_bot.py
   ```

## Commands

### For Everyone
- `/start` — Show help and available commands
- `/list` — Browse all stored files with inline buttons
- `/get <filename>` — Retrieve a file by name
- `/search <query>` — Search files by name
- `/info <filename>` — View file metadata and CDN link

### For Admins
- **Forward any file** to the bot to add it to the vault
- `/delete <filename>` — Remove a file from the index

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from BotFather | `123456:ABCdefGHIjklmnOPQRstuvWXYZ` |
| `VAULT_CHANNEL_ID` | Private channel ID for storing files | `-1001234567890` |
| `ADMIN_IDS` | Comma-separated admin user IDs | `123456789,987654321` |

## File Index

The bot maintains a lightweight JSON index (`vault_index.json`):

```json
{
  "filename": {
    "name": "filename",
    "file_id": "AgADBAAD...",
    "file_type": "document",
    "size_bytes": 1024000,
    "message_id": 42,
    "channel_id": -1001234567890
  }
}
```

**Note:** Only metadata is stored — file bytes are never cached on your server.

## Architecture

```
┌─────────────────┐
│   User/Admin    │
└────────┬────────┘
         │
    Command/File
         │
    ┌────▼─────────────────────────────┐
    │   Telegram File Vault Bot        │
    │  ✓ Processes commands            │
    │  ✓ Manages vault_index.json      │
    │  ✓ Forwards files to vault       │
    └────┬─────────────────────────────┘
         │
    ┌────┴──────────────────┬──────────────────┐
    │                       │                  │
    ▼                       ▼                  ▼
���──────────────┐   ┌──────────────┐   ┌──────────────┐
│  vault_      │   │   Telegram   │   │  Telegram    │
│  index.json  │   │   Vault      │   │  User Chat   │
│  (metadata)  │   │  Channel     │   │  (requests)  │
└──────────────┘   │  (file_ids)  │   └──────────────┘
                   └──────────────┘
                         │
                    ┌────▼──────────┐
                    │  Telegram CDN  │
                    │  (streaming)   │
                    └────────────────┘
```

## Storage Usage

- **Server storage:** ~1-10 KB per 100 files (metadata only)
- **Device storage:** 0 KB until you open a file
- **Bandwidth:** Only when files are accessed

## Security Notes

- 🔒 **Admin-only uploads** — Only admins can add files
- 🔒 **Private channel** — Keep vault channel restricted
- 🔒 **file_id protection** — File IDs are Telegram-only tokens
- 🔒 **No file bytes on server** — Just metadata stored locally

## License

MIT License — See LICENSE file for details

## Support

For issues or questions, open a GitHub issue or check the [python-telegram-bot documentation](https://python-telegram-bot.readthedocs.io/).