import time
import re
import discord
import datetime
import ast
import copy

async def checkArg(value, type_):
    if value=="None":
        return None
    else:
        if type_=="str":
            return str(value)
        elif type_=="int":
            return int(value)
        elif type_=="bool":
            return bool(value)
        elif type_=="list":
            if type(value) is str:
                return value.split()
            elif type(value) is list:
                return value
            else:
                raise Exception(value.__class__.__name__+" cannot be converted to a list")
        elif type_=="dict":
            if type(value) is str:
                value=ast.literal_eval(value)
                return value
            elif type(value) is dict:
                return value
            else:
                raise Exception(value.__class__.__name__+" cannot be converted to a dict")
        else:
            raise Exception(type_+" is an unknown type")

async def validArg(str_value, type_):
    value=await checkArg(str_value, type_)
    if value==None:
        return "None"
    return value

async def checkArgs(bot, args, dictionary):
    return_args=[bot]
    if len(dictionary)!=len(args):
        raise Exception("Mismatch between the number of arguments expected ("+str(len(dictionary))+") and those given ("+str(len(args))+")")
    for i in range(len(dictionary)):
        arg=await checkArg(args[i], dictionary[i]["type"])
        return_args.append(arg)
    return return_args

async def ruleToString(rule, count):
    string="---------- RULE "+str(count)+" ----------\n"
    string+=await eventToString(rule["event"])
    string+=await conditionsToString(rule["conditions"])
    string+=await effectsToString(rule["effects"])
    string+="--------------------------"
    return string

async def eventToString(event):
    string="If "+events[event["type"]]["description"]+"\n"
    string+=await argsToString(event["args"], events[event["type"]]["args"])
    return string

async def conditionsToString(conditions_):
    string=""
    for i in range(len(conditions_)):
        string+="If "+conditions[conditions_[i]["type"]]["description"]+"\n"
        string+=await argsToString(conditions_[i]["args"], conditions[conditions_[i]["type"]]["args"])
    return string

async def effectsToString(effects_):
    string=""
    for i in range(len(effects_)):
        string+="Then "+effects[effects_[i]["type"]]["description"]+"\n"
        string+=await argsToString(effects_[i]["args"], effects[effects_[i]["type"]]["args"])
    return string

async def argsToString(args, dictionary):
    string=""
    for i in range(len(args)):
        string+="With ```"+dictionary[i]["name"]+" = "+str(args[i])+"``` ("+dictionary[i]["description"]+")\n"
    return string

async def parseArgs(ctx):
    len_prefix=len(ctx.prefix)+len(ctx.command.name)
    content=ctx.message.content[len_prefix:]
    return content.split()

async def formatVar(string, data):
    return string.format(**{"data": data})

"""
Things definition

A thing is an event or a condition or an effect
"""

"""
Event which can be triggered
"""

class MessageSentBy:
    """Trigger when a certain message was sent in a certain amount of time. The condition will apply for the last message"""

    def __init__(self, bot, number, delay, channels):
        self.number=number
        self.delay=delay
        if channels==None:
            self.channels=[]
        else:
            self.channels=list(map(int, channels))

    async def process(self, times, message):
        timenow=time.time()
        times.append(timenow)
        while len(times)>1 and timenow-times[0]>self.delay:
            if timenow-times[0]>self.delay:
                times.pop(0)
        if len(times)>=self.number:
            times.pop(0)
            return times, message
        return times, False

    async def checkChannel(self, message):
        if len(self.channels)==0:
            return True
        return message.channel.id in self.channels

    async def get(self):
        return "message"

class MessageSentByAll(MessageSentBy):
    """The message can be sent by anyone to be counted"""

    def __init__(self, bot, number, delay, channels):
        super(self.__class__, self).__init__(bot, number, delay, channels)
        self.times=[]

    async def wait(self, message):
        check=await self.checkChannel(message)
        if not check:
            return check
        self.times, message=await self.process(self.times, message)
        return message

class MessageSentBySame(MessageSentBy):
    """The message has to be sent by the same member"""

    def __init__(self, bot, number, delay, channels):
        super(self.__class__, self).__init__(bot, number, delay, channels)
        self.times={}

    async def wait(self, message):
        check=await self.checkChannel(message)
        if not check:
            return check
        if not str(message.author.id) in self.times:
            self.times[str(message.author.id)]=[]
        self.times[str(message.author.id)], message=await self.process(self.times[str(message.author.id)], message)
        return message

