import sys
import json
from time import sleep
import discord
from discord.ext import commands
from pydub import AudioSegment
from voice import knockApi


with open('token.json') as f:
    df = json.load(f)

token = df["bot"]

bot = commands.Bot(command_prefix='?')

voice = {}
channel = {}
msger = {}
# guild_id = 0

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title='喋太郎', description='メッセージを読み上げるBotやで。')
    embed.add_field(name='?summon', value='わいをボイスチャンネルに呼ぶコマンドや。', inline=False)
    embed.add_field(name='?bye', value='わいをボイスチャンネルから追い出す時に使うんや。', inline=False)
    embed.add_field(name='?yukari', value='声がゆかりはんに変わるで。', inline=False)
    embed.add_field(name='?maki', value='声がマキマキに変わるで。', inline=False)
    embed.add_field(name='?kou', value='声がコウはんに変わるで。', inline=False)
    embed.add_field(name='?ai', value='声がアイちゃんに変わるで。', inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def summon(ctx):
    global voice
    global channel
    global msger
    global guild_id
    guild_id = ctx.guild.id
    vo_ch = ctx.author.voice
    if guild_id not in voice and not isinstance(vo_ch, type(None)):
        voice[guild_id] = await vo_ch.channel.connect()
        channel[guild_id] = ctx.channel.id
        msger[guild_id] = "sumire"
        await ctx.channel.send('毎度おおきに。わいは喋太郎や。"?help"コマンドで使い方を表示するで')
    else :
        await ctx.channel.send('あんたボイスチャンネルおらへんやんけ！')
            
@bot.command()
async def bye(ctx):
    global guild_id
    global voice
    global channel
    guild_id = ctx.guild.id

    if ctx.channel.id == channel[guild_id]:
        await ctx.channel.send('じゃあの')
        await voice[guild_id].disconnect()
        del voice[guild_id]
        del channel[guild_id]
        guild_id = 0

@bot.command()
async def yukari(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "sumire"

@bot.command()
async def maki(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "maki"

@bot.command()
async def kou(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "osamu"

@bot.command()
async def ai(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "anzu"


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    global voice
    global channel
    global msger
    guild_id = message.guild.id
    if guild_id not in channel or message.content.startswith("?"):
        await bot.process_commands(message)
        return

    str_guild_id = str(guild_id)
    if message.channel.id == channel[guild_id]:
        knockApi(message.content, msger[guild_id], str_guild_id)
        voice_mess = './sound/{}/msg.wav'.format(str_guild_id)
        mess_time = AudioSegment.from_file(voice_mess, "wav").duration_seconds
        voice[guild_id].play(discord.FFmpegPCMAudio(voice_mess), after=lambda e: print('done', e))
        sleep(mess_time)
    
    await bot.process_commands(message)

bot.run(token)
