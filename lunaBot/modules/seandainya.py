import random
from lunaBot.events import register
from lunaBot.events import telethn

APAKAH_STRING = ["Haha Mimpi !", 
                 "Tidak Mungkin Besti😅", 
                 "Iyaa,pasti terwujud aamiin✨", 
                 "Heleh...Ngimpi !", 
                 "70 % bisa lah..", 
                 "YUK BISA YUK , SEMANGAT 💜",
                 "NGGA MUNGKIN..HAHAHA",
                 "Ya Nda Tau Kok Tanya Seira",
                 "Pala bapak kau Kempes Xixixixi",
                 "Coba lagi",
                 "Coba Tanya Admin 🤭"
                 ]


@register(pattern="^/seandainya ?(.*)")
async def apakah(event):
    quew = event.pattern_match.group(1)
    if not quew:
        await event.reply('seandainya tidak terdeteksi, coba lagi 😐')
        return
    await event.reply(random.choice(APAKAH_STRING))