class MessageSentSimple:
    """Trigger when a single message is send"""

    def __init__(self, bot, channels, authors, roles):
        if channels==None:
            self.channels=[]
        else:
            self.channels=list(map(int, channels))
        if authors==None:
            self.authors=[]
        else:
            self.authors=list(map(int, authors))
        if roles==None:
            self.roles=[]
        else:
            self.roles=list(map(int, roles))

    async def wait(self, message):
        if len(self.channels)!=0:
            if message.channel.id not in self.channels:
                return False
        if len(self.authors)!=0:
            if message.author.id not in self.authors:
                return False
        if len(self.roles)!=0:
            if not any(check in self.roles for check in [role.id for role in message.author.roles]):
                return False
        return message

    async def get(self):
        return "message"

class Join:
    """Trigger when someone join the server"""

    def __init__(self, bot):
        pass

    async def wait(self, member):
        return member

    async def get(sef):
        return "join"


"""
Condition to apply the effects
"""

class HasUsername:
    """If the member who sent the message or join or did any update has a certain pattern in the name"""

    def __init__(self, bot, regex):
        self.regex=regex

    async def check(self, data):
        if isinstance(data, discord.message.Message):
            name=data.author.name
        elif isinstance(data, dicord.Member):
            name=data.name
        if re.search(self.regex, name):
            return True
        return False

class Contains:
    """Can only be used for messaged event, check if the message contains a pattern"""

    def __init__(self, bot, regex):
        self.regex=regex

    async def check(self, message):
        if re.search(self.regex, message.content):
            return True
        return False

class InDenyList:
    """If the member name or the message content contains a substring in a denylist"""

    def __init__(self, bot, denylist):
        self.denylist=denylist

    async def check(self, data):
        if isinstance(data, discord.message.Message):
            haystack=data.content
        elif isinstance(data, discord.Member):
            haystack=data.name
        else:
            raise Exception("Cannot use a denylist with this type of content")
        for denyword in self.denylist:
            if re.search(r"(?:^|\W)"+denyword+r"(?:$|\W)", haystack)!=None:
                return True
        return False

class NotInAllowList:
    """If the member name or the message content does not contain a substring in a allowlist"""

    def __init__(self, bot, allowlist):
        self.allowlist=allowlist

    async def check(self, data):
        if isinstance(data, discord.message.Message):
            haystack=data.content
        elif isinstance(data, discord.Member):
            haystack=data.name
        else:
            raise Exception("Cannot use a denylist with this type of content")
        for allowword in self.allowlist:
            if re.search(r"(?:^|\W)"+allowword+r"(?:$|\W)", haystack)!=None:
                return False
        return True

"""
The effect taken
"""

class SendMessage:
    """Send a message, can contain |variable| and can be used without channel if the event triggered within a channel (message)"""

    def __init__(self, bot,  message, channel=None):
        self.message=message
        self.channel=bot.get_channel(channel)

    async def process(self, data):
        channel=self.channel
        message=await formatVar(self.message, data)
        if isinstance(data, discord.message.Message):
            channel=data.channel
        if self.channel==None:
            return await channel.send(message)
        return await self.channel.send(message)

class SendMessageEternal(SendMessage):

    async def execute(data):
        await self.process(self, data)

class SendMessageTimed(SendMessage):

    def __init__(self, bot,  message, channel=None, delay=3):
        super(self.__class__, self).__init__(bot, message, channel)
        self.delay=delay

    async def execute(self, data):
        message=await self.process(data)
        await message.delete(delay=self.delay)

