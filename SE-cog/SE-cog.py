import discord
from discord.ext import commands
from __main__ import send_cmd_help
from random import randint
try:  # check if BeautifulSoup4 is installed
    from bs4 import BeautifulSoup
    soupAvailable = True
except:
    soupAvailable = False
import aiohttp

urlSEnews = "http://spaceengine.org/news/"
urlSEversion = "http://spaceengine.org/download/spaceengine"
urlSEimage = "http://spaceengine.org/universe/"
categoryImage = ['planets-and-moons', 'landscapes', 'deep-space', 'real-celestial-object', 'space-ships', 'easy-to-explore', 'modding-abilities', 'gallery']
categoryImageNameFR = ['planètes et lunes', 'paysages', 'espace profond', 'objets céleste réels', 'vaisseaux spatiaux', 'outils de prise en main', 'démonstration de modage', 'gallerie']


class SEcog:
    """A Space Engine related cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, name='SE', aliases=['Space-Engine', 'se', 'SpaceEngine', 'space-engine', 'spaceengine'])
    async def _SEcog(self, context):
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_SEcog.command(pass_context=True, name='news', aliases=['SEN', 'SEn', 'sen', 'SENews', 'SENEWS', 'senews', 'SEnews', 'n'])
    async def _SEnews(self):
        '''
        Get the last news of Space Engine
        '''

        async with aiohttp.get(urlSEnews) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
        try:
            dateMonthNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_image').find(class_='post_date_standard_holder').find(class_='post_date_month').get_text()
            dateDayNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_image').find(class_='post_date_standard_holder').find(class_='post_date_day').get_text()
            dateYearNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_image').find(class_='post_date_standard_holder').find(class_='post_date_year').get_text()
            dateNews1 = dateDayNews1 + ' ' + dateMonthNews1 + ' ' + dateYearNews1
            nomNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_text').find('h2').find('a').get_text()
            soulignementNews1 = "="*(len(nomNews1)+len(dateNews1)+3)
            contenuNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_text').find(class_='post_excerpt').get_text()
            lienNews1 = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='post').find(class_='post_text').find('h2').find('a')['href']
            await self.bot.say("```markdown\n" + dateNews1 + ' - ' + nomNews1 + "\n" + soulignementNews1 + "\n" + contenuNews1 + "\n[Lien vers la news](" + lienNews1 + ")\n```")
        except:
            await self.bot.say("L'information n'existe pas: la page " + urlSEnews + " a été supprimée ou son architecture modifiée.")

    @_SEcog.command(pass_context=True, name='version', aliases=['v', 'SEV', 'sev', 'V', 'ver'])
    async def _SEversion(self):
        '''
        Get the actual version of Space Engine
        '''

        async with aiohttp.get(urlSEversion) as response:
            soupObject = BeautifulSoup(await response.text(), "html.parser")
        try:
            versionName = soupObject.find(class_='wrapper').find(class_='content').find(class_='container').find(class_='clearfix').find(class_='wpb_wrapper').find(class_='tab-title').find(class_='tab-title-inner').get_text()
            # versionName contient 'SpaceEngine <numero de version>'
            version = versionName[12:]
            await self.bot.say("La version actuelle de Space Engine est la " + version)
        except:
            await self.bot.say("L'information n'existe pas: la page " + urlSEversion + " a été supprimée ou son architecture modifiée.")

    @_SEcog.command(name='image', aliases=['i', 'I', 'IMAGE', 'picture', 'images', 'pictures'])
    async def _SEimage(self):
        '''
        Get a random image of Space Engine (or a selected one if arg passed)
        Categories list: planètes et lunes, paysages, espace profond, objets céleste réels, vaisseaux spatiaux, outils de prise en main, démonstration de modage, gallerie
        '''
        if not context:
            i = randint(0, len(categoryImage)-1)
            context = categoryImageNameFR[i]
        if context in categoryImageNameFR:
            index = categoryImageNameFR.index(context)
            category = categoryImage[index]
            urlSEimageFull = urlSEimage + category
            async with aiohttp.get(urlSEimageFull) as response:
                soupObject = BeautifulSoup(await response.text(), "html.parser")
            try:
                images = soupObject.find(class_='wrapper').find(class_='content').find(class_='portfolio_gallery').find_all('a')['href']
                j = randint(0, len(images))
                image = images[j]
                if j==0:
                    num = 'ière'
                else:
                    num = 'ième'
                await self.bot.say("Voici la " + j+1 + num + " image de la catégorie " + context + ": " + image)
            except:
                await self.bot.say("L'information n'existe pas: la page " + urlSEimageFull + " a été supprimée ou son architecture modifiée.")
        else:
            await self.bot.say("La catégorie " + context + " n'est pas valide")


def setup(bot):
    if soupAvailable:
        bot.add_cog(SEcog(bot))
    else:
        raise RuntimeError("You need to run `pip3 install beautifulsoup4`")
