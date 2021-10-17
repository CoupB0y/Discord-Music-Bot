import random
from nextcord.ext import commands


class Random(commands.Cog):
    '''Returns random results'''


    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @commands.command()
    async def roll(self, ctx: commands.Context, dice: str):
        ''' Rolls a given number of dice in the form #d#

        Example: ?roll 3d10
        '''
        try:
            rolls = ""
            total = 0
            amount, die = dice.split("d")
            for _ in range(int(amount)):
                roll = random.randint(1,int(die))
                total += roll
                rolls += f"{roll} "
            await ctx.send(f"Rolls: {rolls}\nSum: {total}")
        except ValueError:
            await ctx.send("Dice must be in format #d# (example: 2d6)")




def setup(bot: commands.Bot):
    bot.add_cog(Random(bot))