class SendEmbedMessage:
    """Send an embed message, can contain |variable| and can be used without channel if the event triggered within a channel (message)"""

    def __init__(self, bot, dict_embed, channel=None):
        self.bot=bot
        self.channel=channel
        self.dict_embed=dict_embed

    async def process(self, data):
        dict_embed=copy.deepcopy(self.dict_embed)
        if "title" in dict_embed:
            if len(dict_embed["title"])>256:
                dict_embed["title"]=dict_embed["title"][:253]+"..."
            dict_embed["title"]=await formatVar(dict_embed["title"], data)
        if "description" in dict_embed:
            if len(dict_embed["description"])>2048:
                dict_embed["description"]=dict_embed["description"][:2045]+"..."
            dict_embed["description"]=await formatVar(dict_embed["description"], data)
        if "colour" in dict_embed:
            dict_embed["colour"]=dicord.Colour(int(dict_embed["colour"]))
        if "timestamp" not in dict_embed:
            dict_embed["timestamp"]=datetime.datetime.now()

        embed=discord.Embed(**dict_embed)

        if "footer" in dict_embed:
            if "text" in dict_embed["footer"]:
                if len(dict_embed["footer"]["text"])>2048:
                    dict_embed["footer"]["text"]=dict_embed["footer"]["text"][:2045]+"..."
            dict_embed["footer"]["text"]=await formatVar(dict_embed["footer"]["text"], data)
            embed.set_footer(**dict_embed["footer"])
        if "image" in dict_embed:
            embed.set_image(await formatVar(dict_embed["image"],data))
        if "thumbnail" in dict_embed:
            embed.set_thumbnail(**dict_embed["thumbnail"])
        if "author" in dict_embed:
            if "name" in dict_embed["author"]:
                if len(dict_embed["author"]["name"])>256:
                    dict_embed["author"]["name"]=dict_embed["author"]["name"][:253]+"..."
                dict_embed["author"]["name"]=await formatVar(dict_embed["author"]["name"], data)
            else:
                raise Exception("Name is a necessary argument to set_author")
            embed.set_author(**dict_embed["author"])
        if "fields" in dict_embed:
            if len(dict_embed["fields"])>25:
                raise Exception("An embed message cannot contains more than 25 fields")
            for field in dict_embed["fields"]:
                if not "name" in field:
                    raise Exception("A field must contains a name")
                if len(field["name"])>256:
                    field["name"]=field["name"][:253]+"..."
                if not "value" in field:
                    raise Exception("A field must contains a value")
                if len(field["value"])>1024:
                    field["value"]=field["value"][:1021]+"..."
                if "inline" in field:
                    field["inline"]=bool(field["inline"])
                field["name"]=await formatVar(field["name"], data)
                field["value"]=await formatVar(field["value"], data)
                embed.add_field(**field)

        if isinstance(data, discord.message.Message):
            channel=data.channel
        if self.channel==None:
            return await channel.send(embed=embed)
        channel=self.bot.get_channel(self.channel)
        return await channel.send(embed=embed)


class SendEmbedMessageEternal(SendEmbedMessage):

    def __init__(self, bot, dict_embed, channel=None):
        super(self.__class__, self).__init__(bot, dict_embed, channel)

    async def execute(self, data):
        await self.process(data)

class SendEmbedMessageTimed(SendEmbedMessage):

    def __init__(self, bot, dict_embed, channel=None, delay=3):
        super(self.__class__, self).__init__(bot, dict_embed, channel)
        self.delay=delay

    async def execute(self, data):
        message=await self.process(data)
        await message.delete(delay=self.delay)

class ChangeUsername:
    """Change the username of the member or the author"""

    def __init__(self, bot, username):
        self.username=username

    async def execute(self, data: discord.Member):
        username=await formatVar(self.username, data)
        await data.edit(nick=username)

class Mute:
    """Mute the author or the member (toggle if bool mute=None)"""

    def __init__(self, mute):
        self.mute=mute

    async def execute(self, data: discord.Member):
        if self.mute==None:
            await data.edit(mute=not data.muted)
        await data.edit(mute=self.mute)

class DeleteIt:
    """Delete a message, only possible if the event is triggered with message"""

    def __init__(self, bot):
        pass

    async def execute(self, message):
        await message.delete()


"""
Things storage
"""

events={
    "MessageSentByAll": {
        "name": "MessageSentByAll",
        "description": "|number| messages are send between |delay| seconds by anybody on this server",
        "class": MessageSentByAll,
        "args": [
            {
                "name": "number",
                "description": "Number of messages sent",
                "type": "int"
            },
            {
                "name": "delay",
                "description": "Time between the first and the last message",
                "type": "int"
            },
            {
                "name": "channels",
                "description": "Id of the channels to watch (every channels if empty)",
                "type": "list"
            }
        ]
    },
    "MessageSentBySame": {
        "name": "MessageSentBySame",
        "description": "|number| messages are send between |delay| seconds by the same person on this server",
        "class": MessageSentBySame,
        "args": [
            {
                "name": "number",
                "description": "Number of messages sent",
                "type": "int"
            },
            {
                "name": "delay",
                "description": "Time between the first and the last message",
                "type": "int"
            },
            {
                "name": "channels",
                "description": "Id of the channels to watch (every channels if empty)",
                "type": "list"
            }
        ]
    },
    "MessageSentSimple": {
        "name": "MessageSentSimple",
        "description": "a message is sent in the channels with an id: |channels| by authors with id in: |authors| with role id in: |roles|",
        "class": MessageSentSimple,
        "args": [
            {
                "name": "channels",
                "description": "Id of the channels to watch (every if empty or none)",
                "type": "list"
            },
            {
                "name": "authors",
                "description": "Id of the authors to watch (every if empty or none)",
                "type": "list"
            },
            {
                "name": "roles",
                "description": "Id of the roles to watch (every if empty or none)",
                "type": "list"
            }
        ]
    },
    "Join": {
        "name": "Join",
        "description": "someone join your server",
        "class": Join,
        "args": []
    }
}

