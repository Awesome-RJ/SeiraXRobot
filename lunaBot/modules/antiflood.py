import html
from typing import Optional, List
import re

from telegram import Message, Chat, Update, User, ChatPermissions

from lunaBot import TIGERS, WOLVES, dispatcher
from lunaBot.modules.helper_funcs.chat_status import (
    bot_admin,
    is_user_admin,
    user_admin,
    user_admin_no_reply,
)
from lunaBot.modules.log_channel import loggable
from lunaBot.modules.sql import antiflood_sql as sql
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html, escape_markdown
from lunaBot.modules.helper_funcs.string_handling import extract_time
from lunaBot.modules.connection import connected
from lunaBot.modules.helper_funcs.alternate import send_message
from lunaBot.modules.sql.approve_sql import is_approved

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(update, context) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    # ignore admins and whitelists
    if is_user_admin(chat, user.id) or user.id in WOLVES or user.id in TIGERS:
        sql.update_flood(chat.id, None)
        return ""
    # ignore approved users
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return
    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(
                chat.id, user.id, permissions=ChatPermissions(can_send_messages=False)
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = "Di Banned untuk {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Mute selama {}".format(getvalue)
            tag = "TMUTE"
        send_message(
            update.effective_message, "Beep Boop! Boop Beep!\n{}!".format(execstrings)
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>User:</b> {}"
            "\nFlooded the group.".format(
                tag,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )

    except BadRequest:
        msg.reply_text(
            "Saya tidak bisa membatasi penggunaan di sini, beri seira izin dulu!  Sampai saat itu, seira akan menonaktifkan anti-flood."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nTidak memiliki izin yang cukup untuk membatasi pengguna sehingga anti-flood secara otomatis dinonaktifkan".format(
                chat.title
            )
        )


@run_async
@user_admin_no_reply
@bot_admin
def flood_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    if match := re.match(r"unmute_flooder\((.+?)\)", query.data):
        user_id = match.group(1)
        chat = update.effective_chat.id
        try:
            bot.restrict_chat_member(
                chat,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            update.effective_message.edit_text(
                f"Di Mute oleh {mention_html(user.id, html.escape(user.first_name))}.",
                parse_mode="HTML",
            )
        except:
            pass


@run_async
@user_admin
@loggable
def set_flood(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini dimaksudkan untuk digunakan di grup bukan di PM",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat_id, 0)
            if conn:
                text = message.reply_text(
                    "Antiflood telah di nonaktifkan di {}.".format(chat_name)
                )
            else:
                text = message.reply_text("Antiflood has been disabled.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = message.reply_text(
                        "Antiflood telah di nonaktifkan di {}.".format(chat_name)
                    )
                else:
                    text = message.reply_text("Antiflood telah di nonaktifkan.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable antiflood.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                    )
                )

            elif amount <= 3:
                send_message(
                    update.effective_message,
                    "Antiflood harus 0 (disable) atau angka lebih besar dari 3!!",
                )
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = message.reply_text(
                        "Anti-flood telah di set menjadi {} di group: {}".format(
                            amount, chat_name
                        )
                    )
                else:
                    text = message.reply_text(
                        "Berhasil updated anti-flood limit ke {}!".format(amount)
                    )
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet antiflood ke <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, html.escape(user.first_name)),
                        amount,
                    )
                )

        else:
            message.reply_text("Argumen tidak valid, harap gunakan angka, 'off' or 'no'")
    else:
        message.reply_text(
            (
                "Gunakan `/setflood angka` untuk mengaktifkan anti-flood.\natau gunakan  `/setflood off` untuk menonaktifkan antiflood!."
            ),
            parse_mode="markdown",
        )
    return ""


@run_async
def flood(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini dimaksudkan untuk digunakan di group bukan di PM",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        text = (
            msg.reply_text(
                "Saya tidak menerapkan pengendalian anti-flood  di {}!".format(
                    chat_name
                )
            )
            if conn
            else msg.reply_text(
                "Saya tidak menerapkan pengendalian anti-flood di sini!"
            )
        )

    elif conn:
        text = msg.reply_text(
            "Saat ini saya membatasi anggota setelah {} berurutan di  {}.".format(
                limit, chat_name
            )
        )
    else:
        text = msg.reply_text(
            "Saat ini saya membatasi anggota setelah {} pesan berurutan.".format(
                limit
            )
        )


