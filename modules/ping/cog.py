from nextcord.ext import commands


class Ping(commands.Cog):
    ''' Receives ping commands '''

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx: commands.Context):
        ''' Checks for response from bot '''
        
        await ctx.send(f"Pong! {round(self.bot.latency * 1000, 1)} ms")


def setup(bot: commands.Bot):
    bot.add_cog(Ping(bot))
