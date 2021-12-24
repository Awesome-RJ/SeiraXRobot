import importlib
import time
import re
from sys import argv
from typing import Optional

from lunaBot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from lunaBot.modules import ALL_MODULES
from lunaBot.modules.helper_funcs.chat_status import is_user_admin
from lunaBot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

LUNA_IMG = "https://telegra.ph/file/b05fb827470a67aeec05f.jpg"

PM_START_TEXT = """
✪ ʜᴀʟᴏ ɴᴀᴍᴀ sᴀʏᴀ sᴇɪʀᴀ ʀᴏʙᴏᴛ  [🇮🇩](https://telegra.ph/file/9b9e97072f01ce23500ac.jpg)
================================
✪ sᴀʏᴀ ᴀᴅᴀʟᴀʜ ʙᴏᴛ ᴛᴇᴍᴀ ᴀɴɪᴍᴇ ᴜɴᴛᴜᴋ ᴍᴇɴɢᴇʟᴏʟᴀ ɢʀᴜᴘ ᴀɴᴅᴀ ᴅᴇɴɢᴀɴ ᴍᴜᴅᴀʜ!
ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ [sᴇᴛʜ](https://t.me/xyzsethh)
================================
✪ ᴛᴇᴋᴀɴ /help ᴜɴᴛᴜᴋ ᴍᴇʟɪʜᴀᴛ ᴘᴇʀɪɴᴛᴀʜ ʏᴀɴɢ ᴛᴇʀsᴇᴅɪᴀ​.
"""

buttons = [
    [
        InlineKeyboardButton(text="➕ ᴛᴀᴍʙᴀʜ sᴇɪʀᴀ ᴋᴇ ɢʀᴜᴘ ᴀɴᴅᴀ​ ➕", url="http://t.me/SeiraXRobot?startgroup=true"),
    ],
    [
        InlineKeyboardButton(text="ᴛᴇɴᴛᴀɴɢ sᴇɪʀᴀ​ 💜", callback_data="luna_"),
        InlineKeyboardButton(
            text="ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ​", callback_data="luna_basichelp"
        ),
    ],
    [
        
        InlineKeyboardButton(
            text="ʙᴀɴᴛᴜᴀɴ & ᴘᴇʀɪɴᴛᴀʜ​", callback_data="help_back"),
    ],
]


HELP_STRINGS = """
**Main commands:**  [ㅤ](https://telegra.ph/file/9b9e97072f01ce23500ac.jpg)
❂ /start:ᴀɴᴅᴀ ᴍᴜɴɢᴋɪɴ sᴜᴅᴀʜ ᴍᴇɴɢɢᴜɴᴀᴋᴀɴ.
❂ /help: ᴍᴇɴɢɪʀɪᴍ ᴘᴇsᴀɴ ɪɴɪ; sᴀʏᴀ ᴀᴋᴀɴ ʙᴇʀᴄᴇʀɪᴛᴀ ʟᴇʙɪʜ ʙᴀɴʏᴀᴋ ᴛᴇɴᴛᴀɴɢ ᴅɪʀɪ sᴀʏᴀ​.

Semua perintah dapat digunakan dengan / atau !.
Jika Anda ingin melaporkan bug atau membutuhkan bantuan dalam menyiapkan Seira, hubungi kami di sini @SeiraSupport"""


