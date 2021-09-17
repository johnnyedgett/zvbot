import discord
import os
import requests
from dotenv import load_dotenv
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL
import queue
import threading
import uuid

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

def process_command(message):
    message.channel.send('test')

class Music():
    uuid: str
    name: str
    link: str
    requester: str

    def __init__(self, uuid, name, link, requester):
        self.uuid = uuid
        self.name = name
        self.link = link
        self.requester = requester

class MusicPlayer():
    active_song = None
    song_queue = queue.Queue()
    discord_client = None
    voice_client = None
    is_playing = False

    def checkStatusEveryFiveSeconds(self, f_stop):
        if not self.voice_client == None:
            print(f'is_playing(): {self.voice_client.is_playing()}')
            if not self.voice_client.is_playing():
                if not self.song_queue.empty():
                    try:
                        song = self.get_song()
                        self.play_internal(song)
                    except ValueError as err:
                        print(f'Unable to play next song due to: {err}')

            self.is_playing = False
            self.active_song = None

        if not f_stop.is_set():
            threading.Timer(5, self.checkStatusEveryFiveSeconds, [f_stop]).start()

    def __init__(self, discord_client):
        self.discord_client = discord_client
        f_stop = threading.Event()
        self.checkStatusEveryFiveSeconds(f_stop)
        print(f'Music Player has been initialized')

    async def createVoiceConnection(self, voice_channel):
        self.voice_client = await voice_channel.connect()

    async def destroyVoiceConnection(self, message):
        await self.voice_client.disconnect()
        await message.channel.send(f'Disconnected!')

    async def addToQueue(self, message, link, requester):
        if self.voice_client is None or not self.voice_client.is_connected():
            await message.channel.send(f'Please add me to a voice channel first~!')
            return

        song = Music(uuid.uuid4(), "Placeholder", link, requester)
        self.song_queue.put(song)
        await message.channel.send(f'[DEBUG] Added `{link}` ')

    def get_song(self):
        song = self.song_queue.get()

        YDL_OPTIONS = {
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'{song.uuid}.%(ext)s',
        }

        if "youtube.com" in song.link or "youtu.be" in song.link:
            with YoutubeDL(YDL_OPTIONS) as ydl:
                print(f'{song.link}')
                ydl.download([song.link])

        # If not, check if you url is an mp3 and download it
        elif "mp3" in song.link:
            print(f'Downling {song.uuid}')
            downloaded = requests.get(song.link)
            with open(f'{song.uuid}.mp3', 'wb') as f:
                f.write(downloaded.content)  

        else:
            raise ValueError(f'{song.link} does not appear to be a valid song link.')

        return song

    async def play(self, message):
        if not self.voice_client.is_connected():
            await message.channel.send(f'I am not currently in a voice channel. Please join a voice channel and use \`join.')
            return
        
        try:
            song = self.get_song()
        except ValueError as err:
            await message.channel.send(f'Error: {err}' )

        self.play_internal(song)

    def play_internal(self, song):
        if not self.voice_client.is_playing():
            self.is_playing = True
            self.active_song = song
            self.voice_client.play(FFmpegPCMAudio(f"{song.uuid}.mp3"))

    async def pause(self, message):
        if not self.voice_client.is_connected():
            await message.channel.send(f'I am not currently in a voice channel. Please join a voice channel and use \`join.')
            return

        if not self.active_song == None:
            self.voice_client.pause()
            await message.channel.send(f'Paused')
        else:
            await message.channel.send(f'There is no currently active song')

    async def resume(self, message):
        if not self.voice_client.is_connected():
            await message.channel.send(f'I am not currently in a voice channel. Please join a voice channel and use \`join.')
            return

        if not self.active_song == None:
            self.voice_client.resume()
            await message.channel.send(f'Resuming')
        else:
            await message.channel.send(f'There is no currently active song')

    async def skip(self, message):
        if self.voice_client == None or not self.voice_client.is_connected():
            await message.channel.send(f'I am not currently in a voice channel. Please join a voice channel and use \`join.')
            return

        if not self.active_song == None:
            self.voice_client.stop()
            self.is_playing = False
            self.active_song = None
            await message.channel.send(f'Skipped the currently playing song')
        else:
            await message.channel.send(f'There is no currently active song')

class CommandProcessor():
    # Initialize the music player and begin polling every 60 seconds
    discord_client = None
    music_player = None
    voice_connection = None

    def __init__(self, discord_client):
        self.discord_client = discord_client
        self.music_player = MusicPlayer(discord_client)

    async def processor(self, message):
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

        try:
            self.voice_connection = await self.music_player.createVoiceConnection(message.author.voice.channel)
            await message.channel.send(f'Joined {message.author.voice.channel.name} on behalf of {message.author.nick}')
        except Exception as err:
            await message.channel.send(f'Unable to connect to {message.author.voice.channel.name} due to: {err}')

    async def com_disconnect(self,  message, arguments):
        await self.music_player.destroyVoiceConnection(message)

    async def com_pause(self, message, arguments):
        await self.music_player.pause(message)

    async def com_resume(self, message, arguments):
        await self.music_player.resume(message)

    async def com_skip(self, message, arguments):
        await self.music_player.skip(message)

    async def com_add(self, message, arguments):
        await self.music_player.addToQueue(message, arguments[0], message.author.nick)

class CustomClient(discord.Client):
    commandProcessor = None

    async def on_ready(self):
        self.commandProcessor = CommandProcessor(self)
        print(f'Initialized Custom Discord Client')
        for guild in client.guilds:
            print(f'{client.user} is in guild: {guild}')

        print(f'{client.user} connected')

    async def on_message(self, message):
        if message.author == client.user:
            return

        if message.content.startswith("`"):
            await self.commandProcessor.processor(message)

client = CustomClient()
client.run(TOKEN)