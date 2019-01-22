import discord
from discord.ext import commands
try:  # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False
import aiohttp

urlSEnews = "http://spaceengine.org/news/"


class SEcog:
    """A Space Engine related cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def SEnews(self):
        """Get the last news of Space Engine"""

        async with aiohttp.get(urlSEnews) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
        try:
            nomNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_text').find('h2').find('a').get_text()
            soulignementNews1 = "="*len(nomNews1)
            contenuNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_text').find(class_='post_excerpt').get_text()
            lienNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_text').find('h2').find('a')['href']
            await self.bot.say("```markdown\n" + nomNews1 + "\n" + soulignementNews1 + "\n" + contenuNews1 + "\n[Lien vers la news](" + lienNews1 + ")\n```")
        except:
            await self.bot.say("L'information n'existe pas: la page " + urlSEnews + " a été supprimée ou son architecture modifiée.")


def setup(bot):
    if soupAvailable:
        bot.add_cog(SEcog(bot))
    else:
        raise RuntimeError("You need to run `pip3 install beautifulsoup4`")
