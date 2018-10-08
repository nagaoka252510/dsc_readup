import json
from time import sleep
import discord
from discord.ext import commands
from pydub import AudioSegment
from voice import knockApi


with open('token.json') as f:
    df = json.load(f)
group = input("input group:")
token = df[group]

bot = commands.Bot(command_prefix='?')

client = discord.Client()
voice = {}
channel = {}
msger = {}
guild_id = 0

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

bot.remove_command('help')

@bot.command()
async def help(ctx):
    embed = discord.Embed(title='喋太郎', description='I read aloud messages.')
    embed.add_field(name='?summon', value='Call me to the voice channel.', inline=False)
    embed.add_field(name='?bye', value='Remove me to the voice channel.', inline=False)
    embed.add_field(name='?yukari', value='Change voice to Yukari.', inline=False)
    embed.add_field(name='?maki', value='Change voice to Maki.', inline=False)
    embed.add_field(name='?kou', value='Change voice to Kou.', inline=False)

    await ctx.send(embed=embed)

@bot.command()
async def summon(ctx):
    global voice
    global channel
    global msger
    global guild_id
    guild_id = ctx.guild.id
    if guild_id not in voice:
        voice[guild_id] = await ctx.author.voice.channel.connect()
        channel[guild_id] = ctx.channel.id
        msger[guild_id] = "sumire"
        await ctx.channel.send('Hello! I\'m 喋太郎!')
            
@bot.command()
async def bye(ctx):
    global guild_id
    global voice
    global channel

    if ctx.channel.id == channel[guild_id]:
        await ctx.channel.send('Good Bye!')
        await voice[guild_id].disconnect()
        del voice[guild_id]
        del channel[guild_id]
        guild_id = 0

@bot.command()
async def yukari(ctx):
    global msger
    global guild_id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "sumire"

@bot.command()
async def maki(ctx):
    global msger
    global guild_id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "maki"

@bot.command()
async def kou(ctx):
    global msger
    global guild_id
    if ctx.channel.id == channel[guild_id]:
        msger[guild_id] = "osamu"

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    global voice
    global channel
    global msger
    global guild_id
    if guild_id == 0 or message.content.startswith("?"):
        await bot.process_commands(message)
        return

    if message.channel.id == channel[guild_id]:
        knockApi(message.content, msger[guild_id], group)
        voice_mess = './sound/{}/msg.wav'.format(group)
        mess_time = AudioSegment.from_file(voice_mess, "wav").duration_seconds
        voice[guild_id].play(discord.FFmpegPCMAudio(voice_mess), after=lambda e: print('done', e))
        sleep(mess_time)
    
    await bot.process_commands(message)

bot.run(token)