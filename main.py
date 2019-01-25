import re
import sys
import json
import discord
import ctrl_db
from discord.ext import commands
from pydub import AudioSegment
from voice import knockApi


# Discord アクセストークン読み込み
with open('token.json') as f:
    df = json.load(f)

token = df["bot"]
manager = int(df["manager_id"])

# コマンドプレフィックスを設定
bot = commands.Bot(command_prefix='?')

# サーバ別に各値を保持
voice = {} # ボイスチャンネルID
channel = {} # テキストチャンネルID
msger = {} # ユーザごとのボイス情報

#bot自身
client = discord.Client()
syabe_taro = client.user

@bot.event
# ログイン時のイベント
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# 標準のhelpコマンドを無効化
bot.remove_command('help')

# helpコマンドの処理
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

# summonコマンドの処理
@bot.command()
async def summon(ctx):
    global voice
    global channel
    global msger
    global guild_id
    guild_id = ctx.guild.id # サーバIDを取得
    vo_ch = ctx.author.voice # 召喚した人が参加しているボイスチャンネルを取得
    # 召喚された時、voiceに情報が残っている場合
    if guild_id in voice:
        await voice[guild_id].disconnect()
        del voice[guild_id] 
        del channel[guild_id]
    # 召喚した人がボイスチャンネルにいた場合
    if not isinstance(vo_ch, type(None)): 
        voice[guild_id] = await vo_ch.channel.connect()
        channel[guild_id] = ctx.channel.id
        add_guild_db(ctx.guild)
        noties = get_notify(ctx)
        await ctx.channel.send('毎度おおきに。わいは喋太郎や。"?help"コマンドで使い方を表示するで')
        for noty in noties:
            await ctx.channel.send(noty)
        if len(noties) != 0:
            await ctx.channel.send('もし良ければ、製作者にポップコーンでも奢ってあげてください\rhttp://amzn.asia/5fx6FNv')
    else :
        await ctx.channel.send('あんたボイスチャンネルおらへんやんけ！')


# byeコマンドの処理            
@bot.command()
async def bye(ctx):
    global guild_id
    global voice
    global channel
    guild_id = ctx.guild.id
    # コマンドが、呼び出したチャンネルで叩かれている場合
    if ctx.channel.id == channel[guild_id]:
        await ctx.channel.send('じゃあの')
        await voice[guild_id].disconnect() # ボイスチャンネル切断
        # 情報を削除
        del voice[guild_id] 
        del channel[guild_id]

# yukariコマンドの処理
@bot.command()
async def yukari(ctx):
    global msger
    guild_id = ctx.guild.id
    # 呼び出したチャンネルでコマンドが叩かれた場合
    if ctx.channel.id == channel[guild_id]:
        msger[ctx.author.id] = "sumire" # 話者をsumire(結月ゆかり)に変更

@bot.command()
async def maki(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[ctx.author.id] = "maki" # 弦巻マキに変更

@bot.command()
async def kou(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[ctx.author.id] = "osamu" # 水奈瀬コウに変更

@bot.command()
async def ai(ctx):
    global msger
    guild_id = ctx.guild.id
    if ctx.channel.id == channel[guild_id]:
        msger[ctx.author.id] = "anzu" # 月読アイに変更

@bot.command()
async def notify(ctx, arg1, arg2):
    # 管理人からしか受け付けない
    if ctx.author.id != manager:
        return
    ctrl_db.add_news(arg1, arg2.replace("\\r", "\r"))


# メッセージを受信した時の処理
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    global voice
    global channel
    global msger

    mess_id = message.author.id # メッセージを送った人のユーザID

    #ギルドIDがない場合、DMと判断する
    if isinstance(message.guild, type(None)):
        # 管理人からのDMだった場合
        if message.author.id == manager:
            #コマンド操作になっているか
            if message.content.startswith("?"):
                await message.channel.send("コマンドを受け付けたで")
                await bot.process_commands(message) # メッセージをコマンド扱いにする
                return
            else:
                await message.channel.send("コマンド操作をしてくれ")
                return
        else:
            await message.channel.send("喋太郎に何かあれば、だーやまんの質問箱(https://peing.net/ja/gamerkohei?event=0)までお願いします。")
            return

    guild_id = message.guild.id # サーバID

    # ユーザに話者が設定されていない場合
    if mess_id not in msger:
        msger[mess_id] = 'sumire' # 話者をsumireに設定

    # 召喚されていないか、コマンドだった場合
    if guild_id not in channel or message.content.startswith("?"):
        await bot.process_commands(message) # メッセージをコマンド扱いにする
        return

    str_guild_id = str(guild_id)

    # メッセージを、呼び出されたチャンネルで受信した場合
    if message.channel.id == channel[guild_id]:
        # 音声ファイルを再生中の場合再生終了まで止まる
        while (voice[guild_id].is_playing()):
            pass
        # URLを、"URL"へ置換
        get_msg = re.sub(r'http(s)?://([\w-]+\.)+[\w-]+(/[-\w ./?%&=]*)?', 'URL', message.content)
        # 辞書dbから、鯖で登録された単語を抽出し、置換する
        # w_dict = ctrl_db.get_dict(str_guild_id)
        for word in w_dict:
            get_msg = get_msg.replace(word.word, word.read)
    
        try : # メッセージを、音声ファイルを作成するモジュールへ投げる処理
            knockApi(get_msg , msger[mess_id], str_guild_id)
        except : # 失敗した場合(ログは吐くようにしたい)
            await message.channel.send('ちょいとエラー起きたみたいや。少し待ってからメッセージ送ってくれな。')
            return 
        
        # 再生処理
        voice_mess = './sound/{}/msg.wav'.format(str_guild_id) # 音声ファイルのディレクトリ
        voice[guild_id].play(discord.FFmpegPCMAudio(voice_mess), after=lambda e: print('done', e)) # 音声チャンネルで再生
    
    await bot.process_commands(message)

def add_guild_db(guild):
    str_id = str(guild.id)
    guilds = ctrl_db.get_guild(str_id)

    if isinstance(guilds, type(None)):
        ctrl_db.add_guild(str_id, guild.name)

def get_notify(ctx):
    str_id = str(ctx.guild.id)
    notifis = ctrl_db.get_notify(str_id)
    newses = ctrl_db.get_news()
    list_noty = []

    for new in newses:
        is_notify = False
        for noty in notifis:
            if new.id == noty.news_id:
                is_notify = True
        if is_notify == False:
            list_noty.append('[{}] {}'.format(new.category, new.text))
            ctrl_db.add_notify(new.id, str_id)
    
    return list_noty

bot.run(token)