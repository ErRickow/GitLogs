#!/usr/bin/env python3

from logging import basicConfig, getLogger, INFO
from flask import Flask, request, jsonify
from html import escape
from requests import get, post
from os import environ
import config

from telegram.ext import CommandHandler, Application, MessageHandler, filters

server = Flask(__name__)

basicConfig(level=INFO)
log = getLogger()

ENV = bool(environ.get('ENV', False))

if ENV:
    BOT_TOKEN = environ.get('BOT_TOKEN', None)
    PROJECT_NAME = environ.get('PROJECT_NAME', None)
    ip_addr = environ.get('APP_URL', None)
    GIT_REPO_URL = environ.get('GIT_REPO_URL', "https://github.com/ErRickow/GitLogs")
else:
    BOT_TOKEN = config.BOT_TOKEN
    PROJECT_NAME = config.PROJECT_NAME
    ip_addr = get('https://api.ipify.org').text
    GIT_REPO_URL = config.GIT_REPO_URL

# Menggunakan Application.builder() untuk menggantikan Updater
application = Application.builder().token(BOT_TOKEN).build()

print("If you need more help, join @GitGramChat in Telegram.")


async def start(update, context):
    """/start message for bot"""
    message = update.effective_message
    await message.reply_text(
        f"Ini adalah github notifications {PROJECT_NAME}. Saya cuma memberi notifikasi dari github melalui webhooks.\n\nKamu perlu menambahkan saya ke group atau ketik /help untuk menggunakan saya di group.",
        parse_mode="markdown")


async def help(update, context):
    """/help message for the bot"""
    message = update.effective_message
    await message.reply_text(
        f"*Available Commands*\n\n`/connect` - Setup how to connect this chat to receive Git activity notifications.\n`/support` - Get links to get support if you're stuck.\n`/source` - Get the Git repository URL.",
        parse_mode="markdown"
    )


async def support(update, context):
    """Links to Support"""
    message = update.effective_message
    await message.reply_text(
        f"*Getting Support*\n\nTo get support in using the bot, join [Er support](https://t.me/Er_Support_Group).",
        parse_mode="markdown"
    )


async def source(update, context):
    """Link to Source"""
    message = update.effective_message
    await message.reply_text(
        f"*Source*:\n[Repo](https://xnxx.com).",
        parse_mode="markdown"
    )


async def getSourceCodeLink(update, context):
    """Pulls link to the source code."""
    message = update.effective_message
    await message.reply_text(
        f"{GIT_REPO_URL}"
    )

# Menambahkan handler sesuai dengan versi baru
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help))
application.add_handler(CommandHandler("support", support))
application.add_handler(CommandHandler("source", source))

# Mulai polling
application.run_polling()

TG_BOT_API = f'https://api.telegram.org/bot{BOT_TOKEN}/'
checkbot = get(TG_BOT_API + "getMe").json()
if not checkbot['ok']:
    log.error("[ERROR] Invalid Token!")
    exit(1)
else:
    username = checkbot['result']['username']
    log.info(
        f"[INFO] Logged in as @{username}, waiting for webhook requests...")


def post_tg(chat, message, parse_mode):
    """Send message to desired group"""
    response = post(
        TG_BOT_API + "sendMessage",
        params={
            "chat_id": chat,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True}).json()
    return response


def reply_tg(chat, message_id, message, parse_mode):
    """reply to message_id"""
    response = post(
        TG_BOT_API + "sendMessage",
        params={
            "chat_id": chat,
            "reply_to_message_id": message_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True}).json()
    return response


@server.route("/", methods=['GET'])
# Just send 'Hello, world!' to tell that our server is up.
def helloWorld():
    return 'Ngaceng!'


@server.route("/<groupid>", methods=['GET', 'POST'])
def git_api(groupid):
    """Requests to api.github.com"""
    data = request.json
    if not data:
        return f"<b>Add this url:</b> {ip_addr}/{groupid} to webhooks of the project"

    if data.get('hook'):
        repo_url = data['repository']['html_url']
        repo_name = data['repository']['name']
        sender_url = data['sender']['html_url']
        sender_name = data['sender']['login']
        response = post_tg(
            groupid,
            f"🙌 Successfully set webhook for <a href='{repo_url}'>{repo_name}</a> by <a href='{sender_url}'>{sender_name}</a>!",
            "html"
        )
        return response

    # Implementasi lainnya tidak berubah, tetap sama

if __name__ == "__main__":
    # We can't use port 80 due to the root access requirement.
    port = int(environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)
