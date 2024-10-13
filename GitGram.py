#!/usr/bin/env python3

from logging import basicConfig, getLogger, INFO
from flask import Flask, request, jsonify
from html import escape as html_escape
from requests import get, post
from os import environ
import config

from telegram.ext import CommandHandler, Updater

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

updater = Updater(token=BOT_TOKEN, workers=1)
dispatcher = updater.dispatcher

print("If you need more help, join @GitGramChat in Telegram.")


def start(_bot, update):
    """/start message for bot"""
    message = update.effective_message
    message.reply_text(
        f"Ini adalah github notifications {PROJECT_NAME}. Saya cuma memberi notifikasi dari github melalui webhooks.\n\nKamu perlu menambahkan saya ke group atau ketik /help untuk menggunakan saya di group.",
        parse_mode="markdown")


def help(_bot, update):
    """/help message for the bot"""
    message = update.effective_message
    message.reply_text(
        f"*Available Commands*\n\n`/connect` - Setup how to connect this chat to receive Git activity notifications.\n`/support` - Get links to get support if you're stuck.\n`/source` - Get the Git repository URL.",
        parse_mode="markdown"
    )


def support(_bot, update):
    """Links to Support"""
    message = update.effective_message
    message.reply_text(
        f"*Getting Support*\n\nTo get support in using the bot, join [Er support](https://t.me/Er_Support_Group).",
        parse_mode="markdown"
    )


def source(_bot, update):
    """Link to Source"""
    message = update.effective_message
    message.reply_text(
        f"*Source*:\n[Repo](https://xnxx.com).",
        parse_mode="markdown"
    )


def getSourceCodeLink(_bot, update):
    """Pulls link to the source code."""
    message = update.effective_message
    message.reply_text(
        f"{GIT_REPO_URL}"
    )


start_handler = CommandHandler("start", start)
help_handler = CommandHandler("help", help)
supportCmd = CommandHandler("support", support)
sourcecode = CommandHandler("source", source)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
dispatcher.add_handler(supportCmd)
dispatcher.add_handler(sourcecode)
updater.start_polling()

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

    if data.get('commits'):
        commits_text = ""
        rng = len(data['commits'])
        if rng > 10:
            rng = 10
        for x in range(rng):
            commit = data['commits'][x]
            commit_msg = html_escape(commit['message'])[:300].split("\n")[0]
            commits_text += f"{commit_msg}\n<a href='{commit['url']}'>{commit['id'][:7]}</a> - {commit['author']['name']} <{html_escape(commit['author']['email'])}>\n\n"
            if len(commits_text) > 1000:
                text = f"""✨ <b>{html_escape(data['repository']['name'])}</b> - New {len(data['commits'])} commits ({html_escape(data['ref'].split('/')[-1])})
{commits_text}
"""
                response = post_tg(groupid, text, "html")
                commits_text = ""
        if not commits_text:
            return jsonify({"ok": True, "text": "Commits text tidak ada"})
        text = f"""✨ <b>{html_escape(data['repository']['name'])}</b> - New {len(data['commits'])} commits ({html_escape(data['ref'].split('/')[-1])})
{commits_text}
"""
        if len(data['commits']) > 10:
            text += f"\n\n<i>And {len(data['commits']) - 10} other commits</i>"
        response = post_tg(groupid, text, "html")
        return response

    if data.get('issue'):
        if data.get('comment'):
            text = f"""💬 New comment: <b>{html_escape(data['repository']['name'])}</b>
{html_escape(data['comment']['body'])}

<a href='{data['comment']['html_url']}'>Issue #{data['issue']['number']}</a>
"""
            response = post_tg(groupid, text, "html")
            return response
        text = f"""🚨 New {data['action']} issue for <b>{html_escape(data['repository']['name'])}</b>
<b>{html_escape(data['issue']['title'])}</b>
{html_escape(data['issue']['body'])}

<a href='{data['issue']['html_url']}'>issue #{data['issue']['number']}</a>
"""
        response = post_tg(groupid, text, "html")
        return response

    if data.get('pull_request'):
        if data.get('comment'):
            text = f"""❗ There is a new pull request for <b>{html_escape(data['repository']['name'])}</b> ({data['pull_request']['state']})
{html_escape(data['comment']['body'])}

<a href='{data['comment']['html_url']}'>Pull request #{data['issue']['number']}</a>
"""
            response = post_tg(groupid, text, "html")
            return response
        text = f"""❗  New {data['action']} pull request for <b>{html_escape(data['repository']['name'])}</b>
<b>{html_escape(data['pull_request']['title'])}</b> ({data['pull_request']['state']})
{html_escape(data['pull_request']['body'])}

<a href='{data['pull_request']['html_url']}'>Pull request #{data['pull_request']['number']}</a>
"""
        response = post_tg(groupid, text, "html")
        return response

    if data.get('forkee'):
        response = post_tg(
            groupid,
            f"🍴 <a href='{data['sender']['html_url']}'>{data['sender']['login']}</a> forked <a href='{data['repository']['html_url']}'>{data['repository']['name']}</a>!\nTotal forks now are {data['repository']['forks_count']}",
            "html")
        return response

    if data.get('action'):
        if data.get('action') == "published" and data.get('release'):
            text = f"<a href='{data['sender']['html_url']}'>{data['sender']['login']}</a> published a release for <b>{html_escape(data['repository']['name'])}</b> v{html_escape(data['release']['tag_name'])}\n" + html_escape(data['release']['body'])
            response = post_tg(groupid, text, "html")
            return response

    return jsonify({"ok": True})


if __name__ == "__main__":
    # We can't use port 80 due to the root access requirement.
    port = int(environ.get("PORT", 8080))
    server.run(host="0.0.0.0", port=port)
