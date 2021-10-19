from nextcord import Embed
from nextcord import FFmpegPCMAudio
from nextcord.ext import commands
from nextcord.utils import get as dget
from youtube_dl import YoutubeDL
from requests import get


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

    def check_queue(self, ctx, guild_id):
        if self.queues[guild_id]:
            voice = ctx.guild.voice_client
            source = self.queues[guild_id].pop(0)

            source = source['formats'][0]['url']
            voice.play(FFmpegPCMAudio(source, **self.FFMPEG_OPTS),
                       after=lambda x: self.check_queue(ctx,
                                                        ctx.message.guild.id))

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

        Example: ?play country roads
        '''

        video = self.search(query)
        source = video['formats'][0]['url']
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
            await ctx.send(f"Now playing {video['title']}.")
            voice.play(FFmpegPCMAudio(source, **self.FFMPEG_OPTS),
                       after=lambda x: self.check_queue(ctx,
                                                        ctx.message.guild.id))
            voice.is_playing()

    @commands.command()
    async def volume(self, ctx, value: int):
        """Sets the volume of the currently playing song."""

        pass

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
        self.check_queue(ctx, guild_id)

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
            await ctx.send("Paused")
        else:
            await ctx.send("Currently no audio is playing.")

    @commands.command()
    async def resume(self, ctx):
        ''' Resumes the cuurrent song '''

        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send("Resumed")
        else:
            await ctx.send("The audio is not paused.")

    @commands.command()
    async def stop(self, ctx):
        ''' Stops the current song and clears the queue '''

        guild_id = ctx.message.guild.id
        voice = dget(self.bot.voice_clients, guild=ctx.guild)
        voice.stop()
        self.queues[guild_id] = []


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
