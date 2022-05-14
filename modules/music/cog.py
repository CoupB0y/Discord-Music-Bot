
import nextcord
from nextcord import Embed, ButtonStyle
from nextcord import FFmpegPCMAudio
from nextcord.ext import commands
from nextcord.ui import Button, View
from nextcord.utils import get as dget
from youtube_dl import YoutubeDL
from requests import get


class MediaController(View):
    def __init__(self, voice):
        super().__init__(timeout=None)
        self.voice = voice

    @nextcord.ui.button(label='Pause', style=ButtonStyle.primary)
    async def pause(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.voice.is_playing():
            self.voice.pause()

    @nextcord.ui.button(label='Resume', style=ButtonStyle.secondary)
    async def resume(self, button: Button, interaction: nextcord.Interaction):
        if self.voice.is_paused():
            self.voice.resume()
            
    @nextcord.ui.button(label='Mute', style=ButtonStyle.secondary)
    async def mute(self, button: Button, interaction: nextcord.Interaction):
        prev_vol = self.voice.source.volume 
        if self.voice.is_playing():
            if self.voice.source.volume == 0:
                self.voice.source.volume = prev_vol
            else:
                self.voice.source.volume = 0
                         


class Music(commands.Cog, name="Music Player"):
    '''Handles music player commands'''

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.FFMPEG_OPTS = {
            'before_options':
            '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
            }

        self.queues = {}
        self.volume = None
                
    
    async def check_queue(self, ctx, guild_id):
        if self.queues[guild_id]:
            voice = ctx.guild.voice_client
            source = self.queues[guild_id].pop(0)

            song = source['formats'][0]['url']
            thumbnail = source['thumbnails'][0]['url']
            myview = MediaController(voice)
            embed = nextcord.Embed(title="Now Playing", description=source['title'])
            embed.set_image(url=thumbnail)
            await ctx.send(embed=embed,view=myview)
            voice.play(FFmpegPCMAudio(song, **self.FFMPEG_OPTS),
                       after=lambda x: self.check_queue(ctx,
                                                        ctx.message.guild.id))
            voice.source = nextcord.PCMVolumeTransformer(voice.source, volume=self.volume)



    def search(self, query):
        with YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True', 'source_address': '0.0.0.0'}) as ydl:
            try:
                get(query)
            except:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)[
                                        'entries'][0]
            else:
                info = ydl.extract_info(query, download=False)

        return info
    
            

    @commands.command()
    async def play(self, ctx, *, query):
        ''' Searches youtube for the song entered and plays it

        Example: ?play <song>
        '''
        
        video = self.search(query)
        source = video['formats'][0]['url']
        thumbnail = video['thumbnails'][0]['url']
        voice_state = ctx.author.voice
        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        guild_id = ctx.message.guild.id

        try:
            voice_channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send("You need to be in a channel to use this command")

        if voice is not None:
            if not voice.is_connected():
                await voice_channel.connect()
        else:
            await voice_channel.connect()

        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        
        
        if voice.is_playing():
            if guild_id in self.queues:
                self.queues[guild_id].append(video)
            else:
                self.queues[guild_id] = [video]

            await ctx.send(f"Added {video['title']} to queue")
        else:
            myview = MediaController(voice)
            embed = nextcord.Embed(title="Now Playing", description=video['title'])
            embed.set_image(url=thumbnail)
            await ctx.send(embed=embed,view=myview)
            await self.bot.change_presence(status=nextcord.Status.online, activity=nextcord.Game("Songs"))
            voice.play(FFmpegPCMAudio(source, **self.FFMPEG_OPTS),
                       after=lambda x: self.check_queue(ctx,
                                                        ctx.message.guild.id))
            self.volume = 1.0
            voice.source = nextcord.PCMVolumeTransformer(voice.source, volume=self.volume)
            voice.is_playing()


    @commands.command()
    async def volume(self, ctx, volume):
        ''' Adjusts the volume of the bot. Enter Up,Down or a #

        Example: ?volume 50, ?volume down, ?volume up
        '''
        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        volume = volume.lower()
        if volume == "up" or volume == "down":
            if volume == "up":
                if voice.source.volume == 2 or 2 < (voice.source.volume + 0.1):
                    await ctx.send("Volume is already at highest setting")
                else:
                    voice.source.volume = voice.source.volume + 0.1
                    self.volume = voice.source.volume
            else:
                if voice.source.volume == 0 or 0 > (voice.source.volume - 0.1):
                    await ctx.send("Volume is already at lowest setting")
                else:
                    voice.source.volume = voice.source.volume - 0.1
                    self.volume = voice.source.volume
        else:
            new_volume = float(volume)
            if 0 <= new_volume <= 200:
                self.volume = new_volume / 100
                voice.source.volume = self.volume
            else:
                await ctx.channel.send('Please enter a volume between 0 and 200')





    @commands.command()
    async def show(self, ctx):
        ''' Shows the current queue of songs '''

        guild_id = ctx.message.guild.id
        i = 0
        embed = Embed(title="Queue")
        if self.queues and self.queues[guild_id]:
            for item in self.queues[guild_id]:
                num = str(i + 1)
                embed.add_field(name=num, value=item['title'], inline=False)
                i += 1

            await ctx.send(embed=embed)
        else:
            await ctx.send("queue is empty")

    @commands.command()
    async def queue(self, ctx, *, query):
        ''' Adds the entered song to the queue

        Example: ?queue breezeblocks
        '''

        video = self.search(query)

        guild_id = ctx.message.guild.id

        if guild_id in self.queues:
            self.queues[guild_id].append(video)
        else:
            self.queues[guild_id] = [video]

        await ctx.send(f"Added {video['title']} to queue")

    @commands.command()
    async def skip(self, ctx):
        ''' Skips the current song '''

        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        guild_id = ctx.message.guild.id
        voice.pause()
        await ctx.send("Skipped \U000023ED")
        await self.check_queue(ctx, guild_id)

    @commands.command()
    async def clear(self, ctx):
        ''' Clears the queue '''

        guild_id = ctx.message.guild.id
        self.queues[guild_id] = []
        await ctx.send("cleared queue")

    @commands.command()
    async def leave(self, ctx):
        ''' Forces bot to leave voice channel '''

        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected():
            await voice.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.command()
    async def pause(self, ctx):
        ''' Pauses the current song '''

        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send("Paused \U000023F8")
        else:
            await ctx.send("Currently no audio is playing.")

    @commands.command()
    async def resume(self, ctx):
        ''' Resumes the cuurrent song '''

        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send("Resumed \U000025B6")
        else:
            await ctx.send("The audio is not paused.")

    @commands.command()
    async def stop(self, ctx):
        ''' Stops the current song and clears the queue '''

        guild_id = ctx.message.guild.id
        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        voice.stop()
        self.queues[guild_id] = []
        await self.bot.change_presence(status=nextcord.Status.online, activity=nextcord.Game("Songs"))


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