conditions={
    "HasUsername": {
        "name": "HasUsername",
        "description": "the user who sent the message or who is concerned has the pattern |pattern| in his username",
        "class": HasUsername,
        "args": [
            {
                "name": "regex",
                "description": "Pattern to search in the username",
                "type": "str"
            }
        ]
    },
    "Contains": {
        "name": "Contains",
        "description": "the message contains the pattern |pattern|",
        "class": Contains,
        "args": [
            {
                "name": "regex",
                "description": "Pattern to search in the message",
                "type": "str"
            }
        ]
    },
    "InDenyList": {
        "name": "InDenyList",
        "description": "the message content or the member name contains a word in the denylist |denylist|",
        "class": InDenyList,
        "args": [
            {
                "name": "denylist",
                "description": "The list of word which will be watched",
                "type": "list"
            }
        ]
    },
    "NotInAllowList": {
        "name": "NotInAllowList",
        "description": "the message content or the member name does not contain a word in the allowlist |allowlist",
        "class": NotInAllowList,
        "args": [
            {
                "name": "allowlist",
                "description": "The list of word which will be watched",
                "type": list
            }
        ]
    }
}

effects={
    "SendMessageEternal": {
        "name": "SendMessageEternal",
        "description": "send this message: |message| to the channel |channel| or, if no channel is defined, to the channel which is concerned about the event",
        "class": SendMessageEternal,
        "args": [
            {
                "name": "message",
                "description": "The message to send",
                "type": "str"
            },
            {
                "name": "channel",
                "description": "The channel id where to send the message",
                "type": "int"
            }
        ]
    },
    "SendMessageTimed": {
        "name": "SendMessageTimed",
        "description": "send the message: |message| which will be auto-deleted in |delay| seconds to the channel |channel| or, if no channel is defined, to the channel which is concerned about the event",
        "class": SendMessageTimed,
        "args": [
            {
                "name": "message",
                "description": "The message to send",
                "type": "str"
            },
            {
                "name": "channel",
                "description": "The channel id where to send the message",
                "type": "int"
            },
            {
                "name": "delay",
                "description": "Delay before the message is removed",
                "type": "int"
            }
        ]
    },
    "SendEmbedMessageEternal": {
        "name": "SendEmbedMessageEternal",
        "description": "send this embed message: |embed| to the channel |channel| or, if no channel is defined, to the channel which is concerned about the event",
        "class": SendEmbedMessageEternal,
        "args": [
            {
                "name": "embed",
                "description": "The embed to send",
                "type": "dict"
            },
            {
                "name": "channel",
                "description": "The channel id where to send the embed",
                "type": "int"
            }
        ]
    },
    "SendEmbedMessageTimed": {
        "name": "SendEmbedMessageTimed",
        "description": "send this embed: |embed| which will be auto-deleted in |delay| seconds to the channel |channel| or, if no channel is defined, to the channel which is concerned about the event",
        "class": SendEmbedMessageTimed,
        "args": [
            {
                "name": "embed",
                "description": "The embed to send",
                "type": "dict"
            },
            {
                "name": "channel",
                "description": "The channel id where to send the embed",
                "type": "int"
            },
            {
                "name": "delay",
                "description": "Delay before the embed is removed",
                "type": "int"
            }
        ]
    },
    "ChangeUsername": {
        "name": "ChangeUsername",
        "description": "change the username with |username|",
        "class": ChangeUsername,
        "args": [
            {
                "name": "username",
                "description": "The new username of the member",
                "type": "str"
            }
        ]
    },
    "Mute": {
        "name": "Mute",
        "description": "will toggle the mute of a user, or set it with the value of |mute| if it is not None",
        "class": Mute,
        "args": [
            {
                "name": "mute",
                "description": "If the user has to be mute or un-muted, toggle if None",
                "type": "bool"
            }
        ]
    },
    "DeleteIt": {
        "name": "DeleteIt",
        "description": "delete the message",
        "class": DeleteIt,
        "args": []
    }
}
