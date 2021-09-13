import discord
import os
from discord.channel import VoiceChannel
import requests
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
import queue

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')

def process_command(message):
    message.channel.send('test')

class Music():
    name: str
    link: str
    requester: str

    def __init__(self, name, link, requester):
        self.name = name
        self.link = link
        self.requester = requester

class MusicPlayer():
    active_song = None
    song_queue = queue.Queue()
    voice_client = None
    is_playing = False

    YDL_OPTIONS = {
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song.%(ext)s',
    }

    async def player(self):
        print(f'Music player is not yet implemented')

    async def createVoiceConnection(self, voice_channel):
        self.voice_client = await voice_channel.connect()

    async def destroyVoiceConnection(self, message):
        # if self.voice_client == None or not self.voice_client.is_connected:
        #     await message.channel.send(f'Not currently connected to a voice channel')
        #     return

        await self.voice_client.disconnect()
        await message.channel.send(f'Disconnected!')

    async def addToQueue(self, message, link, requester):
        # if self.voice_client == None or not self.voice_client.is_connected:
        #     await message.channel.send(f'Not currently connected to a voice channel')
        #     return

        song = Music("Placeholder", link, requester)
        self.song_queue.put(song)
        await message.channel.send(f'[DEBUG] Added <<Placeholder>> to the queue')
        # If a song is queued and no song is playing it, go ahead and start playing
        if not self.is_playing:
            await message.channel.send(f'[DEBUG] Playing <<Placeholder>> from the queue')
            await self.play(message)

    async def play(self, message):
        # time for magic
        # First, Check if you url contains 'youtube' - if it does grab it 
        song = self.song_queue.get()

        if "youtube.com" in song.link or "youtu.be" in song.link:
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                print(f'{song.link}')
                ydl.download([song.link])

        # If not, check if you url is an mp3 and download it
        elif "mp3" in song.link:
            downloaded = requests.get(song.link)
            with open('song.mp3', 'wb') as f:
                f.write(downloaded.content)

        else:
            await message.channel.send(f'For some reason {song.link} does not appear to be a valid link.')

        if not self.voice_client.is_playing():
            self.is_playing = True
            self.active_song = song
            self.voice_client.play(FFmpegPCMAudio("song.mp3"))
            self.voice_client.is_playing()
            await message.channel.send(f'Now playing: {self.song_queue[0].link}')

    async def pause(self, message):
        if not self.active_song == None:
            self.voice_client.pause()
            await message.channel.send(f'Paused')
        else:
            await message.channel.send(f'There is no currently active song')

    async def resume(self, message):
        if not self.active_song == None:
            self.voice_client.resume()
            await message.channel.send(f'Resuming')
        else:
            await message.channel.send(f'There is no currently active song')

    async def skip(self, message):
        if not self.active_song == None:
            self.voice_client.stop()
            self.is_playing = False
            self.active_song = None
            await message.channel.send(f'Skipped the currently playing song')
        else:
            await message.channel.send(f'There is no currently active song')

music_player = MusicPlayer()

class CommandProcessor():
    async def processor(self, client, message):
        message_text = message.content.split()

        command = message_text[0]
        arguments = []

        for index in range(1,len(message_text)):
            arguments.append(message_text[index])

        method_name = 'com_' + str(command[1:])
        method = getattr(self, method_name, lambda message, arguments: message.channel.send(f'That was an unknown command: {command[1:]} with arguments {arguments}'))

        await method(message, arguments)

    async def com_help(self, message, arguments): 
        await message.channel.send('Available Commands: \`help, \`join, \`disconnect, \`add, \`pause, \`resume, \`skip')

    async def com_join(self, message, arguments):
        if message.author.voice == None:
            await message.channel.send(f'User {message.author.nick} is not currently in a voice channel.')
            return

        await message.channel.send(f'Joining {message.author.voice.channel.name} on behalf of {message.author.nick}')
        await music_player.createVoiceConnection(message.author.voice.channel)

    async def com_disconnect(self,  message, arguments):
        await music_player.destroyVoiceConnection(message)

    async def com_pause(self, message, arguments):
        await music_player.pause(message)

    async def com_resume(self, message, arguments):
        await music_player.resume(message)

    async def com_skip(self, message, arguments):
        await music_player.skip(message)

    async def com_add(self, message, arguments):
        # if(len(arguments) < 2):
        #     await message.channel.send('Usage: `add [Song Link]')
        #     return
        await music_player.addToQueue(message, arguments[0], message.author.nick)
        # await message.channel.send('TODO')

commandProcessor = CommandProcessor()

class CustomClient(discord.Client):
    async def on_ready(self):
        for guild in client.guilds:
            print(f'{client.user} is in guild: {guild}')

        print(f'{client.user} connected')

    async def on_message(self, message):
        if message.author == client.user:
            return

        # print(f'{message}')
        # print(f'{message.content}')
        # print(f'{message.author.voice}')

        if message.content.startswith("`"):
            await commandProcessor.processor(self, message)

client = CustomClient()
client.run(TOKEN)