@run_async
@user_admin
def set_flood_mode(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(
                update.effective_message,
                "Perintah ini dimaksudkan untuk digunakan di group bukan di PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """Sepertinya Anda mencoba mengatur nilai waktu untuk antiflood tetapi Anda tidak menentukan waktu; coba dengan, `/setfloodmode tban <timevalue>`.
Contoh nilai waktu: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = "tban untuk {}".format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    update.effective_message,
                    """Sepertinya Anda mencoba mengatur nilai waktu untuk antiflood tetapi Anda tidak menentukan waktu; coba dengan, `/setfloodmode tmute <timevalue>`.
Contoh nilai waktu: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""",
                )
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = "tmute untuk {}".format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(
                update.effective_message, "saya hanya mengerti ban/kick/mute/tban/tmute!"
            )
            return
        if conn:
            text = msg.reply_text(
                "Exceeding consecutive flood limit will result in {} in {}!".format(
                    settypeflood, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Melebihi batas anti-flood berturut-turut akan mengakibatkan{}!".format(
                    settypeflood
                )
            )
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Telah menngubah antiflood mode. User akan {}.".format(
                settypeflood,
                html.escape(chat.title),
                mention_html(user.id, html.escape(user.first_name)),
            )
        )
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = "ban"
        elif getmode == 2:
            settypeflood = "kick"
        elif getmode == 3:
            settypeflood = "mute"
        elif getmode == 4:
            settypeflood = "tban untuk {}".format(getvalue)
        elif getmode == 5:
            settypeflood = "tmute untuk {}".format(getvalue)
        if conn:
            text = msg.reply_text(
                "Mengirim lebih banyak pesan melebihi limit flood akan mengakibatkan {} di {}.".format(
                    settypeflood, chat_name
                )
            )
        else:
            text = msg.reply_text(
                "Mengirim lebih banyak pesan melebihi limit floor akan mengakibatkan {}.".format(
                    settypeflood
                )
            )
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Tidak menegakkan pengendalian anti-flood."
    else:
        return "Antiflood telah di set ke`{}`.".format(limit)


__help__ = """

*Pembersih text biru* menghapus semua perintah yang dibuat-buat dan dikirim user dalam obrolan Anda.
 ❍ /cleanblue <on/off/yes/no>*:* menghapus perintah setelah mengirim
 ❍ /ignoreblue <word>*:* mencegah pembersihan otomatis dari perintah
 ❍ /unignoreblue <word>*:* menghapus dan mencegah pembersihan otomatis dari perintah
 ❍ /listblue*:* daftar perintah yang saat ini masuk daftar putih

*Antiflood* memungkinkan Anda untuk mengambil tindakan pada pengguna yang mengirim lebih dari x pesan berturut-turut.  Melebihi flood yang ditetapkan \
 akan mengakibatkan pembatasan pengguna itu.
 Ini akan membisukan pengguna jika mereka mengirim lebih dari 10 pesan berturut-turut, bot diabaikan.
 ❍ /flood*:* Dapatkan pengaturan pengendalian flood saat ini
• *Admins only:*
 ❍ /setflood <int/'no'/'off'>*:* Mengaktifkan atau Menonaktifkan flood control
 *Example:* `/setflood 10`
 ❍ /setfloodmode <ban/kick/mute/tban/tmute> <value>*:* Tindakan yang harus dilakukan ketika pengguna telah melampaui batas flood. ban/kick/mute/tmute/tban
• *Note:*
 • Angka harus diisi untuk tban dan tmute!!
 Bisa jadi seperti:
 `5m` = 5 minutes
 `6h` = 6 hours
 `3d` = 3 days
 `1w` = 1 week
 """

__mod_name__ = "AntiFlood"

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.group, check_flood
)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, filters=Filters.group)
SET_FLOOD_MODE_HANDLER = CommandHandler(
    "setfloodmode", set_flood_mode, pass_args=True
)  # , filters=Filters.group)
FLOOD_QUERY_HANDLER = CallbackQueryHandler(flood_button, pattern=r"unmute_flooder")
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(FLOOD_QUERY_HANDLER)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)

__handlers__ = [
    (FLOOD_BAN_HANDLER, FLOOD_GROUP),
    SET_FLOOD_HANDLER,
    FLOOD_HANDLER,
    SET_FLOOD_MODE_HANDLER,
]
