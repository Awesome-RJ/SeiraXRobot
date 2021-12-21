import random
from lunaBot.events import register
from lunaBot.events import telethn

APAKAH_STRING = ["Haha Mimpi !", 
                 "Tidak Mungkin Besti😅", 
                 "Semoga yaa,pasti terwujud aamiin✨", 
                 "Heleh...Ngimpi !",
                 "YUK BISA YUK , SEMANGAT 💜",
                 "NGGA MUNGKIN..HAHAHA",
                 "Ya Nda Tau Kok Tanya Seira",
                 "Pala bapak kau Kempes Xixixixi",
                 "Mungkin..",
                 "Coba Tanya Admin 🤭"
                ]


@register(pattern="^/seandainya ?(.*)")
async def apakah(event):
    quew = event.pattern_match.group(1)
    if not quew:
        await event.reply('seandainya apa boss?')
        return
    await event.reply(random.choice(APAKAH_STRING))
