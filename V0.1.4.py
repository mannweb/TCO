

from datetime import datetime
from multiprocessing import Pool, Process
import asyncio
import copy
import discord
import json
import logging
import os
import platform
import random
import shutil
import threading
import time
import yaml
import youtube_dl

import _updatemedia as updatemedia


client = discord.Client()


@client.event
async def on_ready():

    logging.info("The Chosen One is initialising!")
    logging.debug(f"TCO V{__version__} attempting to initialise...")

    # Status setup:
    try:
        activity = discord.Game(name=f"{status} | V{__version__} | {commandkey}help")
        await client.change_presence(status=discord.Status.online, activity=activity)
        logging.debug("Successfully set bot status.")

    except Exception as e:
        logging.debug(f"Bot status failed to initialise. Error: {e}")

    # Load users:
    logging.debug("Loading users...")

    try:
        with open("UserData.json", "r") as stream:
            jsondata = stream.read()

        userdata = json.loads(jsondata)
        for usr in userdata:
            profile = user(usr, userdata[usr], 2)
            logging.info(f"Loaded user: {profile.name}.")

        logging.debug("Successfully loaded all existing users.")

    except Exception as e:
        logging.error(f"Failed to load existing users. Error: {e}")

    # Load media:
    logging.debug("Loading media data...")

    try:
        mediaroot = os.path.join(os.getcwd(), "Media")
        updatemedia.update(mediaroot)

    except Exception as e:
        logging.error(f"Failed to load media data. Some commands will not work. Error: {e}")


@client.event
async def on_message(ctx):

    # Return if a bot sent the message:
    if ctx.author.bot:
        return

    # Check if the bot has administrator privileges:
    admin, channeltype = True, "server"
    try:
        if not ctx.channel.permissions_for(ctx.channel.guild.me).administrator: 
            admin = False
    except Exception as e:
        channeltype = "direct"
    
    # Reconstruct username for author of message:
    username = ctx.author.name + "#" + ctx.author.discriminator

    # Find the user that sent the command:
    existinguser = False
    for usr in user.users:
        if usr.name == username:
            currentuser, existinguser = usr, True

    # If the user is not an existing user, create user profile:
    if not existinguser:
        logging.info(f"Initialising new user: {username}")
        currentuser = user(username, ctx.author.id, 1)
        user.rewritedata()

    # Set textchannel and voicechannel data for current user: 
    currentuser.textchannel = ctx.channel
    currentuser.voicechannel = None

    # Establish the guild the user is currently typing in:
    if channeltype == "server":
        currentuser.guild = ctx.guild
        
        # Establish if the user is in a voice channel:
        if ctx.author.voice:
            currentuser.voicechannel = ctx.author.voice.channel           

    # Prevents python from automatically formatting strings, and breaking urls:
    message = ctx.content.encode("unicode-escape").decode("utf-8")
    
    # Check if the message was a command:
    if message.startswith(commandkey):
        
        # Separate the command from the arguments, and remove command key:
        command, *args = message.split(" ")
        command = command[len(commandkey):].lower()

        # Process a known command:
        await processcommand(command, args, currentuser, admin)


