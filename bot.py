import os
import zipfile
import asyncio
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, CallbackContext, filters
from yt_dlp import YoutubeDL

# Function to download YouTube content
async def download_content(url, format_type='video'):
    download_path = "./downloads"
    os.makedirs(download_path, exist_ok=True)

    # Configure download options
    ydl_opts = {
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio' if format_type == 'video' else 'bestaudio',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if format_type == 'audio' else [],
    }

    downloaded_files = []
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if 'entries' in info:  # It's a playlist
            for entry in info['entries']:
                downloaded_files.append(ydl.prepare_filename(entry))
        else:
            downloaded_files.append(ydl.prepare_filename(info))

    return downloaded_files

# Create a ZIP file for playlists
def create_zip_file(file_list, zip_name="playlist.zip"):
    zip_path = f"./downloads/{zip_name}"
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in file_list:
            zipf.write(file, os.path.basename(file))
    return zip_path

# Command to start the bot
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Welcome to YouTube Downloader Bot!\nSend me a YouTube URL to get started.")

# Ask user for format selection
async def ask_format(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if "youtube.com" in url or "youtu.be" in url:
        keyboard = [
            [InlineKeyboardButton("Video", callback_data=f"video|{url}")],
            [InlineKeyboardButton("Audio", callback_data=f"audio|{url}")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Choose the format you want to download:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Please send a valid YouTube URL.")

# Handle format selection
async def handle_format(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    format_type, url = query.data.split("|")
    await query.edit_message_text("Processing your request. Please wait...")

    try:
        # Download content
        downloaded_files = await download_content(url, format_type=format_type)

        if len(downloaded_files) > 1:  # It's a playlist
            zip_path = create_zip_file(downloaded_files)
            await query.edit_message_text("Playlist download complete. Sending ZIP file...")

            with open(zip_path, 'rb') as zip_file:
                await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(zip_file))

            os.remove(zip_path)  # Clean up ZIP file
        else:  # Single video or audio
            await query.edit_message_text("Download complete. Sending file...")

            with open(downloaded_files[0], 'rb') as file:
                await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(file))

        # Clean up downloaded files
        for file in downloaded_files:
            if os.path.exists(file):
                os.remove(file)
    except Exception as e:
        await query.edit_message_text(f"An error occurred: {e}")

# Main function to set up the bot
async def main():
    bot_token = "YOUR_BOT_TOKEN"
    app = ApplicationBuilder().token(bot_token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_format))
    app.add_handler(CallbackQueryHandler(handle_format))

    print("Bot is running...")
    await app.run_polling()

# Run the bot
if __name__ == '__main__':
    import asyncio

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise

                      
