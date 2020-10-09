import json
import os, sys, inspect

"""
Allow to import from this directory
"""
cmd_folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile( inspect.currentframe() ))[0]))
if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)

import utils as ut

import discord
from redbot.core import commands, checks, bot, utils

cmd_json_file = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"storage.json")))

class Rulemanager:

    def __init__(self):
        self.rules=[]
        self.storage=[]

    async def check(self, guild, event, data):
        for rule in self.rules:
            if rule.guild==guild:
                if await rule.getEvent()==event:
                    await rule.execute(data)

    async def add(self, rule):
        self.rules.append(rule)

    async def setStorage(self, rulesdata):
        self.storage=rulesdata

    async def getStorage(self):
        return self.storage

    async def applyStorage(self, bot):
        self.rules=[]
        for rule in self.storage:
            if rule["event"]["type"] in ut.events:
                args=await ut.checkArgs(bot, rule["event"]["args"], ut.events[rule["event"]["type"]]["args"])
                event=ut.events[rule["event"]["type"]]["class"](*tuple(args))
            else:
                raise Exception(rule["event"]["type"]+" is not not an event")
            conditions=[]
            for condition in rule["conditions"]:
                if condition["type"] in ut.conditions:
                    args=await ut.checkArgs(bot, condition["args"], ut.conditions[condition["type"]]["args"])
                    conditions.append(ut.conditions[condition["type"]]["class"](*tuple(args)))
                else:
                    raise Exception(condition["type"]+" is not a condition")
            effects=[]
            for effect in rule["effects"]:
                if effect["type"] in ut.effects:
                    args=await ut.checkArgs(bot, effect["args"], ut.effects[effect["type"]]["args"])
                    effects.append(ut.effects[effect["type"]]["class"](*tuple(args)))
                else:
                    raise Exception(condition["type"]+" is not an effect")
            guild=bot.get_guild(int(rule["guild"]))
            rule=Rule(guild, event, conditions, effects)
            await self.add(rule)

    async def saveStorage(self):
        storage=await self.getStorage()
        print(storage)
        json_data=json.dumps({
            "rules": storage
        })
        with open(cmd_json_file, "w") as json_file:
            json_file.write(json_data)

    async def loadStorage(self):
        with open(cmd_json_file, "r") as json_file:
            await self.setStorage(json.load(json_file)["rules"])

class Rule:

    def __init__(self, guild, event, conditions, effects):
        self.guild=guild
        self.event=event
        self.conditions=conditions
        self.effects=effects

    async def getEvent(self):
        return await self.event.get()

    async def execute(self, data):
       data=await self.event.wait(data)
       if data:
           for condition in self.conditions:
               if not await condition.check(data):
                    return False
           for effect in self.effects:
                await effect.execute(data)
           return True
       return False

"""
Main script
"""

