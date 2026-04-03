import os
import json
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────

BOT_TOKEN       = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
VAULT_CHANNEL_ID = int(os.environ.get("VAULT_CHANNEL_ID", "0"))
ADMIN_IDS       = set(map(int, os.environ.get("ADMIN_IDS", "").split(","))) if os.environ.get("ADMIN_IDS") else set()
INDEX_FILE      = Path("vault_index.json")

# ── Index helpers ─────────────────────────────────────────────────────────────

def load_index() -> dict:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return {}

def save_index(index: dict):
    INDEX_FILE.write_text(json.dumps(index, indent=2))

def add_to_index(name: str, file_id: str, file_type: str, size: int, message_id: int):
    index = load_index()
    index[name.lower()] = {
        "name": name,
        "file_id": file_id,
        "file_type": file_type,
        "size_bytes": size,
        "message_id": message_id,
        "channel_id": VAULT_CHANNEL_ID,
    }
    save_index(index)
    return index[name.lower()]

# ── Commands ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🗄 *Telegram File Vault*\n\n"
        "Files live in Telegram — never on your device until you open them.\n\n"
        "*Commands:*\n"
        "• /list — browse all stored files\n"
        "• /get `<name>` — retrieve a file by name\n"
        "• /search `<query>` — search files\n"
        "• /info `<name>` — file metadata\n\n"
        "*Admins: forward any file to me to add it to the vault.*"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    index = load_index()
    if not index:
        await update.message.reply_text("📭 Vault is empty. Admins can forward files to add them.")
        return

    items = sorted(index.values(), key=lambda x: x["name"])
    buttons = []
    for item in items[:20]:
        size_kb = item["size_bytes"] // 1024
        icon = '📄' if item['file_type']=='document' else '🎬' if item['file_type']=='video' else '🖼' if item['file_type']=='photo' else '🎵'
        label = f"{icon} {item['name']} ({size_kb} KB)"
        buttons.append([InlineKeyboardButton(label, callback_data=f"get:{item['name'].lower()}")])

    markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        f"🗄 *Vault — {len(index)} file(s)*\nTap to stream any file:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

async def cmd_get(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /get <filename>")
        return
    name = " ".join(ctx.args).lower()
    await _send_file(update, ctx, name)

async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /search <query>")
        return
    query = " ".join(ctx.args).lower()
    index = load_index()
    matches = [v for k, v in index.items() if query in k]

    if not matches:
        await update.message.reply_text(f"🔍 No files matching *{query}*.", parse_mode="Markdown")
        return

    buttons = [[InlineKeyboardButton(m["name"], callback_data=f"get:{m['name'].lower()}")] for m in matches[:10]]
    await update.message.reply_text(
        f"🔍 *{len(matches)} result(s)* for `{query}`:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def cmd_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("Usage: /info <filename>")
        return
    name = " ".join(ctx.args).lower()
    index = load_index()
    item = index.get(name)
    if not item:
        await update.message.reply_text(f"❌ File `{name}` not found.", parse_mode="Markdown")
        return

    size_kb = item["size_bytes"] // 1024
    channel_str = str(item["channel_id"]).replace("-100", "")
    deep_link = f"https://t.me/c/{channel_str}/{item['message_id']}"
    text = (
        f"📋 *{item['name']}*\n"
        f"Type: `{item['file_type']}`\n"
        f"Size: `{size_kb} KB`\n"
        f"[Open in vault channel]({deep_link})\n\n"
        f"_File is stored on Telegram's CDN — tap to stream, no device storage used._"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def on_button(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("get:"):
        name = query.data[4:]
        await _send_file(query, ctx, name, from_callback=True)

async def _send_file(update, ctx, name: str, from_callback=False):
    index = load_index()
    item = index.get(name)
    chat_id = update.message.chat_id if not from_callback else update.message.chat.id

    if not item:
        msg = f"❌ File `{name}` not found. Use /list to browse."
        if from_callback:
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(msg, parse_mode="Markdown")
        return

    ftype = item["file_type"]
    fid = item["file_id"]
    caption = f"📁 *{item['name']}* — streamed from Telegram vault\n_No storage used on your device._"

    send = update.message.reply_document if ftype == "document" else \
           update.message.reply_video    if ftype == "video"    else \
           update.message.reply_photo    if ftype == "photo"    else \
           update.message.reply_audio

    await send(fid, caption=caption, parse_mode="Markdown")

async def on_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Only admins can add files to the vault.")
        return

    msg = update.message
    file_obj = file_type = None

    if msg.document:
        file_obj, file_type = msg.document, "document"
    elif msg.video:
        file_obj, file_type = msg.video, "video"
    elif msg.audio:
        file_obj, file_type = msg.audio, "audio"
    elif msg.photo:
        file_obj, file_type = msg.photo[-1], "photo"
    else:
        return

    name = (msg.caption or getattr(file_obj, "file_name", None) or file_obj.file_unique_id[:12]).strip()

    if VAULT_CHANNEL_ID:
        fwd = await ctx.bot.forward_message(
            chat_id=VAULT_CHANNEL_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id
        )
        message_id = fwd.message_id
    else:
        message_id = msg.message_id

    size = getattr(file_obj, "file_size", 0) or 0
    add_to_index(name, file_obj.file_id, file_type, size, message_id)

    await msg.reply_text(
        f"✅ *{name}* added to vault!\n"
        f"Type: `{file_type}` | Size: `{size // 1024} KB`\n"
        f"_Stored as Telegram file_id only — no bytes on server._",
        parse_mode="Markdown"
    )

async def cmd_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admins only.")
        return
    if not ctx.args:
        await update.message.reply_text("Usage: /delete <filename>")
        return
    name = " ".join(ctx.args).lower()
    index = load_index()
    if name in index:
        del index[name]
        save_index(index)
        await update.message.reply_text(f"🗑 `{name}` removed from vault index.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ `{name}` not found.", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("list",   cmd_list))
    app.add_handler(CommandHandler("get",    cmd_get))
    app.add_handler(CommandHandler("search", cmd_search))
    app.add_handler(CommandHandler("info",   cmd_info))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CallbackQueryHandler(on_button))

    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.VIDEO | filters.AUDIO | filters.PHOTO,
        on_file
    ))

    logger.info("🤖 Vault bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()