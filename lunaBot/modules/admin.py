import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

from lunaBot import DRAGONS, dispatcher
from lunaBot.modules.disable import DisableAbleCommandHandler
from lunaBot.modules.helper_funcs.chat_status import (
    bot_admin,
    can_pin,
    can_promote,
    connection_status,
    user_admin,
    ADMIN_CACHE,
)
from lunaBot.helper_extra.admin_rights import (
    user_can_pin,
    user_can_promote,
    user_can_changeinfo,
)

from lunaBot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from lunaBot.modules.log_channel import loggable
from lunaBot.modules.helper_funcs.alternate import send_message
from lunaBot.modules.helper_funcs.alternate import typing_action


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def promote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    if (
        not (promoter.can_promote_members or promoter.status == "creator")
        and user.id not in DRAGONS
    ):
        message.reply_text("Anda tidak memiliki hak yang diperlukan untuk melakukan itu!")
        return

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Anda sepertinya tidak merujuk ke pengguna atau ID yang ditentukan.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "administrator" or user_member.status == "creator":
        message.reply_text("Bagaimana saya mempromosikan seseorang yang sudah menjadi admin?")
        return

    if user_id == bot.id:
        message.reply_text("aku tidak bisa mempromosikan diriku sendiri! Panggil admin untuk melakukannya.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = chat.get_member(bot.id)

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            # can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("Saya tidak dapat mempromosikan seseorang yang tidak ada dalam grup.")
        else:
            message.reply_text("Terjadi kesalahan saat mempromosikan.")
        return

    bot.sendMessage(
        chat.id,
        f"Berhasil mempromosikan <b>{user_member.user.first_name or user_id}</b>!",
        parse_mode=ParseMode.HTML,
    )

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"USER PROMOTED SUCCESSFULLY\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
def demote(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)

    if user_can_promote(chat, user, context.bot.id) is False:
        message.reply_text("Anda tidak memiliki cukup hak untuk menurunkan seseorang!!")
        return ""

    if not user_id:
        message.reply_text(
            "Anda sepertinya tidak merujuk ke pengguna atau ID yang ditentukan salah.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        message.reply_text("Orang ini adalah Owner, bagaimana cara saya menurunkannya??")
        return

    if not user_member.status == "administrator":
        message.reply_text("Tidak dapat menurunkan apa yang tidak dipromosikan!")
        return

    if user_id == bot.id:
        message.reply_text("Saya tidak bisa menurunkan diri saya sendiri! Panggil admin untuk melakukan nya.")
        return

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
        )

        bot.sendMessage(
            chat.id,
            f"Berhasil menurunkan <b>{user_member.user.first_name or user_id}</b>!",
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"USER DEMOTED SUCCESSFULLY\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        message.reply_text(
            "Tidak dapat menurunkan. Saya mungkin bukan admin, atau status admin ditunjuk oleh yang lain."
            " user, jadi saya tidak bisa bertindak atas mereka!"
        )
        return


@run_async
@user_admin
def refresh_admin(update, _):
    try:
        ADMIN_CACHE.pop(update.effective_chat.id)
    except KeyError:
        pass

    update.effective_message.reply_text("Cache admin diperbarui!")


@run_async
@connection_status
@bot_admin
@can_promote
@user_admin
def set_title(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        message.reply_text(
            "Anda sepertinya tidak merujuk ke pengguna atau ID yang ditentukan salah."
        )
        return

    if user_member.status == "creator":
        message.reply_text(
            "Orang ini adalah owner grup, bagaimana saya bisa mengatur title untuknya??"
        )
        return

    if user_member.status != "administrator":
        message.reply_text(
            "Tidak dapat menyetel title untuk non-admin!\nPromosikan mereka terlebih dahulu untuk menetapkan title khusus!"
        )
        return

    if user_id == bot.id:
        message.reply_text(
            "Aku tidak dapat men-setting title ku sendiri! Dapatkan orang yang menjadikan saya admin untuk melakukannya untuk saya."
        )
        return

    if not title:
        message.reply_text("Mengatur titel kosong tidak merubah apa-apa!")
        return

    if len(title) > 16:
        message.reply_text(
            "Panjang title lebih dari 16 karakter.\nMemotongnya menjadi >16 karakter."
        )

    try:
        bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        message.reply_text("Saya tidak dapat menetapkan titel untuk admin yang tidak saya promosikan!")
        return

    bot.sendMessage(
        chat.id,
        f"Berhasil set title untuk <code>{user_member.user.first_name or user_id}</code> "
        f"ke <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@run_async
@bot_admin
@user_admin
@typing_action
def setchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Anda tidak memiliki hak untuk mengubah info grup!")
        return

    if msg.reply_to_message:
        if msg.reply_to_message.photo:
            pic_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            pic_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Anda hanya dapat mengatur satu foto sebagai gambar group!")
      
        dlmsg = msg.reply_text("Sebentar yaa...")
        tpic = context.bot.get_file(pic_id)
        tpic.download("gpic.png")
        try:
            with open("gpic.png", "rb") as chatp:
                context.bot.set_chat_photo(int(chat.id), photo=chatp)
                msg.reply_text("Berhasil mengganti foto grup!")
        except BadRequest as excp:
            msg.reply_text(f"Error! {excp.message}")
        finally:
            dlmsg.delete()
            if os.path.isfile("gpic.png"):
                os.remove("gpic.png")
    else:
        msg.reply_text("Balas ke photo atau file untuk men-setting foto grup baru!")


@run_async
@bot_admin
@user_admin
@typing_action
def rmchatpic(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Kamu tidak punya hak untuk menghapus group photo")
        return
    try:
        context.bot.delete_chat_photo(int(chat.id))
        msg.reply_text("Berhasil menghapus profile photo!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@run_async
@bot_admin
@user_admin
@typing_action
def setchat_title(update, context):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        msg.reply_text("Kamu tidak memiliki hak untuk mengubah chat info!")
        return

    title = " ".join(args)
    if not title:
        msg.reply_text("Masukkan beberapa teks untuk menetapkan title baru di grup Anda")
        return

    try:
        context.bot.set_chat_title(int(chat.id), str(title))
        msg.reply_text(
            f"Berhasil mengubah <b>{title}</b> sebagai title yang baru!",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")
        return


@run_async
@bot_admin
@user_admin
@typing_action
def set_sticker(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Kamu tidak memiliki hak untuk mengubah  chat info!")

    if msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            return msg.reply_text(
                "Anda harus membalas sebuah sticker untuk mengatur set stiker obrolan!"
            )
        stkr = msg.reply_to_message.sticker.set_name
        try:
            context.bot.set_chat_sticker_set(chat.id, stkr)
            msg.reply_text(
                f"Berhasil setting sticker grup di {chat.title}!")
        except BadRequest as excp:
            if excp.message == "Participants_too_few":
                return msg.reply_text(
                    "Maaf, karena pembatasan telegram, obrolan harus memiliki minimal 100 anggota sebelum mereka dapat memiliki stiker grup!!"
            )
            msg.reply_text(f"Error! {excp.message}.")
    else:
        msg.reply_text(
            "Anda perlu membalas stiker untuk mengatur set stiker obrolan!")


@run_async
@bot_admin
@user_admin
@typing_action
def set_desc(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_can_changeinfo(chat, user, context.bot.id) is False:
        return msg.reply_text("Anda tidak memiliki hak untuk mengubah chat info!")

    tesc = msg.text.split(None, 1)
    if len(tesc) >= 2:
        desc = tesc[1]
    else:
        return msg.reply_text("Menyetel deskripsi kosong tidak akan menghasilkan apa-apa!")
    try:
        if len(desc) > 255:
            return msg.reply_text(
                "Deskripsi harus kurang dari 255 karakter!")
        context.bot.set_chat_description(chat.id, desc)
        msg.reply_text(
            f"Berhasil memperbarui deskripsi di {chat.title}!")
    except BadRequest as excp:
        msg.reply_text(f"Error! {excp.message}.")


def __chat_settings__(chat_id, user_id):
    return "anda adalah *admin*: `{}`".format(
        dispatcher.bot.get_chat_member(chat_id, user_id).status
        in ("administrator", "creator")
    )


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def pin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args

    user = update.effective_user
    chat = update.effective_chat

    is_group = chat.type != "private" and chat.type != "channel"
    prev_message = update.effective_message.reply_to_message

    if user_can_pin(chat, user, context.bot.id) is False:
        message.reply_text("Kamu tidak memiliki hak untuk menyematkan pesan!")
        return ""

    is_silent = True
    if len(args) >= 1:
        is_silent = not (
            args[0].lower() == "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            bot.pinChatMessage(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
        except BadRequest as excp:
            if excp.message == "Chat_not_modified":
                pass
            else:
                raise
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"BERHASIL MENYEMATKAN PESAN\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@run_async
@bot_admin
@can_pin
@user_admin
@loggable
def unpin(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    user = update.effective_user

    try:
        bot.unpinChatMessage(chat.id)
    except BadRequest as excp:
        if excp.message == "Chat_not_modified":
            pass
        else:
            raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"BERHASIL MENYEMATKAN PESAN\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message


@run_async
@bot_admin
@user_admin
@connection_status
def invite(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat

    if chat.username:
        update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = bot.exportChatInviteLink(chat.id)
            update.effective_message.reply_text(invitelink)
        else:
            update.effective_message.reply_text(
                "Saya tidak memiliki akses ke tautan undangan, coba untuk ubah izin saya!"
            )
    else:
        update.effective_message.reply_text(
            "Saya hanya bisa memberi Anda tautan undangan untuk grup dan channel, maaf!"
        )


@run_async
@connection_status
def adminlist(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    bot = context.bot

    if update.effective_message.chat.type == "private":
        send_message(update.effective_message, "This command only works in Groups.")
        return

    chat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title

    try:
        msg = update.effective_message.reply_text(
            "Mendapatkan group admins...", parse_mode=ParseMode.HTML
        )
    except BadRequest:
        msg = update.effective_message.reply_text(
            "Fetching group admins...", quote=False, parse_mode=ParseMode.HTML
        )

    administrators = bot.getChatAdministrators(chat_id)
    text = "Admins di <b>{}</b>:".format(html.escape(update.effective_chat.title))

    bot_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(
                        f'{user.first_name} ' + ((user.last_name or ""))
                    ),
                )
            )


        if user.is_bot:
            bot_admin_list.append(name)
            administrators.remove(admin)
            continue

        # if user.username:
        #    name = escape_markdown("@" + user.username)
        if status == "creator":
            text += "\n 🤴 Pendiri:"
            text += "\n<code> • </code>{}\n".format(name)

            if custom_title:
                text += f"<code> • {html.escape(custom_title)}</code>\n"

    text += "\n👮 Admins:"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.first_name == "":
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(
                        f'{user.first_name} ' + ((user.last_name or ""))
                    ),
                )
            )

        if status == "administrator":
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list[custom_title] = [name]
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> • </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> • </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0], html.escape(admin_group)
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> • </code>{}".format(admin)
        text += "\n"

    text += "\n🤖 Bots:"
    for each_bot in bot_admin_list:
        text += "\n<code> • </code>{}".format(each_bot)

    try:
        msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return


__help__ = """
 ✻  /admins: daftar admin di chat

 Hanya admin:
 ✻ /pin: diam-diam menyematkan pesan yang dibalas - tambahkan 'keras' atau 'beri tahu' untuk memberikan pemberitahuan kepada pengguna
 ✻ /unpin: melepas pin pesan yang saat ini disematkan
 ✻ /invitelink: mendapat invitelink
 ✻ /promote: mempromosikan pengguna
 ✻ /demote: menurunkan pengguna
 ✻ /title : menetapkan judul khusus untuk admin yang dipromosikan bot
 ✻ /setgtitle : Menyetel judul obrolan baru di grup Anda.
 ✻ /setgpic: Sebagai balasan ke file atau foto untuk mengatur gambar profil grup!
 ✻ /delgpic: Sama seperti di atas tetapi untuk menghapus foto profil grup.
 ✻ /setsticker: Sebagai balasan untuk beberapa stiker untuk ditetapkan sebagai set stiker grup!
 ✻ /setdescription : Mengatur deskripsi obrolan baru dalam grup.
 ✻ /admincache: paksa menyegarkan daftar admin
 ✻ /antispam : Akan mengaktifkan teknologi antispam kami atau mengembalikan pengaturan Anda saat ini.
 ✻ /del: menghapus pesan yang Anda balas
 ✻ /purge: menghapus semua pesan antara ini dan pesan yang dibalas.
 ✻ /purge : menghapus pesan yang dibalas, dan X pesan yang mengikutinya jika membalas pesan.
 ✻ /zombies: menghitung jumlah akun yang dihapus di grup Anda
 ✻ /zombies clean: Hapus akun yang dihapus dari grup..

 Catatan: Obrolan Mode Malam ditutup Secara otomatis pada pukul 12 pagi (IST)
 dan Secara otomatis dibuka pada pukul 6 pagi (IST) Untuk Mencegah Spam Malam.

 ️⚠️ `Baca dari atas`
"""

ADMINLIST_HANDLER = DisableAbleCommandHandler("admins", adminlist)

PIN_HANDLER = CommandHandler("pin", pin, filters=Filters.group)
UNPIN_HANDLER = CommandHandler("unpin", unpin, filters=Filters.group)

INVITE_HANDLER = DisableAbleCommandHandler("invitelink", invite)

PROMOTE_HANDLER = DisableAbleCommandHandler("promote", promote)
DEMOTE_HANDLER = DisableAbleCommandHandler("demote", demote)

SET_TITLE_HANDLER = CommandHandler("title", set_title)
ADMIN_REFRESH_HANDLER = CommandHandler(
    "admincache", refresh_admin, filters=Filters.group
)

CHAT_PIC_HANDLER = CommandHandler("setgpic", setchatpic, filters=Filters.group)
DEL_CHAT_PIC_HANDLER = CommandHandler(
    "delgpic", rmchatpic, filters=Filters.group)
SETCHAT_TITLE_HANDLER = CommandHandler(
    "setgtitle", setchat_title, filters=Filters.group
)
SETSTICKET_HANDLER = CommandHandler(
    "setsticker", set_sticker, filters=Filters.group)
SETDESC_HANDLER = CommandHandler(
    "setdescription",
    set_desc,
    filters=Filters.group)

dispatcher.add_handler(ADMINLIST_HANDLER)
dispatcher.add_handler(PIN_HANDLER)
dispatcher.add_handler(UNPIN_HANDLER)
dispatcher.add_handler(INVITE_HANDLER)
dispatcher.add_handler(PROMOTE_HANDLER)
dispatcher.add_handler(DEMOTE_HANDLER)
dispatcher.add_handler(SET_TITLE_HANDLER)
dispatcher.add_handler(ADMIN_REFRESH_HANDLER)
dispatcher.add_handler(CHAT_PIC_HANDLER)
dispatcher.add_handler(DEL_CHAT_PIC_HANDLER)
dispatcher.add_handler(SETCHAT_TITLE_HANDLER)
dispatcher.add_handler(SETSTICKET_HANDLER)
dispatcher.add_handler(SETDESC_HANDLER)

__mod_name__ = "Admin"
__command_list__ = [
    "adminlist",
    "admins",
    "invitelink",
    "promote",
    "demote",
    "admincache",
]
__handlers__ = [
    ADMINLIST_HANDLER,
    PIN_HANDLER,
    UNPIN_HANDLER,
    INVITE_HANDLER,
    PROMOTE_HANDLER,
    DEMOTE_HANDLER,
    SET_TITLE_HANDLER,
    ADMIN_REFRESH_HANDLER,
]