async def processcommand(command, args, currentuser, admin):

    try:
        
        # Info Commands:
        # Display help menu (must be at the top):
        if command in commanddict["help"]:
            await currentuser.displayhelp()

        # Display patchnotes:
        elif command in commanddict["patchnotes"]:
            await currentuser.displaypatchnotes(versions=args)

        # Display roadmap:
        elif command in commanddict["roadmap"]:
            await currentuser.displayroadmap()


        # Dev Commands:
        elif command in commanddict["dev"]:
            await currentuser.makedev(args)

        elif command in commanddict["versiondata"]:
            await currentuser.getversiondata()

        # List the currently stored users:
        elif command in commanddict["idusers"]:
            await currentuser.idusers(specificusers=args)

        # Rewrite the UserData.yml file with current user class instances:
        elif command in commanddict["rwuserdata"]:
            await currentuser.triggerudrw()


        # Alias Commands:
        # Display aliases:
        elif command in commanddict["aliases"]:
            await currentuser.displayaliases(args)


        # Chat Commands:
        # Ship two usernames:
        elif command in commanddict["echo"]:
            await currentuser.echomessage(args)

        elif command in commanddict["ship"]:
            await currentuser.shipusers(args)

        elif command in commanddict["createpoll"]:
            await currentuser.pollcreate(args)

        elif command in commanddict["addpoll"]:
            await currentuser.polladd()
        

        # Video Commands:
        # Queue video or display queue:
        elif command in commanddict["queue"]:
            if not args:
                await currentuser.videoqueuedisplay()
            else:
                if await currentuser.summonbot(passive=True):
                    await currentuser.videoqueueadd(args)

        # Play queued video:
        elif command in commanddict["play"]:
            if await currentuser.summonbot(passive=True):
                if not args: 
                    await currentuser.videoplay()
                else:
                    await currentuser.videoqueueadd(args)
                    await currentuser.videoplay()

        # Pause current video:
        elif command in commanddict["pause"]:
            await currentuser.videopause()

        # Resume current video:
        elif command in commanddict["resume"]:
            await currentuser.videoresume()

        # Skip current video:
        elif command in commanddict["skip"]:
            await currentuser.videostop(stype="skip")
            await currentuser.videoplay()

        # Stop current video:
        elif command in commanddict["stop"]:
            await currentuser.videostop()

        # Summon to current voice channel:
        elif command in commanddict["summon"]:
            await currentuser.summonbot()

        # Leave current voice channel:
        elif command in commanddict["leave"]:
            await currentuser.kickbot()

        elif command in commanddict["clear"]:
            await currentuser.videoqueueclear(args)


        # Image Commands:
        # Send an image:
        elif command in commanddict["cat"]:
            await currentuser.requestimage("cat")
        elif command in commanddict["dog"]:
            await currentuser.requestimage("dog")
        elif command in commanddict["bird"]:
            await currentuser.requestimage("bird")
        elif command in commanddict["bread"]:
            await currentuser.requestimage("bread")


        # Photography Commands:
        # Post a photo:
        elif command in commanddict["photo"]:
            await currentuser.requestphoto("all")
        elif command in commanddict["sunset"]:
            await currentuser.requestphoto("sunset")
        elif command in commanddict["leeds"]:
            await currentuser.requestphoto("leeds")
        elif command in commanddict["space"]:
            await currentuser.requestphoto("space")


        # Custom Commands:
        # Create a custom command:
        elif command in commanddict["createcc"]:
            await currentuser.cccreate(args)

        # Remove a custom command:
        elif command in commanddict["removecc"]:
            await currentuser.ccremove(args)

        # Process a custom command:
        elif command in currentuser.customcommands:
            await processcommand(currentuser.customcommands[command][0], currentuser.customcommands[command][1:], currentuser, admin)


        # Other input:
        else:
            await currentuser.textchannel.send("Command Not Recognised!")


    except Exception as e:
        await currentuser.textchannel.send("Command Failed!")
        logging.error(f"A user command caused the program to error out. Error: {e}")