DONATE_STRING = """Hehe, senang mendengar Anda ingin menyumbang!
 [klick disini](https://t.me/xyzsethh) ❤️
"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("lunaBot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
           LUNA_IMG, caption= "I'm awake already!\n<b>Haven't sleep since:</b> <code>{}</code>".format(
               uptime
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ", url="t.me/seirasupport")]]
            ),
        )
        
def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


@run_async
def luna_about_callback(update, context):
    query = update.callback_query
    if query.data == "luna_":
        query.message.edit_text(
            text="""Halo lagi!  Saya adalah bot manajemen grup lengkap yang dibuat untuk membantu Anda mengelola grup dengan mudah.\n
                    \nSaya bisa melakukan banyak hal, beberapa di antaranya adalah:
                    \n• Batasi pengguna yang membanjiri obrolan Anda menggunakan modul anti-banjir saya.
                    \n• Lindungi grup Anda dengan sistem Antispam yang canggih dan praktis.
                    \n• Sapa pengguna dengan media + teks dan tombol, dengan format yang tepat.
                    \n• Simpan catatan dan filter dengan pemformatan dan markup balasan yang tepat..\n
                    \nPenting!:Saya perlu dipromosikan dengan izin admin yang tepat agar berfungsi dengan baik.\n
                    \nPeriksa Panduan Penyiapan untuk mempelajari cara menyiapkan bot dan bantuan untuk mempelajari lebih lanjut.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="ᴘᴀɴᴅᴜᴀɴ ᴘᴇɴɢᴀᴛᴜʀᴀɴ​", callback_data="luna_aselole"
                        ),
                        InlineKeyboardButton(
                            text="sʏᴀʀᴀᴛ & ᴋᴇᴛᴇɴᴛᴜᴀɴ​", callback_data="luna_puqi"
                        ),
                    ],
                    [InlineKeyboardButton(text="ʙᴀᴄᴋ", callback_data="luna_back")],
                ]
            ),
        )
    elif query.data == "luna_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

    elif query.data == "luna_basichelp":
        query.message.edit_text(
            text=f"**──「 Penggunaan Dasar 」──**"
            f"\n\n1.) Pertama, tambahkan saya ke grup anda.\n"
            f"2.) kemudian promosikan saya sebagai admin dan berikan semua izin kecuali admin anonim.\n"
            f"3.) setelah mempromosikan saya, ketik /reload di grup untuk memperbarui daftar admin.\n"
            f"4.) Tambahkan @seiramusicassisten ke grup anda.\n"
            f"5.) nyalakan obrolan video terlebih dahulu sebelum mulai memutar musik.\n"
            f"\n📌 jika userbot(@seiramusikassisten) tidak join voice chat, pastikan voice chat aktif,.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="📗 ᴅᴀsᴀʀ​ ", callback_data="luna_admin"),
                    InlineKeyboardButton(text="📘 ᴠɪᴅᴇᴏ​ ", callback_data="luna_notes"),
                 ],
                 [
                    InlineKeyboardButton(text="📙 ᴀᴅᴍɪɴ​", callback_data="luna_support"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_back"),
                 
                 ]
                ]
            ),
        )
    elif query.data == "luna_admin":
        query.message.edit_text(
            text=f"**──「 Penggunaan Dasar 」──**"
            f"\n/play (nama lagu) - memutar musik atau dari youtube"
            f"\n/play (balas ke pesan audio) - memutar musik dari file audio."
            f"\n/playlist - mainkan musik playlistmu atau playlist grup."
            f"\n/lyrics (nama lagu) - mencari lirik lagu."
            f"\n/song (nama lagu ) - mendownload lagu dari youtube.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="luna_basichelp")]]
            ),
        )

    elif query.data == "luna_notes":
        query.message.edit_text(
            text=f"──「Video player 」──\n\n"
            f"\n/vplay  (nama lagu / link YouTube) – play video stream via YouTube."
            f"\n/vpause - Untuk pause musik/video yang sedang di putar (hanya admin)."
            f"\n/vstop atau /end - untuk memberhentikan video yang sedang di putar."
            f"\n/bhaks - check musik/video stream ping status."
            f"\n/skip - untuk melompat ke video selanjutnya.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="luna_basichelp")]]
            ),
        )
    elif query.data == "luna_support":
        query.message.edit_text(
            text=f"──「 Penggunaan Admin 」──\n"
            f"\n/play - (nama lagu) / balas ke audio file "
            f"\n/pause - pause musik yang sedang berputar"
            f"\n/resume - melanjutkan musik yang Ter pause"
            f"\n/skip - melewati ke lagu selanjutnya"
            f"\n/end - stop musik yang sedang berputar",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_basichelp"),
                 
                 ]
                ]
            ),
        )
    elif query.data == "luna_credit":
        query.message.edit_text(
            text=f"<b> `Cʀᴇᴅɪᴛ Fᴏʀ Seira Dᴇᴠ's` </b>\n"
            f"\nHᴇʀᴇ Sᴏᴍᴇ Dᴇᴠᴇʟᴏᴘᴇʀs Hᴇʟᴘɪɴɢ Iɴ Mᴀᴋɪɴɢ Tʜᴇ Seira",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Alina", url="https://t.me/rizexx"),
                    InlineKeyboardButton(text="Nao", url="https://t.me/xgothboi"),
                 ],
                 [
                    InlineKeyboardButton(text="Yui", url="https://t.me/Badboyanim"),
                    InlineKeyboardButton(text="Luna", url="https://t.me/tdrki_1"),
                    InlineKeyboardButton(text="Seira", url="https//t.me/xyzparvez"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_basichelp"),
                 
                 ]
                ]
            ),
        )

    elif query.data == "luna_aselole":
        query.message.edit_text(
            text=f"｢ Penggunaan Dasar 」\n"
                 f"\nAnda dapat menambahkan saya ke grup Anda dengan mengeklik tautan ini dan memilih obrolan.\n"
                 f"\nBaca Izin Admin dan Anti-spam untuk info dasar.\n"
                 f"\nBaca Panduan Penyiapan Terperinci untuk mempelajari tentang penyiapan bot secara mendetail. (Disarankan)\n"
                 f"\nJika Anda membutuhkan bantuan dengan petunjuk lebih lanjut, silakan bertanya di @seirasupport.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Perizinan Admin", callback_data="luna_asu"),
                    InlineKeyboardButton(text="Anti Spam", callback_data="luna_asi"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="luna_"),
                 
                 ]
                ]
            ),
        )

    elif query.data == "luna_asu":
        query.message.edit_text(
            text=f"｢ Perizinan Admin 」\n"
                     f"\nUntuk menghindari perlambatan, Seira menyimpan hak admin untuk setiap pengguna. Cache ini berlangsung sekitar 10 menit; ini dapat berubah di masa mendatang. Ini berarti bahwa jika Anda mempromosikan pengguna secara manual (tanpa menggunakan perintah /promote), Seira akan  cari tahu saja ~10 menit kemudian.\n"
                     f"\nJika Anda ingin segera memperbaruinya, Anda dapat menggunakan perintah /admincache atau /reload, yang akan memaksa Seira untuk memeriksa lagi siapa adminnya dan izinnya\n"
                     f"\nJika Anda mendapatkan pesan yang mengatakan:\nAnda harus menjadi administrator obrolan ini untuk melakukan tindakan ini!\n"
                     f"\nIni tidak ada hubungannya dengan hak Seira; ini semua tentang izin ANDA sebagai admin. Seira menghormati izin admin; jika Anda tidak memiliki izin Larangan Pengguna sebagai admin telegram, Anda 
