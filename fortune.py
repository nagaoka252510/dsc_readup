import random
import json
from datetime import date

omikuji = ['大吉', '吉', '中吉', '小吉', '凶']
nariyuki = ['よくない', 'いい感じ', 'つよい', 'ありよりのあり', 'ないよりのあり', 'ありよりのなし', 'ないよりのなし', 'やめとき', 'よわい', 'Power', '敗北者']
kurukonai = ['こない', 'くる', 'もういる', 'となり', '会いたくて会いたくて震える', '会いたくて (´・_・｀) 会いたくて (´；_；｀) ブルブルブルブルwwwwwwwwwwアイwwwwアイwwwwwwwww┏( ^o^)┓wwwwww┗( ^o^)┛ブルwwwwwwベリwwwwwwwwアイwwwwwww']

# 和歌のロード 和歌のjsonファイルは https://qiita.com/wakaba@github/items/861500682eb414142938 より
with open('waka.json') as f:
    waka = json.load(f)

def get_predic(id):
    datenum = int(date.today().strftime('%Y%m%d'))
    random.seed(id+datenum)
    
    result = {
        '運勢':random.choice(omikuji),
        '和歌':random.choice(waka)["bodyKanji"],
        '願望':random.choice(nariyuki),
        '健康':random.choice(nariyuki),
        '待ち人':random.choice(kurukonai),
        '出産':random.choice(nariyuki),
        '商売':random.choice(nariyuki),
        '投稿':'はやめで'
    }

    return result