class user:

    users = []
    
    def __init__(self, User, UD, source):
        
        # source:
        # 0 - no source
        # 1 - message
        # 2 - file

        self.name = User
        
        self.dev = False
        self.nickname = None

        self.textchannel = None
        self.voicechannel = None

        self.customcommands = {}

        if source == 0:
            None

        elif source == 1:
            self.id = UD

        elif source == 2:
            self.id = UD['id']
            self.dev = UD['dev']
            self.nickname = UD['nickname']
            self.customcommands = UD['customcommands']

        user.users.append(self)

    def converttodict(self):
        UD = {'id': self.id, 'nickname': self.nickname, 'dev': self.dev, 'customcommands': self.customcommands}
        return UD

    def rewritedata():

        # Take a backup of the file before trying to rewrite it:
        shutil.copyfile("UserData.json", "UserData - Backup.json")

        # Try to rewrite the user data:
        try:
            userdata = {}
            for usr in user.users:
                userdata[usr.name] = usr.converttodict()
            jsondata = json.dumps(userdata, indent=4, sort_keys=False)
            with open("UserData.json", "w") as stream:
                stream.write(jsondata)
            os.remove("UserData - Backup.json")

        # If rewrite fails, restore from backup.
        except Exception as e:
            logging.error(f"Attempting to rewrite user data threw an error. Error: {e}")
            try:
                os.remove("UserData.json")
                os.rename("UserData - Backup.json", "UserData.json")
                logging.error(f"Backup restored successfully.")
            except Exception as ee:
                logging.error(f"Backup may not have restored correctly. Error: {ee}")

    async def cccreate(self, args):
        self.customcommands[args[0]] = args[1:]
        await self.textchannel.send(f"Created new custom command: ^{args[0]} <-> ^{' '.join(args[1:])}")

    async def ccremove(self, args):
        await self.textchannel.send(f"Removing custom command: ^{args[0]} <-> ^{' '.join(self.customcommands[args[0]])}")
        del self.customcommands[args[0]]

    async def displayaliases(self, args):
        if not args:
            await self.textchannel.send(f"Specify a command to see its aliases.")
        for cmd in args:
            if cmd in commanddict:
                await self.textchannel.send(f"The aliases for '{cmd}' are {commanddict[cmd]}")
            else:
                await self.textchannel.send(f"'{cmd}' is not a recognised command.")

    async def displayhelp(self):
        website = "[" + "our website" + "]" + "(" + "http://bitly.com/98K8eH" + ")"
        desc = f"A list of command, and guide to get you started using them. For more details, check out {website}!"
        embed = discord.Embed(title="Help Menu", description=desc, color=0x000000)
        with open("Notes.yml", "r") as Notes:
            note = yaml.full_load(Notes)["help"]
        for field in note:
            embed.add_field(name=field, value=note[field], inline=False)
        await self.textchannel.send(embed=embed)

    async def displaypatchnotes(self, versions=False):
        with open("Notes.yml", "r") as Notes:
            note = yaml.full_load(Notes)["patchnotes"]
        if not versions:
            embed = discord.Embed(title=__version__, description=f"Changes made under version {__version__}", color=0x0000ff)
            for item in note[__version__]:
                embed.add_field(name=item, value=note[__version__][item], inline=False)
            await self.textchannel.send(embed=embed)
        elif versions[0] == "all":
            for version in note:
                embed = discord.Embed(title=version, description=f"Changes made under version {version}", color=0x0000ff)
                for item in note[version]:
                    embed.add_field(name=item, value=note[version][item], inline=False)
                await self.textchannel.send(embed=embed)
        else:
            for version in versions:
                embed = discord.Embed(title=version, description=f"Changes made under version {version}", color=0x0000ff)
                for item in note[version]:
                    embed.add_field(name=item, value=note[version][item], inline=False)
                await self.textchannel.send(embed=embed)

    async def displayroadmap(self):
        desc = ("Planned future updates and features.")
        embed = discord.Embed(title="Roadmap", description=desc, color=0x000000)
        with open("Notes.yml", "r") as Notes:
            note = yaml.full_load(Notes)["roadmap"]
        for field in note:
            embed.add_field(name=field, value=note[field], inline=False)
        await self.textchannel.send(embed=embed)

    async def echomessage(self, args):
        message = " ".join(args)
        await self.textchannel.send(message)

    async def getversiondata(self):
        if not self.dev:
            await self.textchannel.send(f"Debug commands are reserved for use by developers.")
            return
        version = __version__
        lastpatch = "unknown"
        uptime = "unknown"
        await self.textchannel.send(f"Current version: {version} \nLast patch: {lastpatch} \nUptime: {uptime}")

    async def idusers(self, specificusers):
        if not self.dev:
            await self.textchannel.send(f"Debug commands are reserved for use by developers.")
            return
        if not specificusers:
            await self.textchannel.send(f"These are the users currently registered by the bot:")
            for usr in user.users:
                await self.textchannel.send(f"{usr.name}: \n\t\t\t\tID: {usr.id} \n\t\t\t\tDev: {usr.dev}")
        else:
            for specificuser in specificusers:
                for usr in user.users:
                    found = False
                    if usr.name == specificuser:
                        found = True
                        await self.textchannel.send(f"{usr.name}: \n\t\t\t\tID: {usr.id} \n\t\t\t\tDev: {usr.dev}")
                if not found:
                    await self.textchannel.send(f"User: {specificuser} has no profile.")

    async def kickbot(self):
        if self.guild in video.voiceclients:
            if video.voiceclients[self.guild][0].channel != self.voicechannel:
                await self.textchannel.send("The Chosen One is not in your voice channel.")
            else:
                await video.voiceclients[self.guild][0].disconnect()
                del video.voiceclients[self.guild]
                await self.textchannel.send("Disconnected from voice channel.")

    async def makedev(self, args):
        if self.dev:
            await self.textchannel.send("You are already a developer.")
        else:
            if not args:
                await self.textchannel.send("To set yourself as a developer, please follow the command with the admin password.")
            else:
                if args[0] == devpw:
                    self.dev = True
                    await self.textchannel.send("Developer mode enabled.")
                    user.rewritedata()
                else:
                    await self.textchannel.send("Incorrect password.")

    async def polladd(self):
        message = (await self.textchannel.history(limit=2).flatten())[1]
        await message.add_reaction('\U0001F44D')
        await message.add_reaction('\U0001F44E')

    async def pollcreate(self, args):
        poll = ""
        for i in args:
            poll += i
            poll += " "
        message = await self.textchannel.send(poll)
        await message.add_reaction('\U0001F44D')
        await message.add_reaction('\U0001F44E')

    async def requestimage(self, variant):
        if variant == "cat":
            filepath, caption = os.path.join(os.getcwd(), 'Media', 'Images', 'Cats'), "Cat!"
        elif variant == "dog":
            filepath, caption = os.path.join(os.getcwd(), 'Media', 'Images', 'Dogs'), "Doggo!"
        elif variant == "bird":
            filepath, caption = os.path.join(os.getcwd(), 'Media', 'Images', 'Birds'), "Birb!"
        elif variant == "bread":
            filepath, caption = os.path.join(os.getcwd(), 'Media', 'Images', 'Bread'), "Bread!"

        datafile = os.path.join(filepath, "_data.json")
        with open(datafile, "r") as stream:
            jsondata = stream.read()
        data = json.loads(jsondata)
        if not len(data) == 0:
            img = random.choice(list(data.keys()))
            imgfile = os.path.join(filepath, img)
            await self.textchannel.send(caption, file=discord.File(imgfile))
        else: await self.textchannel.send("There are currently no images of this type.")

    async def requestphoto(self, variant):
        if variant == "all":
            filepath = os.path.join(os.getcwd(), 'Media', 'Photography', 'All')
        elif variant == "sunset":
            filepath = os.path.join(os.getcwd(), 'Media', 'Photography', 'Sunsets')
        elif variant == "leeds":
            filepath = os.path.join(os.getcwd(), 'Media', 'Photography', 'Leeds')
        elif variant == "space":
            filepath = os.path.join(os.getcwd(), 'Media', 'Photography', 'Space')

        datafile = os.path.join(filepath, "_data.json")
        with open(datafile, "r") as stream:
            jsondata = stream.read()
        data = json.loads(jsondata)
        if not len(data) == 0:
            img = random.choice(list(data.keys()))
            imgfile = os.path.join(filepath, img)
            await self.textchannel.send(file=discord.File(imgfile))
        else: await self.textchannel.send("There are no photos of this type.")

    async def senddm(self, message):
        recipient = await client.fetch_user(self.id)
        await recipient.send(message)

    async def shipusers(self, users):
        usernames = []
        for u in users:
            usernames.append((await client.fetch_user(u[3:-1])).name)
        shipname = str(usernames[0][:len(usernames[0])//2] + usernames[1][len(usernames[1])//2:])
        await self.textchannel.send(f"Your shipname is: {shipname}!")

    async def summonbot(self, passive=False):
        if self.voicechannel == None:
            await self.textchannel.send("You need to join a voice channel first.")
            return False
        elif self.guild in video.voiceclients:
            if video.voiceclients[self.guild][0].channel == self.voicechannel and not passive:
                await self.textchannel.send("The Chosen One is already in your voice channel.")
                return True
            else:
                await video.voiceclients[self.guild][0].move_to(self.voicechannel)
                return True
        else:
            vc = await self.voicechannel.connect()
            video.voiceclients[self.guild] = [vc, [], False, 0]
            return True

    async def triggerudrw(self):
        if not self.dev:
            await self.textchannel.send(f"Debug commands are reserved for use by developers.")
            return
        user.rewritedata()
        await self.textchannel.send(f"Successfully rewrote user data.")
            
    async def videopause(self):
        if video.voiceclients[self.guild][0].is_playing():
            video.voiceclients[self.guild][2] = False
            video.voiceclients[self.guild][0].pause()
            await self.textchannel.send("Video paused!")
        else:
            await self.textchannel.send("No video is currently playing!")
               
    async def videoplay(self):
        if len(video.voiceclients[self.guild][1]) == 0:
            await self.textchannel.send("There are no queued videos!")
            return
        if video.voiceclients[self.guild][0].is_playing() == False:
            await video.voiceclients[self.guild][1][0].play(self.guild)
        
    async def videoqueueadd(self, args):
        searchterm = " ".join(args)
        newentity = video(searchterm, self)
        if not newentity.isplaylist:
            await self.textchannel.send(embed=newentity.embedqueued)

    async def videoqueueclear(self, args):
        await video.clear(self, args)

    async def videoqueuedisplay(self):
        if self.guild not in video.voiceclients or len(video.voiceclients[self.guild][1]) == 0:
            await self.textchannel.send("You have not queued any videos.")
        else:
            for vid in video.voiceclients[self.guild][1]:
                await self.textchannel.send(embed=vid.embedqueued)
        
    async def videoqueueremove(self, term):
        video.voiceclients[self.guild].delete(term)
        await self.textchannel.send("Video has been removed.")

    async def videoresume(self):
        if video.voiceclients[self.guild][0].is_paused():
            video.voiceclients[self.guild][0].resume()
            video.voiceclients[self.guild][2] = True
            await self.textchannel.send("Video resumed!")
        else:
            await self.textchannel.send("No video is currently paused!")

    async def videostop(self, stype="stop"):
        if video.voiceclients[self.guild][0].is_playing():
            video.voiceclients[self.guild][2] = False
            video.voiceclients[self.guild][0].stop()
            if stype == "stop":
                await self.textchannel.send("Video stopped!")
            elif stype == "skip":
                await self.textchannel.send("Video skipped!")
        else:
            await self.textchannel.send("No video is currently playing!")


class video:

    voiceclients = {
    # Name of guild: Voice client, video list, active, inactivity
    ##    "server1" : ("client1", [1, 2, 3], False, 0),
    ##    "server2" : ("client2", [1, 2, 3], False, 0),
    ##    "server3" : ("client3", [1, 2, 3], False, 0)
    }

    def __init__(self, searchterm, usr, queueloc=False):
        
        self.isplaylist = False

        # Determine whether the searchterm is a url:
        if "https://" in searchterm:
                
            self.url = searchterm 
            
            # If so, is it a playlist:
            if "playlist?list=" in searchterm:

                self.isplaylist = True

                with youtube_dl.YoutubeDL(ytdlplformatoptions) as ytdlpl:
                    data = ytdlpl.extract_info(self.url, download=False, process=False)

                videos = [vid for vid in data["entries"]]

                for v in videos:

                    if v["_type"] == "url":

                        url = f"https://www.youtube.com/watch?v={v['id']}"
                        video(url, usr)

                return

            # If not a playlist, look for video:
            else:
                with youtube_dl.YoutubeDL(ytdlvformatoptions) as ytdlv:

                    data = ytdlv.extract_info(self.url, download=False)
                
        # If not, use youtube api to find video:
        else:

            with youtube_dl.YoutubeDL(ytdlvformatoptions) as ytdlv:

                searchresults = ytdlv.extract_info(f"ytsearch:'{searchterm}'", download=False)
                data = searchresults['entries'][0]
                self.url = data["url"]

        # Use youtube api to aquire video data:
        self.audiodata = data["url"]
        self.id = data["id"]
        self.title = data["title"]
        self.volume = 0.5
        mins = str(data["duration"] // 60)
        secs = str(data["duration"] % 60)
        if len(secs) == 1: secs = "0" + secs
        self.length = mins + ":" + secs
        self.channel = None
        self.viewcount = None
        self.textchannel = usr.textchannel
        self.embedqueued = self.genembed(1, usr)
        self.embedplaying = self.genembed(2, usr)

        # Append video object to video list:
        if not queueloc:
            video.voiceclients[usr.guild][1].append(self)
        else:
            video.voiceclients[usr.guild][1].insert(queueloc, self)

    def genembed(self, embedtype, user):
        desc = f"[{self.title}]({self.url})\n`[0:00 / {self.length}]`"
        thumbnail = f"https://img.youtube.com/vi/{self.id}/default.jpg"
        mention = f"<@!{user.id}>"
        if embedtype == 0:
            embed = None
        elif embedtype == 1: # For queued video:
            embed = discord.Embed(title="Queued", description=desc, color=0x000000)
            embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Requested by:", value=mention, inline=False)
        elif embedtype == 2: # For played video:
            embed = discord.Embed(title="Now Playing", description=desc, color=0x051094)
            embed.set_thumbnail(url=thumbnail)
            embed.add_field(name="Requested by:", value=mention, inline=False)
        return embed

    async def play(self, guild):
        player = discord.FFmpegPCMAudio(self.audiodata, executable=ffmpegfile, before_options=ffmpegformatoptions["before_options"], options=ffmpegformatoptions["options"])
        await self.textchannel.send(embed=self.embedplaying)
        video.voiceclients[guild][0].play(player)
        video.voiceclients[guild][2] = True
        video.voiceclients[guild][1].pop(0)

    async def clear(usr, id):
        if not id:
            video.voiceclients[usr.guild][1] = []
            await usr.textchannel.send("Cleared video queue.")
        else:
            video.voiceclients[usr.guild][1].pop(int(id[0])-1)
            await usr.textchannel.send("Removed video.")


def checkvcs(playtimer, timeoutcounter):
    dellist = []
    for vc in video.voiceclients:
        # Check whether the bot has been manually disconnected:
        if not video.voiceclients[vc][0].is_connected():
            dellist.append(vc)
        # Check whether a new video needs to be played:
        elif video.voiceclients[vc][2] and not video.voiceclients[vc][0].is_playing():
            if len(video.voiceclients[vc][1]) != 0:
                try:
                    asyncio.run_coroutine_threadsafe(video.voiceclients[vc][1][0].play(vc), loop=client.loop)
                except Exception as e:
                    logging.error(f"Failed to autoplay video. Error: {e}")
            else:
                video.voiceclients[vc][2] = False
        # Check whether the bot should disconnect due to inactivity:
        elif not video.voiceclients[vc][0].is_playing():
            video.voiceclients[vc][3] += 1
            if video.voiceclients[vc][3] > 180:
                try:
                    asyncio.run_coroutine_threadsafe(video.voiceclients[vc][0].disconnect(), loop=client.loop)
                except Exception as e:
                    logging.error(f"Failed to automatically disconnect from voice. Error: {e}")
    for vc in dellist:
        try:
            del video.voiceclients[vc]
        except Exception as e:
            logging.error(f"Voiceclient garbage collection failed. Error: {e}")
    if not playtimer.is_set():
        threading.Timer(1, checkvcs, [playtimer, timeoutcounter]).start()


def main():

    loglevel = logging.INFO
    logformat = '[%(levelname)s] %(asctime)s - %(message)s'
    logging.basicConfig(level=loglevel, format=logformat)

    playtimer = threading.Event()
    threading.Timer(1, checkvcs, [playtimer, 0]).start()

    client.run(clientsecret)


if __name__ == "__main__":

    # Windows setup:
    if platform.system() == "Windows":
        ffmpegfile = "ffmpeg.exe"

    # Linux setup:
    elif platform.system() == "Linux":
        ffmpegfile = "ffmpeg"

    # Import all the config data from yml file:
    with open('FormatOptions.yml', 'r') as formatdata:
    
        formatoptions = yaml.full_load(formatdata)
    
    clientsecret = formatoptions["clientsecret"]

    ytdlvformatoptions = formatoptions["ytdlv"]
    ytdlplformatoptions = formatoptions["ytdlpl"]
    ffmpegformatoptions = formatoptions["ffmpeg"]

    commandkey = formatoptions["commandkey"]
    commanddict = formatoptions["commanddict"]
    
    __version__ = formatoptions["version"]

    status = formatoptions["status"]

    devpw = formatoptions["adminpassword"]

    # Run program:
    main()



    
