import asyncio
from pathlib import Path

from telegram import Update, InputFile
from telegram.constants import MessageOriginType   # ✅ YAHAN ADD KARNA HAI
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================== CONFIG ==================

BOT_TOKEN = "8187041029:AAHLpi0yxr7AN-GugaI6pIw9yZ3IrUwHTfA"

OWNER_ID = 8499902934

ID_FILE = Path("user_ids.txt")

saved_ids: set[int] = set()


# ================== HELPER FUNCTIONS ==================

def load_ids() -> None:
    global saved_ids
    saved_ids.clear()
    if ID_FILE.exists():
        for line in ID_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.isdigit():
                saved_ids.add(int(line))


def save_id_to_file(user_id: int) -> None:
    global saved_ids
    if user_id not in saved_ids:
        saved_ids.add(user_id)
        with ID_FILE.open("a", encoding="utf-8") as f:
            f.write(f"{user_id}\n")


def import_ids_from_text(text: str) -> int:
    global saved_ids
    new_count = 0
    lines = text.splitlines()
    to_append = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not line.isdigit():
            continue

        uid = int(line)
        if uid not in saved_ids:
            saved_ids.add(uid)
            to_append.append(uid)
            new_count += 1

    if to_append:
        with ID_FILE.open("a", encoding="utf-8") as f:
            for uid in to_append:
                f.write(f"{uid}\n")

    return new_count


# ================== COMMAND HANDLERS ==================

async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return
    await update.effective_message.reply_text(
        f"Your user ID: `{user.id}`",
        parse_mode="Markdown"
    )


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("pong. bot chal raha hai ✅")


async def exportuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    if user.id != OWNER_ID:
        await update.effective_message.reply_text("⛔ Ye command sirf owner use kar sakta hai.")
        return

    if not saved_ids:
        await update.effective_message.reply_text("Koi user ID save nahi hai abhi.")
        return

    message = update.effective_message

    export_path = Path("users_export.txt")
    export_path.write_text(
        "\n".join(str(uid) for uid in sorted(saved_ids)),
        encoding="utf-8"
    )

    with export_path.open("rb") as f:
        await message.reply_document(
            document=InputFile(f),
            filename="users_export.txt",
            caption=f"Total {len(saved_ids)} user IDs export ki gayi. ✅",
        )

async def importuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    if user.id != OWNER_ID:
        await update.effective_message.reply_text("⛔ Ye command sirf owner use kar sakta hai.")
        return

    message = update.effective_message

    if not message.reply_to_message or not message.reply_to_message.document:
        await message.reply_text("❗ /importuser use karne ke liye kisi TXT file pe reply karo.")
        return

    await message.reply_text("📥 File download ho rahi hai, thoda wait karo...")

    doc = message.reply_to_message.document
    file = await doc.get_file()
    file_bytes = await file.download_as_bytearray()
    content = file_bytes.decode("utf-8", errors="ignore")

    new_count = import_ids_from_text(content)

    await message.reply_text(
        f"✅ Import complete.\n"
        f"Naye IDs add hue: {new_count}\n"
        f"Total unique IDs ab: {len(saved_ids)}"
    )

async def usercount_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    if user.id != OWNER_ID:
        await update.effective_message.reply_text("⛔ Ye command sirf owner use kar sakta hai.")
        return

    await update.effective_message.reply_text(
        f"👥 Total unique users: {len(saved_ids)}"
    )

async def forward_auto_save_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.effective_message
    if not message:
        return

    origin = message.forward_origin
    if not origin:
        return

    # Agar message kisi USER se forward hua ho
    if origin.type == MessageOriginType.USER:
        uid = origin.sender_user.id
        save_id_to_file(uid)

# ================== MESSAGE HANDLER ==================

async def autosave_ids_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    save_id_to_file(user.id)


# ================== MAIN ==================

def main() -> None:
    load_ids()

    app = Application.builder().token(BOT_TOKEN).build()

    # 🔹 NEW: Forwarded message auto-save (ANY user)
    app.add_handler(
        MessageHandler(filters.FORWARDED, forward_auto_save_handler),
        group=0
    )

    # 🔹 OLD: Auto save normal messages (commands ignore)
    app.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND, autosave_ids_handler),
        group=1
    )

    # 🔹 COMMAND handlers (OWNER only where applied)
    app.add_handler(CommandHandler("myid", myid_command), group=0)
    app.add_handler(CommandHandler("ping", ping_command), group=0)
    app.add_handler(CommandHandler("exportuser", exportuser_command), group=0)
    app.add_handler(CommandHandler("importuser", importuser_command), group=0)
    app.add_handler(CommandHandler("usercount", usercount_command), group=0)

    print("Bot chal raha hai... Ctrl+C se band kar sakte ho.")
    app.run_polling()


if __name__ == "__main__":
    main()
