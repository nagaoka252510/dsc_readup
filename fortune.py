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
        '運勢':omikuji[random.randrange(5)],
        '和歌':waka[random.randint(1, 100)]["bodyKanji"],
        '願望':nariyuki[random.randrange(11)],
        '健康':nariyuki[random.randrange(11)],
        '待ち人':kurukonai[random.randrange(6)],
        '出産':nariyuki[random.randrange(11)],
        '商売':nariyuki[random.randrange(11)],
        '投稿':'はやめで'
    }

    return result

