import datetime
import os
import re
import sys
import json
import logging
import psycopg2
import discord
import asyncio
import ctrl_db
from discord.ext import commands
from pydub import AudioSegment
from voice import knockApi
from fortune import get_predic

# ログを出力
logger = logging.getLogger('discord')
logger.setLevel(logging.WARNING)
handler = logging.FileHandler(filename='syabetaro.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Discord アクセストークン読み込み
with open('token.json') as f:
    df = json.load(f)

token = df['bot']
manager = int(df['manager_id'])

# Speakerの配列

sps = ['yukari', 'maki', 'ai', 'kou']

# コマンドプレフィックスを設定
bot = commands.Bot(command_prefix='?')

# サーバ別に各値を保持
voice = {} # ボイスチャンネルID
channel = {} # テキストチャンネルID

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
    str_id = str(ctx.guild.id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix
    
    embed = discord.Embed(title='喋太郎', description='メッセージを読み上げるBotやで。')
    embed.add_field(name='{}summon'.format(prefix), value='わいをボイスチャンネルに呼ぶコマンドや。', inline=False)
    embed.add_field(name='{}bye'.format(prefix), value='わいをボイスチャンネルから追い出す時に使うんや。', inline=False)
    embed.add_field(name='{}spk'.format(prefix), value='声を変えるのに使うで。詳しくは、「{}spk help」を見てほしい。'.format(prefix), inline=False)
    embed.add_field(name='{}set_prefix'.format(prefix), value='コマンドプレフィックスを変更するのに使うで。「{}set_prefix ??」みたいにするといいぞ。'.format(prefix), inline=False)
    embed.add_field(name='{}stop'.format(prefix), value='わいが喋ってるのを黙らせるで。', inline=False)
    embed.add_field(name='{}wbook'.format(prefix), value='読み仮名の登録とかができるで。詳しくは、「{}wbook help」を見て欲しい。'.format(prefix), inline=False)
    embed.add_field(name='{}readname'.format(prefix), value='コマンドの後に「on」か「off」をつけることで、名前を読み上げるか切り替えられるで。', inline=False)
    embed.add_field(name='{}speed'.format(prefix), value='コマンドの後に0.5~4.0の小数をつけることで、読み上げ速度が変わるで。デフォルトは1.0や。', inline=False)
    embed.add_field(name='{}intone'.format(prefix), value='コマンドの後に0.0~2.0の小数をつけることで、抑揚が変わるで。デフォルトは1.1や。', inline=False)
    embed.add_field(name='{}pitch'.format(prefix), value='コマンドの後に0.0~2.0の小数をつけることで、高さが変わるで。デフォルトは1.2や。', inline=False)
    embed.add_field(name='{}uranai'.format(prefix), value='おみくじが引けるで。結果は日替わりや。', inline=False)

    await ctx.send(embed=embed)

# summonコマンドの処理
@bot.command()
async def summon(ctx):
    global voice
    global channel
    # global guild_id
    guild_id = ctx.guild.id # サーバIDを取得
    vo_ch = ctx.author.voice # 召喚した人が参加しているボイスチャンネルを取得

    # サーバを登録
    add_guild_db(ctx.guild)

    # サーバのプレフィックスを取得
    guild_deta = ctrl_db.get_guild(str(guild_id))
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    # 召喚された時、voiceに情報が残っている場合
    if guild_id in voice:
        await voice[guild_id].disconnect()
        del voice[guild_id] 
        del channel[guild_id]
    # 召喚した人がボイスチャンネルにいた場合
    if not isinstance(vo_ch, type(None)): 
        voice[guild_id] = await vo_ch.channel.connect()
        channel[guild_id] = ctx.channel.id
        noties = get_notify(ctx)
        await ctx.channel.send('毎度おおきに。わいは喋太郎や。"{}help"コマンドで使い方を表示するで'.format(prefix))
        for noty in noties:
            await ctx.channel.send(noty)
        if len(noties) != 0:
            await ctx.channel.send('喋太郎に何かあれば、だーやまんのお題箱( https://odaibako.net/u/gamerkohei )までお願いします。\r喋太郎の開発、運用等にご協力をお願いします🙌\rhttps://fantia.jp/gamerkohei ')
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

# speakerコマンドの処理
@bot.command()
async def spk(ctx, arg1='emp'):
    global channel
    cand = arg1
    guild_id = ctx.guild.id
    str_id = str(guild_id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    if cand == 'emp':
        await ctx.send('引数が不足してるで。{}spk helpを見てみ。'.format(prefix))
        return

    if cand == 'help':
        embed = discord.Embed(title='{}spk'.format(prefix), description='声を変えるコマンド')
        embed.add_field(name='{}spk yukari'.format(prefix), value='ゆかりさんに変身', inline=False)
        embed.add_field(name='{}spk maki'.format(prefix), value='マキマキに変身', inline=False)
        embed.add_field(name='{}spk ai'.format(prefix), value='アイちゃんに変身', inline=False)
        embed.add_field(name='{}spk kou'.format(prefix), value='コウ先生に変身', inline=False)

        await ctx.send(embed=embed)
    else:
        # 呼び出したチャンネルでコマンドが叩かれた場合
        if ctx.channel.id == channel[guild_id]:
            if cand not in sps:
                # 引き数のキャラが存在しない場合
                await ctx.channel.send('おっと、そのキャラは未実装だ。すまねえ。')
                return
            elif cand == 'yukari':
                # ゆかりの場合
                cand = 'sumire'
            elif cand == 'ai':
                # アイの場合
                cand = 'anzu'
            elif cand == 'kou':
                # コウの場合
                cand = 'osamu'

            # 話者を設定
            ctrl_db.set_user(str(ctx.author.id), cand)

@bot.command()
async def set_prefix(ctx, arg1):
    # prefixの設定
    guild_id = str(ctx.guild.id)

    ctrl_db.set_prefix(guild_id, arg1)
    await ctx.send('prefixを{}に変更したで。'.format(arg1))

# ここから管理者コマンド
@bot.command()
async def notify(ctx, arg1, arg2):
    # 管理人からしか受け付けない
    if ctx.author.id != manager:
        return
    ctrl_db.add_news(arg1, arg2.replace('\\r', '\r'))

@bot.command()
async def say_adm(ctx, arg1):
    # 管理人からしか受け付けない
    if ctx.author.id != manager:
        return
    global channel

    for vc in bot.voice_clients:
        if isinstance(channel[vc.guild.id], type(None)):
            continue
        for txch in vc.guild.text_channels:
            if txch.id == channel[vc.guild.id]:
                await txch.send('[INFO] {}'.format(arg1))
# ここまで

# 喋太郎の発言を止める
@bot.command()
async def stop(ctx):
    global voice
    vc = voice[ctx.guild.id]
    if(vc.is_playing()):
        vc.stop()
    else:
        await ctx.send("なんも言うてへんで")

#辞書の操作をするコマンド
@bot.command()
async def wbook(ctx, arg1='emp', arg2='emp', arg3='emp'):
    guild_id = ctx.guild.id
    str_id = str(guild_id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    if arg1 == 'help':
        embed = discord.Embed(title='{}wbook'.format(prefix), description='辞書を操作するコマンド。データはサーバ毎に分けられてるから安心してな。')
        embed.add_field(name='{}wbook add 単語 よみがな'.format(prefix), value='読み上げ文にこの単語があった場合、よみがなの通りに読み変えるで。\r例:{}wbook add 男の娘 おとこのこ'.format(prefix), inline=False)
        embed.add_field(name='{}wbook list'.format(prefix), value='登録した単語の一覧を表示するで。', inline=False)
        embed.add_field(name='{}wbook delete 番号'.format(prefix), value='listで表示された辞書番号の単語を削除するで', inline=False)

        await ctx.send(embed=embed)

    elif arg1 == 'list':
        # リスト表示
        words = ctrl_db.get_dict(str_id)
        embed = discord.Embed(title='辞書一覧')
        embed.add_field(name='番号', value='単語:よみがな', inline=False)
        for i, word in enumerate(words, start=1):
            if i%15 == 0:
                await ctx.send(embed=embed)
                embed = discord.Embed(title=str(word.id), description='{}:{}'.format(word.word, word.read))
            else:
                embed.add_field(name=str(word.id), value='{}:{}'.format(word.word, word.read), inline=False)

        await ctx.send(embed=embed)

    elif arg1 == 'add':
        if arg2 == 'emp' or arg3 == 'emp':
            await ctx.send('引数が不足してるで。{}wbook helpを見てみ。'.format(prefix))
        # 辞書追加、あるいはアップデート
        ctrl_db.add_dict(arg2, arg3, str_id)

    elif arg1 == 'delete':
        if arg2 == 'emp':
            await ctx.send('引数が不足してるで。{}wbook helpを見てみ。'.format(prefix))
        elif arg2.isdecimal():
            # 削除処理
            is_del = ctrl_db.del_dict(int(arg2), str_id)
            if is_del == True:
                await ctx.send('削除成功や。')
            else:
                await ctx.send('その番号の単語は登録されてないで。')
        else:
            await ctx.send('使い方が正しくないで。{}wbook helpを見てみ。'.format(prefix))
    else:
        await ctx.send('使い方が正しくないで。{}wbook helpを見てみ。'.format(prefix))

@bot.command()
async def readname(ctx, arg1='emp'):
    guild_id = ctx.guild.id
    str_id = str(guild_id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    if arg1 == 'emp':
        await ctx.send('引数が不足してるで。{}helpを見てみ。'.format(prefix))
    elif arg1 == 'on':
        ctrl_db.set_nameread(True, str_id)
    elif arg1 == 'off':
        ctrl_db.set_nameread(False, str_id)
    else:
        await ctx.send('使い方が正しくないで。{}helpを見てみ。'.format(prefix))

@bot.command()
async def speed(ctx, arg1='emp'):
    guild_id = ctx.guild.id
    str_id = str(guild_id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    struid = str(ctx.author.id)

    if arg1 == 'emp':
        await ctx.send('引数が不足してるで。{}helpを見てみ。'.format(prefix))
        return

    try:
        speed = float(arg1)
    except:
        await ctx.send('使い方が正しくないで。{}helpを見てみ。'.format(prefix))
        return

    if speed >= 0.5 and speed <= 4.0:
        ctrl_db.set_readspeed(speed, struid)
    else:
        await ctx.send('数値が正しくないで。0.5~4.0を指定してくれな。デフォルトは1.0や。')

@bot.command()
async def intone(ctx, arg1='emp'):
    guild_id = ctx.guild.id
    str_id = str(guild_id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    struid = str(ctx.author.id)

    if arg1 == 'emp':
        await ctx.send('引数が不足してるで。{}helpを見てみ。'.format(prefix))
        return

    try:
        r_range = float(arg1)
    except:
        await ctx.send('使い方が正しくないで。{}helpを見てみ。'.format(prefix))
        return

    if r_range >= 0.0 and r_range <= 2.0:
        ctrl_db.set_readrange(r_range, struid)
    else:
        await ctx.send('数値が正しくないで。0.0~2.0を指定してくれな。デフォルトは1.1や。')

@bot.command()
async def pitch(ctx, arg1='emp'):
    guild_id = ctx.guild.id
    str_id = str(guild_id)
    guild_deta = ctrl_db.get_guild(str_id)
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    struid = str(ctx.author.id)

    if arg1 == 'emp':
        await ctx.send('引数が不足してるで。{}helpを見てみ。'.format(prefix))
        return

    try:
        pitch = float(arg1)
    except:
        await ctx.send('使い方が正しくないで。{}helpを見てみ。'.format(prefix))
        return

    if pitch >= 0.0 and pitch <= 2.0:
        ctrl_db.set_readpitch(pitch, struid)
    else:
        await ctx.send('数値が正しくないで。0.0~2.0を指定してくれな。デフォルトは1.2や。')

@bot.command()
async def uranai(ctx):
    predic = get_predic(ctx.author.id)

    embed = discord.Embed(title='{}のおみくじ'.format(ctx.author.display_name))
    embed.add_field(name='運勢', value=predic['運勢'], inline=False)
    embed.add_field(name='和歌', value=predic['和歌'], inline=False)
    embed.add_field(name='願望', value=predic['願望'], inline=False)
    embed.add_field(name='健康', value=predic['健康'], inline=False)
    embed.add_field(name='待ち人', value=predic['待ち人'], inline=False)
    embed.add_field(name='出産', value=predic['出産'], inline=False)
    embed.add_field(name='商売', value=predic['商売'], inline=False)
    embed.add_field(name='投稿', value=predic['投稿'], inline=False)

    await ctx.send(embed=embed)

# メッセージを受信した時の処理
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    global voice
    global channel
    
    mess_id = message.author.id # メッセージを送った人のユーザID

    # ギルドIDがない場合、DMと判断する
    if isinstance(message.guild, type(None)):
        # 管理人からのDMだった場合
        if message.author.id == manager:
            #コマンド操作になっているか
            if message.content.startswith('?'):
                await message.channel.send('コマンドを受け付けたで')
                await bot.process_commands(message) # メッセージをコマンド扱いにする
                return
            else:
                await message.channel.send('コマンド操作をしてくれ')
                return
        else:
            await message.channel.send('喋太郎に何かあれば、だーやまんのお題箱( https://odaibako.net/u/gamerkohei )までお願いします。')
            return

    guild_id = message.guild.id # サーバID

    # ユーザ情報(speaker)を取得
    user = ctrl_db.get_user(str(mess_id))
    if isinstance(user, type(None)):
        # ユーザ情報がなければ、dbへ登録。話者はsumire
        ctrl_db.add_user(str(mess_id), message.author.name, 'sumire')
        user = ctrl_db.get_user(str(mess_id))

    # サーバのプレフィックスを取得
    guild_deta = ctrl_db.get_guild(str(guild_id))
    if isinstance(guild_deta, type(None)):
        prefix = '?'
    else:
        prefix = guild_deta.prefix

    # コマンドだった場合
    if message.content.startswith(prefix):
        # prefixは?へ変換する
        message.content = message.content.replace(prefix, '?', 1)
        await bot.process_commands(message) # メッセージをコマンド扱いにする
        return

    # 召喚されていなかった場合
    if guild_id not in channel:
        return
    
    str_guild_id = str(guild_id)

    # メッセージを、呼び出されたチャンネルで受信した場合
    if message.channel.id == channel[guild_id]:
        # URLを、"URL"へ置換
        get_msg = re.sub(r'http(s)?://([\w-]+\.)+[\w-]+(/[-\w ./?%&=]*)?', 'URL', message.content)
        # reactionの置換
        get_msg = get_msg.replace('<:', '')
        get_msg = re.sub(r':[0-9]*>', '', get_msg)
        # mention と channel_mentionを名前へ置換
        mn_list = message.raw_mentions
        ch_list = message.raw_channel_mentions
        # IDに対応する名前の辞書を作成
        mn_dict = {}
        ch_dict = {}
        # mentionの、ユーザネームへの置換
        for ment in mn_list:
            # 自身へのメンションかどうかで、Keyを変える
            if ment == mess_id:
                mn_dict['<@!{}>'.format(str(ment))] = message.guild.get_member(ment).name
            else:
                mn_dict['<@{}>'.format(str(ment))] = message.guild.get_member(ment).name
        # channel_mentionの、チャンネル名への置換
        for cnls in ch_list:
            ch_dict['<#{}>'.format(str(cnls))] = message.guild.get_channel(cnls).name
        # 変換テーブルの作成
        for me_key in mn_dict.keys():
            get_msg = get_msg.replace(me_key, mn_dict[me_key], 1)
        for ch_key in ch_dict.keys():
            get_msg = get_msg.replace(ch_key, ch_dict[ch_key], 1)
        # 置換文字のリストを取得
        words = ctrl_db.get_dict(str_guild_id)
        for word in words:
            get_msg = get_msg.replace(word.word, word.read)
        get_msg = get_msg.replace('<', '').replace('>', '')
        # 読み上げモード確認
        is_nameread = ctrl_db.get_guild(str_guild_id).is_nameread
        # モードによって名前を追加するか検討
        if is_nameread == True:
            get_msg = '{}、'.format(message.author.display_name) + get_msg
        #リクエスト回数のカウント
        ctrl_db.set_reqcount(datetime.date.today(), datetime.datetime.now().hour)
        # メッセージを、音声ファイルを作成するモジュールへ投げる処理
        try :
            rawfile = await knockApi(get_msg , user.speaker, user.speed, user.r_range, user.pitch, str_guild_id)
        # 失敗した場合(ログは吐くようにしたい)
        except:
            await message.channel.send('To {} ちょいとエラー起きたみたいや。少し待ってからメッセージ送ってくれな。'.format(message.author.name))
            return
        
        # 音声ファイルを再生中の場合再生終了まで止まる
        while (voice[guild_id].is_playing()):
            # 他の処理をさせて1秒待機
            await asyncio.sleep(1)
        # 再生処理
        voice_mess = './cache/{}/{}'.format(str_guild_id, rawfile) # rawファイルのディレクトリ
        voice[guild_id].play(discord.FFmpegPCMAudio(voice_mess, before_options='-f s16be -ar 16k -ac 1')) # エンコードして音声チャンネルで再生
        await asyncio.sleep(0.5)
        os.remove(voice_mess) #rawファイルの削除

def add_guild_db(guild):
    str_id = str(guild.id)
    guilds = ctrl_db.get_guild(str_id)
    # デフォルトのprefixは'?'
    prefix = '?'

    if isinstance(guilds, type(None)):
        ctrl_db.add_guild(str_id, guild.name, prefix)

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