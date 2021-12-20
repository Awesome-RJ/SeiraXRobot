import re
import os

from telethon import events, Button
from telethon import __version__ as tlhver
from pyrogram import __version__ as pyrover
from lunaBot.events import register as MEMEK
from lunaBot import telethn as tbot

PHOTO = "https://telegra.ph/file/1d196e1a45ac2e20178b7.jpg"

@MEMEK(pattern=("/mhelp"))
async def awake(event):
  tai = event.sender.first_name
   LUNA = "** Panduan Dasar \n\n"
   LUNA += "• /vplay (judul lagu) — Untuk memutar video streaming yang Anda minta melalui YouTube** \n"
   LUNA += "• /play (judul lagu/video) – Untuk memutar musik dari YouTube  \n"
   LUNA += "• /vplaylist - menampilkan daftar video stream  dalam antrian \n"\n"
   LUNA += "** Admin CMD \n\n"
   LUNA += "• /pause - Untuk Menjeda playback Lagu** \n"
   LUNA += "• /resume - Untuk melanjutkan playback Lagu yang dijeda \n"
   LUNA += "• /skip - Untuk Melewati pemutaran lagu ke Lagu berikutnya \n"
   LUNA += "• /end - Untuk Menghentikan playback Lagu \n"
   LUNA += "• /musicplayer on - mengaktifkan music/video player di group anda \n"
   LUNA += "• /musicplayer off - menonaktifkan music/video player di group anda \n"

  BUTTON = [[Button.url("☎️ Support", "https://t.me/SeiraSupport"), Button.url("📡 Updates", "https://t.me/sethproject")]]
  await tbot.send_file(event.chat_id, PHOTO, caption=LUNA,  buttons=BUTTON)
