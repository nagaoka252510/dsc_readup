import json
import discord
from voice import knockApi


with open('token.json') as f:
    df = json.load(f)
group = input("input group:".encode("utf_8"))
token = df[group]

client = discord.Client()
voice = {}
channel = {}
msger = {}
help_msg="""[?summon]: ボイスチャンネルへ呼び出し \n
[?bye]:ボイスチャンネルからさよなら \n
[?yukari]:声がゆかりさんになります \n
[?maki]:声がマキさんになります \n
[?help]:いまさっき叩いたでしょうが!!! \n
"""

@client.event
async def on_ready():
    print('ログインしました')


@client.event
async def on_message(message):
    if message.author.bot:
        return
    global voice
    global channel
    global msger
    server_id = message.server.id
    if message.content == "?summon":
            if server_id not in voice:
                voice[server_id] = await client.join_voice_channel(message.author.voice_channel)
                channel[server_id] = message.channel.id
                msger[server_id] = "sumire"
            return

    if message.channel.id == channel[server_id]: #指定したチャンネルでの発言の時
        if message.content == "?bye":
            await voice[server_id].disconnect()
            del voice[server_id]
            del channel[server_id]
            return
        if message.content == "?help":
            await client.send_message(message.channel, help_msg)
            return
        if message.content == "?yukari":
            msger[server_id] = "sumire"
            return
        if message.content == "?maki":
            msger[server_id] = "maki"
            return
        
        knockApi(message.content, msger[server_id], group)
        player = voice[server_id].create_ffmpeg_player('./sound/{}/msg.wav'.format(group))
        try:
            player.start()
        except:
            pass

client.run(token)