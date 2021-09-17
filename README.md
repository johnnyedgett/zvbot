# This bot is for learning purposes only. 

known bugs.
* bot does not send a message to channel when changing songs (can be fixed by getting setting a channel object)
* is not set up to handle concurrency well (aka if a bunch of people do `add at the same time i have no fucking clue what will happen)
* needs top be restricted via permissions to a specific channel or it will monitor for commands in all channels (not necessarily a bug, but theres no support built in the bot to do things different)
* does not auto delete mp3s after song is done.
* does not shut down cleanly

to run
* create a discord app & bot https://discord.com/developers/applications (this is free)
* install python: https://www.python.org/downloads/
* install ffmpeg (*REQUIRED*): https://www.ffmpeg.org/download.html
* download this repository as a ZIP and extract somewhere on your computer
* create a new file ".env"
* add a single line to the file: DISCORD_TOKEN=[xxxxxxxxxxxx] <-- this is your discord token.
* open command line and navigate to the install location where main.py is located
* run the following: `pip install discord requests dotenv youtube_dl`
* run the app: `python main.py`
* invite your bot to the channel following https://discordjs.guide/preparations/adding-your-bot-to-servers.html#bot-invite-links