class Rules(commands.Cog):
    """Rules cog, a cog which help to create specific rules for many purpose like auto-moderation"""

    def __init__(self, bot):
        super().__init__()
        self.bot=bot
        self.RuleManager=Rulemanager()

    async def init(self):
        await self.RuleManager.loadStorage()
        await self.RuleManager.applyStorage(self.bot)

    async def red_get_data_for_user(*, user_id):
        """No data stored"""
        return

    async def red_delete_data_for_user(*, requester, user_id):
        """No data stored"""
        return

    @commands.command()
    @checks.admin()
    async def listrule(self, ctx):
        """List rules of this server"""
        rules=await self.RuleManager.getStorage()
        if len(rules)!=0:
            messages=[]
            count=0
            for rule in rules:
                if rule["guild"]==ctx.message.guild.id:
                    message=await ut.ruleToString(rule, count)
                    messages.append(message)
                    count+=1
            pages=[]
            for page in utils.chat_formatting.pagify("\n\n".join(messages), ["\n\n"], page_length=1000):
                pages.append(page)
            await utils.menus.menu(ctx, pages, {
                "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}": utils.menus.prev_page,
                "\N{CROSS MARK}": utils.menus.close_menu,
                "\N{BLACK RIGHTWARDS ARROW}\N{VARIATION SELECTOR-16}": utils.menus.next_page,
            })
        else:
            await ctx.send("No defined rules in this server")

    @commands.command()
    @checks.admin()
    async def addrule(self, ctx):
        """Add a rule for this guild"""
        async def askargs(dictionnary):
            args=[]
            for arg in dictionnary:
                message="Enter a "+arg["type"]+" value for "+arg["name"]+"\n"
                message+=utils.chat_formatting.inline(arg["description"])
                await ctx.send(message)
                value=await self.bot.wait_for("message", check=utils.predicates.MessagePredicate.same_context(ctx))
                value=await ut.validArg(value.content, arg["type"])
                args.append(value)
            return args
        async def askthing(dictionnary, name):
            thing={}
            str_thing=""
            str_things=""
            message=utils.chat_formatting.question("For which "+name+" ?\n")
            for element in dictionnary:
                str_things+=dictionnary[element]["name"]+"\n"
            message+=utils.chat_formatting.inline(str_things)
            while str_thing not in dictionnary:
                await ctx.send(message)
                value=await self.bot.wait_for("message", check=utils.predicates.MessagePredicate.same_context(ctx))
                str_thing=value.content
                if str_thing not in dictionnary:
                    await ctx.send(str_thing+" is not a "+name)
            thing["type"]=str_thing
            thing["args"]=await askargs(dictionnary[str_thing]["args"])
            return thing

        event=await askthing(ut.events, "event")

        number=None
        while not number is int:
            message=utils.chat_formatting.question("With how many conditions ?\n")
            await ctx.send(message)
            number=await self.bot.wait_for("message", check=utils.predicates.MessagePredicate.same_context(ctx))
            try:
                number=int(number.content)
            except ValueError:
                ctx.send("Please, enter an integer")

        conditions=[]
        for i in range(number):
            condition=await askthing(ut.conditions, "condition")
            conditions.append(condition)

        number=None
        while not number is int:
            message=utils.chat_formatting.question("With how many effects ?\n")
            await ctx.send(message)
            number=await self.bot.wait_for("message", check=utils.predicates.MessagePredicate.same_context(ctx))
            try:
                number=int(number.content)
            except ValueError:
                ctx.send("Please, enter an integer")

        effects=[]
        for i in range(number):
           effect=await askthing(ut.effects, "effect")
           effects.append(effect)

        rulesdata=await self.RuleManager.getStorage()
        rulesdata.append({
            "guild": ctx.guild.id,
            "event": event,
            "conditions": conditions,
            "effects": effects
        })
        await self.RuleManager.setStorage(rulesdata)
        await self.RuleManager.saveStorage()
        await self.RuleManager.applyStorage(self.bot)

        await ctx.send("Well done!")

    @commands.command()
    @checks.admin()
    async def deleterule(self, ctx):
        """Delete a rule"""
        args=await ut.parseArgs(ctx)
        if len(args)==0:
            await ctx.send("Which rule do you want to delete?")
            arg=await self.bot.wait_for("message", check=utils.predicates.MessagePredicate.same_context(ctx))
            args.append(arg.content)

        while not args[0] is int:
            try:
                number=int(args[0])
            except ValueError:
                ctx.send("Please, enter an integer")

        rules=await self.RuleManager.getStorage()
        if len(rules)!=0:
            count, real_count=0, 0
            for rule in rules:
                if count==number:
                    break
                if rule["guild"]==ctx.message.guild.id:
                    count+=1
                real_count+=1
            if count!=number:
                await ctx.send("Cannot delete a rule that doesn't exist")
            else:
                str_rule=await ut.ruleToString(rules[real_count], count)
                message=await ctx.send("Are you sure you want to delete this rule ?\n"+str_rule)
                pred=utils.predicates.MessagePredicate.yes_or_no(ctx)
                await self.bot.wait_for("message", check=pred)
                await message.delete()
                result=pred.result
                if result:
                    del rules[real_count]
                    await self.RuleManager.setStorage(rules)
                    await self.RuleManager.applyStorage(self.bot)
                    await ctx.send("Rule deleted")
                else:
                    await ctx.send("No rule deleted")
        else:
            await ctx.send("No defined rules in this server")

    @commands.command()
    @checks.is_owner()
    async def inittest(self, ctx):
        """init for testing purpose"""
        await self.init()


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id==self.bot.user.id:
            return
        await self.RuleManager.check(message.guild, "message", message)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        await self.RuleManager.check(after.guild, "member update", [before, after])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.RuleManager.check(member.guild, "join", member)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.RuleManager.check(member.guild, "remove", member)

    @commands.Cog.listener()
    async def on_connect(self):
        await self.init()
        await self.RuleManager.check(None, "connect", self.bot)
