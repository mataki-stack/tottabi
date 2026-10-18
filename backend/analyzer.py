from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from backend.fetcher import RAW_CACHE_PATH
from backend.storage import save_videos_dataset

# ---------------------------------------------------------------------------
# 1. Domestic Regions & 47 Prefectures Dictionary
# ---------------------------------------------------------------------------
JAPAN_REGIONS: list[dict[str, Any]] = [
    {
        "id": "hokkaido",
        "name": "北海道",
        "playlist_keywords": ["北海道"],
        "prefectures": ["北海道"],
    },
    {
        "id": "tohoku",
        "name": "東北",
        "playlist_keywords": ["東北"],
        "prefectures": ["青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"],
    },
    {
        "id": "kanto",
        "name": "関東",
        "playlist_keywords": ["関東"],
        "prefectures": ["茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県"],
    },
    {
        "id": "chubu",
        "name": "中部・北陸",
        "playlist_keywords": ["中部", "北陸"],
        "prefectures": ["新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県"],
    },
    {
        "id": "kinki",
        "name": "近畿・関西",
        "playlist_keywords": ["近畿", "関西"],
        "prefectures": ["三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県"],
    },
    {
        "id": "chugoku",
        "name": "中国",
        "playlist_keywords": ["(中国)"],
        "prefectures": ["鳥取県", "島根県", "岡山県", "広島県", "山口県"],
    },
    {
        "id": "shikoku",
        "name": "四国",
        "playlist_keywords": ["四国"],
        "prefectures": ["徳島県", "香川県", "愛媛県", "高知県"],
    },
    {
        "id": "kyushu_okinawa",
        "name": "九州・沖縄",
        "playlist_keywords": ["九州", "沖縄"],
        "prefectures": ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"],
    },
]

PREF_TO_REGION: dict[str, str] = {}
for _reg in JAPAN_REGIONS:
    for _pref in _reg["prefectures"]:
        PREF_TO_REGION[_pref] = _reg["name"]

# Keywords mapped to each prefecture (carefully curated to avoid false positives)
PREFECTURE_KEYWORDS: dict[str, list[str]] = {
    "北海道": ["北海道", "札幌", "函館", "小樽", "旭川", "富良野", "美瑛", "稚内", "宗谷岬", "知床", "網走", "釧路", "帯広", "十勝", "室蘭", "登別", "洞爺湖", "ニセコ", "積丹", "利尻", "礼文", "根室", "納沙布", "摩周湖", "屈斜路湖", "阿寒湖", "苫小牧", "千歳", "ラビスタ函館", "セイコーマート", "トリトン", "ラッキーピエロ"],
    "青森県": ["青森県", "青森市", "弘前", "八戸", "十和田", "奥入瀬", "恐山", "下北半島", "大間", "津軽", "ねぶた", "酸ヶ湯", "不老ふ死温泉", "竜飛崎"],
    "岩手県": ["岩手県", "盛岡", "一関", "平泉", "中尊寺", "花巻", "遠野", "宮古市", "釜石", "大船渡", "久慈", "龍泉洞", "わんこそば", "八幡平"],
    "宮城県": ["宮城県", "仙台", "松島", "気仙沼", "石巻", "塩竈", "秋保温泉", "鳴子温泉", "蔵王キツネ村"],
    "秋田県": ["秋田県", "秋田市", "男鹿", "なまはげ", "田沢湖", "乳頭温泉", "角館", "横手", "大館", "きりたんぽ", "稲庭うどん", "玉川温泉"],
    "山形県": ["山形県", "山形市", "米沢", "鶴岡", "酒田", "銀山温泉", "蔵王温泉", "山寺", "天童", "最上川", "加茂水族館"],
    "福島県": ["福島県", "福島市", "会津若松", "会津", "喜多方", "郡山", "いわき", "猪苗代", "磐梯", "大内宿", "五色沼", "ハワイアンズ"],
    "茨城県": ["茨城県", "水戸", "つくば", "大洗", "ひたちなか", "袋田の滝", "筑波山", "鹿嶋", "笠間", "牛久"],
    "栃木県": ["栃木県", "宇都宮", "日光", "鬼怒川", "那須", "佐野ラーメン", "足利", "華厳の滝", "中禅寺湖", "益子"],
    "群馬県": ["群馬県", "前橋", "高崎", "草津温泉", "草津", "伊香保", "水上", "みなかみ", "万座温泉", "四万温泉", "尾瀬", "富岡製糸場", "榛名"],
    "埼玉県": ["埼玉県", "さいたま市", "大宮", "川越", "秩父", "長瀞", "所沢", "熊谷", "春日部"],
    "千葉県": ["千葉県", "千葉市", "成田", "船橋", "木更津", "館山", "銚子", "鴨川", "勝浦", "房総", "九十九里", "松戸", "柏市"],
    "東京都": ["東京都", "浅草", "秋葉原", "歌舞伎町", "新宿", "渋谷", "池袋", "原宿", "お台場", "スカイツリー", "東京駅", "上野", "新大久保", "吉祥寺", "高尾山", "奥多摩", "八丈島", "伊豆大島", "小笠原"],
    "神奈川県": ["神奈川県", "横浜", "みなとみらい", "中華街", "鎌倉", "江ノ島", "江の島", "湘南", "箱根", "小田原", "横須賀", "川崎市", "三浦半島", "湯河原"],
    "新潟県": ["新潟県", "新潟市", "長岡", "上越", "佐渡", "佐渡島", "魚沼", "越後湯沢", "燕三条", "弥彦", "清津峡"],
    "富山県": ["富山県", "富山市", "高岡", "黒部", "立山", "宇奈月温泉", "氷見", "五箇山", "富山ブラック"],
    "石川県": ["石川県", "金沢", "兼六園", "能登", "輪島", "和倉温泉", "加賀温泉", "山代温泉", "千里浜", "近江町市場"],
    "福井県": ["福井県", "福井市", "東尋坊", "永平寺", "敦賀", "越前", "恐竜博物館", "若狭", "芦原温泉"],
    "山梨県": ["山梨県", "甲府", "富士五湖", "河口湖", "山中湖", "富士吉田", "富士急", "清里", "勝沼", "ほったらかし温泉", "信玄餅", "ほうとう"],
    "長野県": ["長野県", "長野市", "善光寺", "松本市", "松本城", "軽井沢", "上高地", "白馬", "諏訪湖", "諏訪", "安曇野", "野沢温泉", "渋温泉", "別所温泉", "戸隠", "美ヶ原", "ビーナスライン"],
    "岐阜県": ["岐阜県", "岐阜市", "飛騨高山", "飛騨", "白川郷", "下呂温泉", "下呂", "奥飛騨", "郡上八幡", "多治見", "中津川", "馬籠", "養老", "大垣"],
    "静岡県": ["静岡県", "静岡市", "浜松", "熱海", "伊豆", "下田", "伊東", "修善寺", "沼津", "三島", "富士宮", "御殿場", "寸又峡", "浜名湖", "さわやか"],
    "愛知県": ["愛知県", "名古屋", "栄", "大須", "豊橋", "岡崎", "豊田", "犬山", "常滑", "知多", "渥美半島", "蒲郡", "日間賀島", "ジブリパーク"],
    "三重県": ["三重県", "伊勢", "伊勢神宮", "おかげ横丁", "鳥羽", "志摩", "鈴鹿", "四日市", "松阪", "伊賀", "熊野古道", "ナガシマ", "なばなの里"],
    "滋賀県": ["滋賀県", "大津", "琵琶湖", "彦根", "長浜", "近江八幡", "信楽", "メタセコイア並木", "ラコリーナ"],
    "京都府": ["京都府", "京都市", "嵐山", "祇園", "清水寺", "伏見稲荷", "天橋立", "伊根", "宇治", "貴船", "舞鶴"],
    "大阪府": ["大阪府", "大阪市", "道頓堀", "難波", "なんば", "梅田", "新世界", "通天閣", "USJ", "ユニバ", "堺市", "岸和田", "関空"],
    "兵庫県": ["兵庫県", "神戸", "三宮", "有馬温泉", "姫路", "城崎温泉", "淡路島", "明石", "宝塚", "竹田城", "赤穂", "六甲"],
    "奈良県": ["奈良県", "奈良市", "奈良公園", "東大寺", "春日大社", "吉野", "飛鳥", "明日香", "十津川", "洞川温泉", "法隆寺"],
    "和歌山県": ["和歌山県", "和歌山市", "白浜", "南紀白浜", "アドベンチャーワールド", "高野山", "那智の滝", "熊野本宮", "串本", "友ヶ島", "ホテル川久", "川久", "勝浦温泉"],
    "鳥取県": ["鳥取県", "鳥取市", "鳥取砂丘", "米子", "境港", "皆生温泉", "三朝温泉", "大山", "倉吉", "水木しげる"],
    "島根県": ["島根県", "松江", "出雲", "出雲大社", "玉造温泉", "石見銀山", "津和野", "隠岐", "宍道湖"],
    "岡山県": ["岡山県", "岡山市", "倉敷", "美観地区", "児島", "蒜山", "湯原温泉", "津山", "牛窓", "備前"],
    "広島県": ["広島県", "広島市", "宮島", "厳島神社", "尾道", "しまなみ海道", "呉市", "福山市", "鞆の浦", "大久野島", "ウサギ島", "竹原"],
    "山口県": ["山口県", "山口市", "下関", "唐戸市場", "角島", "元乃隅神社", "秋吉台", "秋芳洞", "萩市", "岩国", "錦帯橋", "湯田温泉"],
    "徳島県": ["徳島県", "徳島市", "鳴門", "祖谷", "かずら橋", "大歩危", "阿波おどり", "阿波踊り"],
    "香川県": ["香川県", "高松", "丸亀", "琴平", "金刀比羅宮", "こんぴら", "小豆島", "直島", "父母ヶ浜", "うどん巡り", "讃岐うどん"],
    "愛媛県": ["愛媛県", "松山市", "道後温泉", "道後", "今治", "宇和島", "下灘駅", "内子", "佐田岬"],
    "高知県": ["高知県", "高知市", "ひろめ市場", "桂浜", "四万十川", "四万十", "足摺岬", "室戸岬", "仁淀川", "柏島", "龍河洞"],
    "福岡県": ["福岡県", "福岡市", "博多", "天神", "中洲", "北九州", "門司港", "小倉", "太宰府", "糸島", "久留米", "柳川", "宗像"],
    "佐賀県": ["佐賀県", "佐賀市", "嬉野温泉", "武雄温泉", "唐津", "呼子", "吉野ヶ里", "有田", "伊万里", "祐徳稲荷"],
    "長崎県": ["長崎県", "長崎市", "佐世保", "ハウステンボス", "雲仙", "島原", "平戸", "五島列島", "五島", "壱岐", "対馬", "稲佐山", "軍艦島"],
    "熊本県": ["熊本県", "熊本市", "阿蘇", "黒川温泉", "天草", "水前寺", "人吉", "杖立温泉", "草千里"],
    "大分県": ["大分県", "大分市", "別府", "湯布院", "由布院", "九重", "中津", "竹田", "国東", "高崎山", "地獄めぐり"],
    "宮崎県": ["宮崎県", "宮崎市", "高千穂", "青島", "日南", "サンメッセ日南", "都城", "延岡", "えびの高原", "鵜戸神宮"],
    "鹿児島県": ["鹿児島県", "鹿児島市", "桜島", "指宿", "霧島", "屋久島", "奄美大島", "奄美", "与論島", "種子島", "知覧", "仙巌園", "天文館"],
    "沖縄県": ["沖縄県", "沖縄", "那覇", "国際通り", "美ら海", "恩納村", "名護", "北谷", "アメリカンビレッジ", "首里城", "古宇利島", "石垣島", "宮古島", "竹富島", "西表島", "小浜島", "波照間島", "与那国島", "久米島", "座間味", "渡嘉敷", "ハレクラニ"],
}

# ---------------------------------------------------------------------------
# 2. Overseas Regions & Countries Dictionary
# ---------------------------------------------------------------------------
OVERSEAS_COUNTRIES: list[dict[str, Any]] = [
    # 東アジア
    {"id": "korea", "name": "韓国", "region": "アジア", "flag": "🇰🇷", "keywords": ["韓国", "ソウル", "釜山", "プサン", "チェジュ", "済州島", "明洞", "ホンデ", "弘大"]},
    {"id": "taiwan", "name": "台湾", "region": "アジア", "flag": "🇹🇼", "keywords": ["台湾", "台北", "九份", "十分", "台中", "高雄", "台南", "夜市"]},
    {"id": "china", "name": "中国", "region": "アジア", "flag": "🇨🇳", "keywords": ["中国旅行", "中国の夜", "中国🇨🇳", "#中国", "上海", "広州", "深圳", "成都", "北京", "中国・香港"]},
    {"id": "hongkong", "name": "香港", "region": "アジア", "flag": "🇭🇰", "keywords": ["香港", "#香港"]},
    {"id": "macau", "name": "マカオ", "region": "アジア", "flag": "🇲🇴", "keywords": ["マカオ", "#マカオ"]},
    # 東南アジア
    {"id": "thailand", "name": "タイ", "region": "アジア", "flag": "🇹🇭", "keywords": ["タイ旅行", "タイの", "タイ山奥", "タイで", "タイ名物", "タイ最終日", "タイにて", "タイ・", "#タイ", "バンコク", "チェンマイ", "コムローイ", "プーケット", "パタヤ", "カオサン", "水かけ祭り", "ソンクラーン", "首長族"]},
    {"id": "laos", "name": "ラオス", "region": "アジア", "flag": "🇱🇦", "keywords": ["ラオス", "#ラオス", "ビエンチャン", "バンビエン", "ルアンパバーン", "世界で最も何もない首都"]},
    {"id": "cambodia", "name": "カンボジア", "region": "アジア", "flag": "🇰🇭", "keywords": ["カンボジア", "#カンボジア", "アンコールワット", "シェムリアップ", "プノンペン", "キリングフィールド"]},
    {"id": "vietnam", "name": "ベトナム", "region": "アジア", "flag": "🇻🇳", "keywords": ["ベトナム", "#ベトナム", "ダナン", "#ダナン", "ホイアン", "#ホイアン", "ハノイ", "ホーチミン", "世界一物価の安い国"]},
    {"id": "singapore", "name": "シンガポール", "region": "アジア", "flag": "🇸🇬", "keywords": ["シンガポール", "マーライオン", "マリーナベイ"]},
    # 南アジア・インド洋
    {"id": "srilanka", "name": "スリランカ", "region": "アジア", "flag": "🇱🇰", "keywords": ["スリランカ", "#スリランカ", "シーギリヤ", "キャンディ", "コロンボ"]},
    {"id": "india", "name": "インド", "region": "アジア", "flag": "🇮🇳", "keywords": ["インド1日目", "インド列車", "インド旅行", "インド行ってくる", "#インド", "ニューデリー", "バラナシ", "タージマハル"]},
    {"id": "maldives", "name": "モルディブ", "region": "アジア", "flag": "🇲🇻", "keywords": ["モルディブ", "#モルディブ", "水中レストラン"]},
    # 中央アジア・中東・コーカサス
    {"id": "uzbekistan", "name": "ウズベキスタン", "region": "中東・中央アジア", "flag": "🇺🇿", "keywords": ["ウズベキスタン", "#ウズベキスタン", "サマルカンド", "#サマルカンド", "タシュケント", "ブハラ"]},
    {"id": "uae", "name": "UAE（ドバイ）", "region": "中東・中央アジア", "flag": "🇦🇪", "keywords": ["ドバイ", "#ドバイ", "アブダビ"]},
    {"id": "georgia", "name": "ジョージア", "region": "中東・中央アジア", "flag": "🇬🇪", "keywords": ["ジョージア", "トビリシ", "99%の日本人が行かない親日国"]},
    {"id": "turkey", "name": "トルコ", "region": "中東・中央アジア", "flag": "🇹🇷", "keywords": ["トルコ", "#トルコ", "イスタンブール", "#イスタンブール", "カッパドキア", "#カッパドキア", "パムッカレ", "世界三大料理"]},
    # ヨーロッパ
    {"id": "italy", "name": "イタリア", "region": "ヨーロッパ", "flag": "🇮🇹", "keywords": ["イタリア", "#イタリア", "🇮🇹", "ベネチア", "ヴェネツィア", "ローマ", "ミラノ", "ナポリ", "フィレンツェ"]},
    {"id": "czechia", "name": "チェコ", "region": "ヨーロッパ", "flag": "🇨🇿", "keywords": ["チェコ", "プラハ", "#プラハ", "世界一のビール大国"]},
    {"id": "austria", "name": "オーストリア", "region": "ヨーロッパ", "flag": "🇦🇹", "keywords": ["オーストリア", "ウィーン", "#ウィーン", "ハルシュタット", "#ハルシュタット", "ザルツブルク"]},
    {"id": "slovakia", "name": "スロバキア", "region": "ヨーロッパ", "flag": "🇸🇰", "keywords": ["スロバキア", "ブラチスラバ", "日本人に全く人気ない未知の国"]},
    {"id": "hungary", "name": "ハンガリー", "region": "ヨーロッパ", "flag": "🇭🇺", "keywords": ["ハンガリー", "#ハンガリー", "ブダペスト", "消費税世界一の国"]},
    {"id": "slovenia", "name": "スロベニア", "region": "ヨーロッパ", "flag": "🇸🇮", "keywords": ["スロベニア", "#スロベニア", "リュブリャナ", "ポストイナ", "ブレッド湖", "崖の上の城"]},
    {"id": "croatia", "name": "クロアチア", "region": "ヨーロッパ", "flag": "🇭🇷", "keywords": ["クロアチア", "ドブロブニク", "ドゥブロヴニク", "魔女の宅急便", "ジブリ聖地"]},
    {"id": "greece", "name": "ギリシャ", "region": "ヨーロッパ", "flag": "🇬🇷", "keywords": ["ギリシャ", "サントリーニ", "アテネ", "夢のヨーロッパリゾート"]},
    {"id": "uk", "name": "イギリス", "region": "ヨーロッパ", "flag": "🇬🇧", "keywords": ["イギリス", "ロンドン", "#ロンドン"]},
    {"id": "iceland", "name": "アイスランド", "region": "ヨーロッパ", "flag": "🇮🇸", "keywords": ["アイスランド", "#アイスランド", "白夜の国", "ブルーラグーン", "レイキャビク"]},
    {"id": "portugal", "name": "ポルトガル", "region": "ヨーロッパ", "flag": "🇵🇹", "keywords": ["ポルトガル", "#ポルトガル", "リスボン", "ポルト"]},
    {"id": "spain", "name": "スペイン", "region": "ヨーロッパ", "flag": "🇪🇸", "keywords": ["スペイン", "#スペイン", "バルセロナ", "マドリード", "トマト祭り", "ブニョール", "サンセバスチャン", "サン・セバスチャン"]},
    {"id": "germany", "name": "ドイツ", "region": "ヨーロッパ", "flag": "🇩🇪", "keywords": ["ドイツ", "#ドイツ", "ドレスデン", "ミュンヘン", "フランクフルト", "クリスマスマーケット", "豚の生肉"]},
    {"id": "baltics", "name": "バルト三国", "region": "ヨーロッパ", "flag": "🇪🇪🇱🇻🇱🇹", "keywords": ["バルト三国", "バルト３国", "エストニア", "ラトビア", "リトアニア", "ヴィリニュス"]},
    {"id": "finland", "name": "フィンランド", "region": "ヨーロッパ", "flag": "🇫🇮", "keywords": ["フィンランド", "#フィンランド", "🇫🇮", "ロヴァニエミ", "サンタクロース村", "ヘルシンキ", "サンタさんに会いに", "サンタさんと会って"]},
    {"id": "switzerland", "name": "スイス", "region": "ヨーロッパ", "flag": "🇨🇭", "keywords": ["スイス", "#スイス", "ツェルマット", "グリンデルワルト", "マッターホルン", "チューリッヒ", "世界一物価の高い国"]},
    {"id": "france", "name": "フランス", "region": "ヨーロッパ", "flag": "🇫🇷", "keywords": ["フランス旅行", "フランスの", "フランスで", "フランスの中", "#フランス", "パリ3泊", "パリで", "#パリ", "モン・サン・ミシェル", "モンサンミシェル", "コルマール", "ボルドー", "ニース", "ストラスブール"]},
    {"id": "monaco", "name": "モナコ", "region": "ヨーロッパ", "flag": "🇲🇨", "keywords": ["モナコ", "フランスの中にある超お金持ちの独立国"]},
    # アフリカ
    {"id": "namibia", "name": "ナミビア（アフリカ）", "region": "アフリカ", "flag": "🇳🇦", "keywords": ["ナミビア", "#ナミビア", "アフリカ車旅", "アフリカで", "#アフリカ", "ヒンバ族", "キリンの肉"]},
    {"id": "morocco", "name": "モロッコ", "region": "アフリカ", "flag": "🇲🇦", "keywords": ["モロッコ", "#モロッコ", "サハラ砂漠", "シャウエン", "#シャウエン", "フェズ", "マラケシュ", "迷宮都市", "世界でウザいと有名な国"]},
    # オセアニア・北米
    {"id": "newzealand", "name": "ニュージーランド", "region": "オセアニア・北米", "flag": "🇳🇿", "keywords": ["ニュージーランド", "#ニュージーランド", "クイーンズタウン", "テカポ", "世界最南端のマック"]},
    {"id": "hawaii", "name": "アメリカ（ハワイ）", "region": "オセアニア・北米", "flag": "🇺🇸", "keywords": ["ハワイ", "ホノルル", "ワイキキ", "ハワイアン航空"]},
]

# Explicit video-to-country overrides for ambiguous titles
EXPLICIT_VIDEO_COUNTRIES: dict[str, list[str]] = {
    "YAN3VAPytZA": ["ラオス", "タイ"],
    "7j3RkG8bQNU": ["タイ"],
    "W5_j6xm_XOc": ["タイ"],
    "Jev865yc9BE": ["タイ"],
    "8gjw6ivldZw": ["ベトナム"],
    "3qIhAzinqzM": ["ベトナム"],
    "CbCNp9oYksY": ["モルディブ"],
    "oPaHFz6rdAc": ["ニュージーランド", "ウズベキスタン"],
    "zPQhpkGgt5o": ["ウズベキスタン"],
    "31PUVJm3DzI": ["ジョージア"],
    "XAohojN2ESQ": ["イタリア"],
    "bgsdTmgg9Z0": ["イタリア"],
    "BvS87txPyZY": ["イタリア"],
    "on6DiV_woyc": ["イタリア"],
    "xu4VZWeLf2I": ["チェコ", "ドイツ"],
    "hs9bVMAFAfA": ["スロバキア"],
    "wMIAQNIquUk": ["ハンガリー"],
    "tYTqMuCku60": ["ハンガリー"],
    "TNlA0CWWKZs": ["スロベニア"],
    "d2ULf1YATzc": ["クロアチア"],
    "wFAOtFxs65k": ["クロアチア", "ギリシャ"],
    "3ygqbq96h6c": ["ギリシャ"],
    "r-7VHxl_1Zw": ["ギリシャ"],
    "qYt98kXtCpg": ["韓国"],
    "l6ObtIQ09SU": ["アイスランド"],
    "nWcJFzdigSk": ["アイスランド"],
    "9ABTeeSZao8": ["アイスランド"],
    "zBk01vaVevQ": ["アイスランド"],
    "cYWRMyOXmrw": ["アイスランド"],
    "SpIrftzat3k": ["ポルトガル", "スペイン"],
    "vc_4X4on2Ng": ["ナミビア（アフリカ）"],
    "d8jcT2kd190": ["ナミビア（アフリカ）"],
    "YlG9pSG55RU": ["ナミビア（アフリカ）"],
    "K5h2wEkoAZM": ["スイス"],
    "PNGtLjEClLw": ["スイス"],
    "214PBZA0y7A": ["スイス"],
    "oth1iljr--c": ["スイス"],
    "fZGfRUsBTH8": ["モナコ", "フランス"],
    "N4Ak1EoB3tI": ["モロッコ"],
    "FSnrLFqEPLk": ["フランス"],
    "uruqUSGYkCI": ["ドイツ", "フランス"],
    "MF6eImvDT3g": ["モロッコ"],
}


# ---------------------------------------------------------------------------
# 3. Honeymoon Seasons Definition
# ---------------------------------------------------------------------------
HONEYMOON_SEASONS_META: list[dict[str, Any]] = [
    {
        "id": "hm_season6",
        "season_number": 6,
        "title": "ハネムーン Season 6",
        "subtitle": "スイス・フランス・モナコ・スペイン・モロッコ編",
        "period": "2026年8月 〜 2026年10月",
        "start_date": "2026-08-14",
        "end_date": "2026-10-18",
        "playlist_id": "PLFXwsWue-P6o",
        "countries": ["シンガポール", "スイス", "フランス", "モナコ", "スペイン", "モロッコ"],
        "description": "物価世界一のスイス絶景登山＆氷河特急から、フランス周遊（コルマール・パリ・モンサンミシェル・ボルドー・ニース）、モナコ、美食の街サンセバスチャン、そしてモロッコ（サハラ砂漠・迷宮都市フェズ・青い街シャウエン）へ！",
        "badge_color": "#0ea5e9",
    },
    {
        "id": "hm_season5",
        "season_number": 5,
        "title": "ハネムーン Season 5",
        "subtitle": "冬のドイツ・バルト三国・フィンランドオーロラ編",
        "period": "2025年12月",
        "start_date": "2025-12-08",
        "end_date": "2026-01-05",
        "playlist_id": "PLFsNadn7fRZ36mpkNOwWDIOCu6Z7LHT1z",
        "countries": ["ドイツ", "バルト三国", "フィンランド"],
        "description": "憧れのドイツ・ドレスデンのクリスマスマーケットから、真冬のバルト三国、そして氷点下30℃のフィンランドでサンタクロース村＆オーロラを追いかける冬のヨーロッパ旅！",
        "badge_color": "#6366f1",
    },
    {
        "id": "hm_season4",
        "season_number": 4,
        "title": "ハネムーン Season 4",
        "subtitle": "北欧アイスランド車中泊・ポルトガル・スペイン・アフリカ車旅編",
        "period": "2025年8月 〜 2025年10月",
        "start_date": "2025-08-23",
        "end_date": "2025-10-26",
        "playlist_id": "PLFsNadn7fRZ0GQIMUOMfSLosAzZFRnqT6",
        "countries": ["韓国", "アイスランド", "ポルトガル", "スペイン", "ナミビア（アフリカ）"],
        "description": "白夜の北欧アイスランド3000km車中泊旅から、美食のポルトガル、スペインのトマト祭り、そして規格外の大自然ナミビア（アフリカ）ルーフテント車旅へ！",
        "badge_color": "#10b981",
    },
    {
        "id": "hm_season3",
        "season_number": 3,
        "title": "ハネムーン Season 3",
        "subtitle": "ヨーロッパ大周遊編（イタリア・中欧・クロアチア・ギリシャ）",
        "period": "2025年3月 〜 2025年5月",
        "start_date": "2025-03-19",
        "end_date": "2025-05-23",
        "playlist_id": "PLFsNadn7fRZ0Jzyr5FCF7PbolgISN7XZy",
        "countries": ["イタリア", "チェコ", "オーストリア", "スロバキア", "ハンガリー", "スロベニア", "クロアチア", "ギリシャ", "イギリス"],
        "description": "イタリア（ミラノ・ベネチア・ローマ・ナポリ）からチェコ・オーストリア・スロバキア・ハンガリーの中欧周遊、さらにスロベニア・魔女の宅急便の聖地クロアチア・ギリシャのサントリーニ島まで巡る大冒険！",
        "badge_color": "#f59e0b",
    },
    {
        "id": "hm_season2",
        "season_number": 2,
        "title": "ハネムーン Season 2",
        "subtitle": "NZキャンピングカー旅・ウズベキスタン・ドバイ・ジョージア・トルコ編",
        "period": "2024年11月 〜 2024年12月",
        "start_date": "2024-11-01",
        "end_date": "2024-12-26",
        "playlist_id": "PLFsNadn7fRZ2Lytcqdgr7ZG4oWFSPr0MI",
        "countries": ["ニュージーランド", "ウズベキスタン", "UAE（ドバイ）", "ジョージア", "トルコ"],
        "description": "ニュージーランド3000km車中泊旅から、青の都ウズベキスタン鉄道旅、超セレブ都市ドバイ、親日国ジョージア、そしてイスタンブール＆カッパドキアを巡るトルコ旅！",
        "badge_color": "#ec4899",
    },
    {
        "id": "hm_season1",
        "season_number": 1,
        "title": "ハネムーン Season 1",
        "subtitle": "東アジア・東南アジア・スリランカ・インド・モルディブ編",
        "period": "2024年3月 〜 2024年7月",
        "start_date": "2024-03-15",
        "end_date": "2024-08-05",
        "playlist_id": "PLFsNadn7fRZ3uMK9BD_WxRR1Up7SaTe7G",
        "countries": ["中国", "香港", "マカオ", "ラオス", "タイ", "カンボジア", "ベトナム", "スリランカ", "インド", "モルディブ"],
        "description": "世界一周ハネムーン開幕！中国・香港・マカオからラオス・タイ・カンボジア・ベトナムの東南アジア縦断、さらにスリランカ・カオスなインド列車旅を経て地上の楽園モルディブへ！",
        "badge_color": "#f97316",
    },
    {
        "id": "hm_season0",
        "season_number": 0,
        "title": "ハネムーン序章（結婚式後・沖縄＆タイ編）",
        "subtitle": "結婚式直後の沖縄リゾート＆タイ・コムローイ祭り旅",
        "period": "2023年11月 〜 2023年12月",
        "start_date": "2023-11-15",
        "end_date": "2023-12-23",
        "playlist_id": "",
        "countries": ["タイ"],
        "description": "結婚式を終えた直後の沖縄高級リゾート旅と、ラプンツェルのモデルになったタイ・チェンマイのコムローイ祭り＆寝台列車を巡るプレハネムーン旅！",
        "badge_color": "#8b5cf6",
    },
    {
        "id": "hm_extra",
        "season_number": -1,
        "title": "海外旅・番外編 ＆ ハネムーン総集編",
        "subtitle": "台湾旅・韓国旅・ハワイ旅・世界一周総集編まとめ",
        "period": "2023年 〜 2026年",
        "start_date": "",
        "end_date": "",
        "playlist_id": "PLFsNadn7fRZ0ORi0fmwVi2N1DlzEogFmD",
        "countries": ["台湾", "韓国", "アメリカ（ハワイ）", "ベトナム"],
        "description": "ハネムーン合間の夫婦海外旅行（2026年5月台湾縦断旅、韓国グルメ旅、念願のハワイ旅など）と、国別の長尺総集編ムービーまとめ！",
        "badge_color": "#14b8a6",
    },
]


# Footer markers where everything after them (unless 【あーちゃん日記】 starts later) is boilerplate
FOOTER_CUTOFF_MARKERS = [
    "🛒とったびのグッズ販売",
    "👫ゆるvlogのサブch",
    "👫サブチャンネルはこちら",
    "🚐ふたりの家(車)ができるまで",
    "☝️気になってることがほぼ全て解決する",
    "👇メインチャンネルはこちら",
    "✉️お手紙やプレゼントの宛先はこちら",
    "📨HP/ギャラリー",
    "📱ふたりの日常は、SNSにて更新中",
    "📚ふたりのフォトエッセイ",
]

BOILERPLATE_MARKERS = [
    "📷撮影機材・旅のバッグの中身",
    "サブチャンネルでラジオ始めました",
    "毎月15日更新",
    "👇お便り大募集",
    "tottabibiyori.radio@gmail.com",
    "🎉「とったびランド",
    "＜詳細/チケット申込はこちら＞",
    "カップルで軽キャンに乗って日本一周",
    "チャンネル登録よろしくお願いします",
    "SNSもフォロー",
    "Twitter",
    "Instagram",
    "BGM",
    "効果音",
    "お仕事のご依頼",
    "ファンレター",
    "プレゼントの送り先",
    "〒107",
    "東京都港区赤坂",
    "ミッドタウン・タワー",
    "UUUM株式会社",
    "撮って 笑って 旅をして宛",
    "危険物・飲食物・現金はお受取りできません",
]


def clean_description_for_analysis(desc: str) -> tuple[str, str, list[str]]:
    """
    Return (clean_text_for_location, diary_or_summary_excerpt, hashtags).
    Strips boilerplate event/merch/social blocks so event venue lists don't pollute location tags.
    """
    if not desc:
        return "", "", []

    hashtags = re.findall(r"[#＃]([^\s#＃　]+)", desc)
    lines = desc.splitlines()
    clean_lines: list[str] = []
    diary_lines: list[str] = []
    in_boilerplate_block = False
    in_diary_block = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        if "【あーちゃん日記】" in line or "今日の気まぐれ一言" in line or "今日の一言" in line:
            in_boilerplate_block = False
            in_diary_block = True
            cleaned_header = re.sub(r"^(【あーちゃん日記】|今日の気まぐれ一言)[:：]?\s*", "", line)
            if cleaned_header:
                diary_lines.append(cleaned_header)
                clean_lines.append(cleaned_header)
            continue

        if any(m in line for m in FOOTER_CUTOFF_MARKERS) or "とったびランド" in line or "＜詳細/チケット申込はこちら＞" in line:
            in_boilerplate_block = True
            in_diary_block = False
            continue

        if in_boilerplate_block:
            if line.startswith("#") or line.startswith("＃"):
                in_boilerplate_block = False
            else:
                continue

        if any(marker in line for marker in BOILERPLATE_MARKERS):
            in_diary_block = False
            continue
        if line.startswith("http://") or line.startswith("https://") or line.startswith("→http") or line.startswith("→ http") or line.startswith("・"):
            continue
        if re.match(r"^[ー\-━＝=_]{4,}$", line):
            in_diary_block = False
            continue

        if in_diary_block:
            diary_lines.append(line)

        clean_lines.append(line)

    clean_text = "\n".join(clean_lines)
    if diary_lines:
        excerpt = " ".join(diary_lines)[:180]
    else:
        non_hash = [l for l in clean_lines if not l.startswith("#") and not l.startswith("＃")]
        excerpt = " ".join(non_hash)[:180]

    return clean_text, excerpt, hashtags


def detect_locations(
    vid: str,
    title: str,
    clean_desc: str,
    hashtags: list[str],
    playlist_titles: list[str],
    publish_date: str = "",
) -> tuple[list[str], list[str], list[str], str]:
    """
    Returns (prefectures, japan_regions, overseas_countries, location_scope)
    where location_scope is 'overseas', 'domestic', 'both', or 'other'.
    """
    search_primary = f"{title} {' '.join('#' + h for h in hashtags)}"
    desc_head = clean_desc[:500]
    combined_text = f"{search_primary}\n{desc_head}"

    # 1. Overseas countries detection (only for videos from 2023-11-15 onwards, when their overseas travel began)
    detected_countries: list[str] = []
    if not publish_date or publish_date >= "2023-11-15":
        if vid in EXPLICIT_VIDEO_COUNTRIES:
            detected_countries.extend(EXPLICIT_VIDEO_COUNTRIES[vid])

        for c_meta in OVERSEAS_COUNTRIES:
            c_name = c_meta["name"]
            if c_name in detected_countries:
                continue
            for kw in c_meta["keywords"]:
                if kw in search_primary or kw in desc_head:
                    if c_meta["id"] == "china" and ("中国地方" in combined_text or "鳥取" in combined_text or "島根" in combined_text or "岡山" in combined_text or "広島" in combined_text or "山口" in combined_text):
                        continue
                    detected_countries.append(c_name)
                    break

    # 2. Check regional playlists first so we know which domestic regions this video belongs to
    detected_regions: list[str] = []
    for pl_t in playlist_titles:
        if "日本一周旅" in pl_t:
            for reg in JAPAN_REGIONS:
                for pkw in reg["playlist_keywords"]:
                    if pkw in pl_t and reg["name"] not in detected_regions:
                        detected_regions.append(reg["name"])

    # 3. Domestic prefectures detection
    detected_prefs: list[str] = []

    # Explicit pattern: "日本一周...日目は○○(県|府|都|道)"
    m_day = re.search(r"日本一周\d+日目は\s*([^\s/／！!]+?[都道府県])", clean_desc)
    if m_day:
        p_cand = m_day.group(1)
        if p_cand in PREF_TO_REGION:
            detected_prefs.append(p_cand)

    masked_text = combined_text.replace("東京都", "___TOKYO___").replace("東京", "___TOKYO_SHORT___")

    for pref, kws in PREFECTURE_KEYWORDS.items():
        if pref in detected_prefs:
            continue
        check_target = title if (detected_countries and pref != "沖縄県") else (combined_text if pref == "東京都" else masked_text)
        for kw in kws:
            if kw in check_target:
                detected_prefs.append(pref)
                break

    # Also check short prefecture names in title, hashtags, or within matching regional playlists
    for pref, reg_name in PREF_TO_REGION.items():
        if pref in detected_prefs:
            continue
        short_pref = pref[:-1] if pref != "北海道" else "北海道"
        if short_pref in ("東京", "京都", "大阪"):
            if short_pref == "東京" and "東京" in title:
                detected_prefs.append("東京都")
            elif short_pref == "京都" and "京都" in title.replace("東京都", ""):
                detected_prefs.append("京都府")
            elif short_pref == "大阪" and "大阪" in title:
                detected_prefs.append("大阪府")
            continue

        # Avoid matching common words like 大分 (daibu), 三重 (sanjū) unless in title/regional context
        if short_pref in ("大分", "三重", "岩手", "山形", "香川", "佐賀") and reg_name not in detected_regions and short_pref not in title and short_pref not in hashtags:
            continue

        if (
            short_pref in title
            or short_pref in hashtags
            or (reg_name in detected_regions and short_pref in clean_desc)
            or re.search(rf"{re.escape(short_pref)}(?:旅|旅行|グルメ|車中泊|観光|県|一周|上陸|編|の夜|の宿|の朝)", combined_text)
        ):
            if not detected_countries or short_pref in title:
                detected_prefs.append(pref)

    for pl_t in playlist_titles:
        if "日本一周旅" in pl_t:
            if "北海道" in pl_t and "北海道" not in detected_prefs:
                detected_prefs.append("北海道")
            if "沖縄" in pl_t and "沖縄県" not in detected_prefs and "鹿児島県" not in detected_prefs:
                detected_prefs.append("沖縄県")

    for pref in detected_prefs:
        reg_name = PREF_TO_REGION.get(pref)
        if reg_name and reg_name not in detected_regions:
            detected_regions.append(reg_name)

    if detected_countries and detected_prefs:
        scope = "both"
    elif detected_countries:
        scope = "overseas"
    elif detected_prefs or detected_regions:
        scope = "domestic"
    else:
        scope = "other"

    return detected_prefs, detected_regions, detected_countries, scope


def assign_honeymoon_season(
    vid: str,
    title: str,
    clean_desc: str,
    publish_date: str,
    playlist_ids: list[str],
    playlist_titles: list[str],
    overseas_countries: list[str],
) -> tuple[str | None, str | None]:
    """
    Return (honeymoon_season_id, honeymoon_season_title) if the video belongs to a Honeymoon season
    (either main channel or sub-channel 'とったび日和' filmed during that season!).
    """
    # 1. Check direct membership in official Honeymoon season playlists
    for hm in HONEYMOON_SEASONS_META:
        if hm["playlist_id"] and hm["playlist_id"] in playlist_ids and hm["id"] != "hm_extra":
            return hm["id"], hm["title"]

    # Dynamic check if a future "ハネムーンseason7" playlist is created on YouTube
    for pl_t in playlist_titles:
        m = re.search(r"ハネムーン.*season\s*([0-9０-９]+)", pl_t, re.IGNORECASE)
        if m:
            s_num = m.group(1).translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            return f"hm_season{s_num}", f"ハネムーン Season {s_num}"

    # 2. Explicit mappings for special Honeymoon videos (e.g. NZ vanlife in Season 2, post-season hauls/guides in Biyori)
    explicit_season_map = {
        # Season 6 sub-channel & extras
        "v40Q88-4RZE": "hm_season6",  # ハネムーンで信じられないくらいお土産買ってきた
        "ecmXAO0MOZQ": "hm_season6",  # シンガポール
        "PNGtLjEClLw": "hm_season6",  # スイス マック shorts
        "iSucAeOA3UY": "hm_season6",  # スイスの川 shorts
        "214PBZA0y7A": "hm_season6",  # スイス マック shorts
        "waEqy31bckk": "hm_season6",  # フランス マック shorts
        # Season 5 extras
        "CmjqeAfYpto": "hm_season5",  # さらば日本 サンタさんに会いにいきます
        "OeP0n2YIP0Y": "hm_season5",  # 海外のマック shorts
        "e4hL_sU4Wts": "hm_season5",  # フィンランドのマック shorts
        # Season 4 extras & Biyori retrospectives
        "jMUXtpMr6yo": "hm_season4",  # 新婚旅行は念願のあの国を車旅してきます
        "cMMIhW1xRMI": "hm_season4",  # 韓国グルメ (Season 4 出国直後)
        "ZO9NPlcpZVg": "hm_season4",  # 海外で豪華すぎるマクドナルド
        "F880bqDWSdQ": "hm_season4",  # アイスランド車旅の攻略法 (とったび日和)
        "AxtjGnUpJv4": "hm_season4",  # アフリカで食べた銃弾の件について (とったび日和)
        # Season 3 extras & Biyori retrospectives
        "4A6ltghm5o0": "hm_season3",  # 新婚旅行は妻念願の"あの国"へ行きます
        "BvS87txPyZY": "hm_season3",  # ローマ旅行で妻がやらかしました
        "CTb6tj7i62w": "hm_season3",  # 世界一美食の国のマック
        "tYTqMuCku60": "hm_season3",  # 世界一美しいマック
        "6xrWIND35LQ": "hm_season3",  # ベネチアの仮面 (とったび日和)
        "r-7VHxl_1Zw": "hm_season3",  # 雨のリゾートで真剣勝負 (とったび日和)
        # Season 2 NZ vanlife & Biyori retrospectives
        "AXCNWFmAgKQ": "hm_season2",  # 次の新婚旅行の行き先が決まりました
        "LWDx_kevSP8": "hm_season2",  # ニュージーランド車中泊旅 1
        "5hd3mEn77DM": "hm_season2",  # ニュージーランド車中泊旅 2
        "Yxbl2t-KnBc": "hm_season2",  # 世界最南端のマック shorts
        "VTnYVOIBT1Q": "hm_season2",  # ニュージーランド車中泊旅 3
        "Mze1iL1Uu34": "hm_season2",  # 作業用BGM in ニュージーランド
        "EZbuvy-gJ88": "hm_season2",  # ニュージーランド車中泊旅 4
        "8iOPRIJIY5s": "hm_season2",  # ニュージーランド車中泊旅 5
        "zPQhpkGgt5o": "hm_season2",  # ウズベキスタン砂漠
        "_HYJWMI2BnU": "hm_season2",  # 海外のマック shorts
        "Hr5LGUSDS0o": "hm_season2",  # トルコアイス屋 shorts
        "S4ORDG46s6k": "hm_season2",  # 海外で2000円超えマック shorts
        "L36R45lwZbM": "hm_season2",  # トルコ土産紹介 (とったび日和)
        "n3D5OkEUPRY": "hm_season2",  # ドバイを感じた出来事 (とったび日和)
        "YCTNJoS2090": "hm_season2",  # ニュージーランド車旅の攻略法 (とったび日和)
        # Season 1 extras
        "rQWa9TN04cE": "hm_season1",  # 新婚旅行の行き先が決まりました
        "3F2oNMxyQsg": "hm_season1",  # こんな新婚旅行ってアリ？
        "uEYKbRwI7L0": "hm_season1",  # 帰ってきたからとりあえず垢すり
        # Season 0 (Pre-honeymoon Okinawa & Thailand Dec 2023)
        "u6Ql-LyqCzY": "hm_season0",  # 【ハネムーン】高級リゾートに泊まってみた
        "_scFCgCBd5g": "hm_season0",  # とったび、ついに世界へいきます
        "heKRIxCQiJw": "hm_season0",  # 楽しみにしてた海外旅行が…
        "X8KVbAEsN90": "hm_season0",  # 旦那が海外でクレジットカード失くしました
        "jSNod5lYrH0": "hm_season0",  # 英語力0の妻が海外でスタバ注文したら
        "r8TiHNEyDRM": "hm_season0",  # タイの夜を体験したんだけど
        "GK53zFjsOjc": "hm_season0",  # タイの超人気ラーメン
        "bak4yz6aCjg": "hm_season0",  # タイのお祭り コムローイ
        "UBieJ03ywbI": "hm_season0",  # 3000円の寝台列車
        "YuqaWrqvev4": "hm_season0",  # タイで注文間違えてエビが2kg
        "y6ktygY_Ktc": "hm_season0",  # 3週間ぶりに日本帰国
        "FPyq3nqwkeQ": "hm_season0",  # 【総集編】タイ旅行
        "Kn1abDHLT5U": "hm_season0",  # タイ・コムローイ祭りの値段・行き方や攻略法 (とったび日和)
        "xGdXay5hqsM": "hm_season0",  # モフモフ天国 (とったび日和)
        "PrYGaNSCosk": "hm_season0",  # 象と過ごせるカフェ (とったび日和)
        "RGjDQLYHFis": "hm_season0",  # タイの温泉に突入 (とったび日和)
        "4KzTHGhswyE": "hm_season0",  # タイ名物のマンゴーご飯 (とったび日和)
        "6yqI0nELx-g": "hm_season0",  # タイ最終日の過ごし方 (とったび日和)
        "hoswdhC1eOg": "hm_season0",  # 画伯、タイにて新作をしたためる (とったび日和)
    }
    if vid in explicit_season_map:
        sid = explicit_season_map[vid]
        s_meta = next(h for h in HONEYMOON_SEASONS_META if h["id"] == sid)
        return sid, s_meta["title"]

    # 3. Check if video falls into a Season's date window AND has overseas/honeymoon relevance
    combined = f"{title} {clean_desc}"
    is_radio = "とったびラジオ" in playlist_titles or bool(re.search(r"[#＃][0-9０-９]{2}", title))
    is_compilation = "【総集編】" in title or "PLFsNadn7fRZ0ORi0fmwVi2N1DlzEogFmD" in playlist_ids

    if is_compilation and (overseas_countries or "PLFsNadn7fRZ0ORi0fmwVi2N1DlzEogFmD" in playlist_ids):
        return "hm_extra", "海外旅・番外編 ＆ ハネムーン総集編"

    if publish_date and not is_radio:
        for hm in HONEYMOON_SEASONS_META:
            if not hm["start_date"] or not hm["end_date"]:
                continue
            if hm["start_date"] <= publish_date <= hm["end_date"]:
                if (
                    overseas_countries
                    or any(kw in combined for kw in ["ハネムーン", "新婚旅行", "海外", "帰国", "時差ボケ", "フライト", "空港", "お土産", "パッキング", "砂漠", "進撃の巨人", "変質者"])
                ):
                    return hm["id"], hm["title"]

    # 4. Other overseas travel videos (e.g. Taiwan May 2026, Korea Mar 2025, Hawaii Oct 2024, Vietnam w/ guests)
    if overseas_countries and publish_date >= "2023-01-01":
        return "hm_extra", "海外旅・番外編 ＆ ハネムーン総集編"

    return None, None


def determine_primary_category(
    honeymoon_season_id: str | None,
    playlist_titles: list[str],
    title: str,
    video_type: str,
    location_scope: str,
) -> str:
    if honeymoon_season_id and honeymoon_season_id != "hm_extra":
        return "ハネムーン"
    if honeymoon_season_id == "hm_extra" or location_scope == "overseas":
        return "海外旅・総集編"
    if any("日本一周" in pt for pt in playlist_titles) or "日本一周" in title:
        return "日本一周旅"
    if any("中古一軒家DIY" in pt for pt in playlist_titles) or "一軒家" in title or "DIY" in title:
        return "マイホーム・DIY"
    if any("とったびラジオ" in pt for pt in playlist_titles) or bool(re.search(r"[『「].+[』」]\s*[#＃][0-9０-９]+", title)):
        return "とったびラジオ"
    if any("キャンプ" in pt or "秘湯・温泉" in pt or "グルメ企画" in pt for pt in playlist_titles) or "車中泊" in title:
        return "国内旅・車中泊・グルメ"
    if any("日常" in pt or "新生活" in pt for pt in playlist_titles):
        return "夫婦・カップルの日常"
    if video_type == "live" or "LIVE" in title:
        return "ライブ配信"
    if video_type == "short":
        return "ショート動画"
    return "日常・企画Vlog"


def build_enriched_dataset(raw_data: dict[str, Any] | None = None) -> dict[str, Any]:
    if raw_data is None:
        if not RAW_CACHE_PATH.exists():
            raise FileNotFoundError(f"Raw cache not found at {RAW_CACHE_PATH}")
        raw_data = json.loads(RAW_CACHE_PATH.read_text(encoding="utf-8"))

    raw_videos: dict[str, dict[str, Any]] = raw_data.get("videos") or {}
    raw_playlists: list[dict[str, Any]] = raw_data.get("playlists") or []
    player_details: dict[str, dict[str, Any]] = raw_data.get("player_details") or {}

    # Map video_id -> list of playlists it belongs to
    video_playlists: dict[str, list[dict[str, Any]]] = {}
    for pl in raw_playlists:
        for item in pl.get("items") or []:
            vid = item["id"]
            video_playlists.setdefault(vid, []).append(
                {
                    "id": pl["id"],
                    "title": pl["title"],
                    "position": item["position"],
                }
            )

    enriched_videos: list[dict[str, Any]] = []

    for vid, v_base in raw_videos.items():
        p_det = player_details.get(vid) or {}
        title = p_det.get("title") or v_base.get("title") or ""
        if not title or title in ("None", "[Private video]", "[Deleted video]", "非公開動画", "削除された動画"):
            continue

        description = p_det.get("description") or ""
        duration = int(p_det.get("duration") or v_base.get("duration") or 0)
        view_count = int(p_det.get("view_count") or 0)
        publish_date = p_det.get("publish_date") or ""
        publish_year = publish_date[:4] if len(publish_date) >= 4 else "不明"
        publish_month = publish_date[:7] if len(publish_date) >= 7 else "不明"

        pls = video_playlists.get(vid) or []
        pl_ids = [p["id"] for p in pls]
        pl_titles = [p["title"] for p in pls]

        clean_desc, excerpt, hashtags = clean_description_for_analysis(description)
        prefs, jp_regions, countries, loc_scope = detect_locations(
            vid, title, clean_desc, hashtags, pl_titles, publish_date
        )

        hm_id, hm_title = assign_honeymoon_season(
            vid, title, clean_desc, publish_date, pl_ids, pl_titles, countries
        )

        # If a video is in a Honeymoon season and has no country detected yet, try inferring from adjacent videos later
        vtype = v_base.get("video_type") or "video"
        if duration > 0 and duration <= 75 and ("#shorts" in title.lower() or "#shorts" in description.lower()):
            vtype = "short"

        category = determine_primary_category(hm_id, pl_titles, title, vtype, loc_scope)

        # Format human-readable duration
        if duration >= 3600:
            h = duration // 3600
            m = (duration % 3600) // 60
            s = duration % 60
            duration_str = f"{h}:{m:02d}:{s:02d}"
        else:
            m = duration // 60
            s = duration % 60
            duration_str = f"{m}:{s:02d}"

        enriched_videos.append(
            {
                "id": vid,
                "title": title,
                "description": description,
                "excerpt": excerpt,
                "hashtags": hashtags[:10],
                "channel_key": v_base["channel_key"],
                "channel_name": v_base["channel_name"],
                "video_type": vtype,
                "duration": duration,
                "duration_str": duration_str,
                "view_count": view_count,
                "publish_date": publish_date,
                "publish_year": publish_year,
                "publish_month": publish_month,
                "thumbnail": v_base["thumbnail"],
                "thumbnail_hq": v_base["thumbnail_hq"],
                "url": v_base["url"],
                "playlists": pls,
                "playlist_ids": pl_ids,
                "playlist_titles": pl_titles,
                "prefectures": prefs,
                "japan_regions": jp_regions,
                "overseas_countries": countries,
                "location_scope": loc_scope,
                "honeymoon_season_id": hm_id,
                "honeymoon_season_title": hm_title,
                "category": category,
            }
        )

    # Sort newest first by publish_date, then by upload_order
    enriched_videos.sort(
        key=lambda x: (x["publish_date"] or "0000-00-00", -raw_videos[x["id"]].get("upload_order", 0)),
        reverse=True,
    )

    # Build Honeymoon Seasons summary groups (chronological inside each season!)
    hm_groups: list[dict[str, Any]] = []
    for hm_meta in HONEYMOON_SEASONS_META:
        sid = hm_meta["id"]
        season_vids = [v for v in enriched_videos if v["honeymoon_season_id"] == sid]
        # Sort chronological (oldest -> newest) for season story order, except hm_extra which is newest first
        season_vids.sort(
            key=lambda x: (x["publish_date"] or "9999-99-99", x["id"]),
            reverse=(sid == "hm_extra"),
        )
        # Assign episode numbers within the season
        main_ep = 0
        sub_ep = 0
        for sv in season_vids:
            if sv["channel_key"] == "tottabi" and sv["video_type"] != "short":
                main_ep += 1
                sv["season_episode_label"] = f"本編 #{main_ep}"
            elif sv["channel_key"] == "tottabi_biyori" and sv["video_type"] != "short":
                sub_ep += 1
                sv["season_episode_label"] = f"日和 #{sub_ep}"
            else:
                sv["season_episode_label"] = "Shorts"

        hm_groups.append(
            {
                **hm_meta,
                "video_count": len(season_vids),
                "main_count": sum(1 for v in season_vids if v["channel_key"] == "tottabi"),
                "sub_count": sum(1 for v in season_vids if v["channel_key"] == "tottabi_biyori"),
                "video_ids": [v["id"] for v in season_vids],
            }
        )

    # Build aggregate stats for filters
    pref_counts: dict[str, int] = {p: 0 for reg in JAPAN_REGIONS for p in reg["prefectures"]}
    region_counts: dict[str, int] = {reg["name"]: 0 for reg in JAPAN_REGIONS}
    country_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    year_counts: dict[str, int] = {}

    for v in enriched_videos:
        for p in v["prefectures"]:
            pref_counts[p] = pref_counts.get(p, 0) + 1
        for r in v["japan_regions"]:
            region_counts[r] = region_counts.get(r, 0) + 1
        for c in v["overseas_countries"]:
            country_counts[c] = country_counts.get(c, 0) + 1
        cat = v["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1
        yr = v["publish_year"]
        if yr and yr != "不明":
            year_counts[yr] = year_counts.get(yr, 0) + 1

    overseas_with_counts = []
    for c_meta in OVERSEAS_COUNTRIES:
        cnt = country_counts.get(c_meta["name"], 0)
        if cnt > 0:
            overseas_with_counts.append({**c_meta, "count": cnt})

    dataset = {
        "updated_at": raw_data.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        "total_count": len(enriched_videos),
        "channels": {
            "tottabi": sum(1 for v in enriched_videos if v["channel_key"] == "tottabi"),
            "tottabi_biyori": sum(1 for v in enriched_videos if v["channel_key"] == "tottabi_biyori"),
        },
        "honeymoon_seasons": hm_groups,
        "japan_regions": [
            {
                "id": reg["id"],
                "name": reg["name"],
                "count": region_counts.get(reg["name"], 0),
                "prefectures": [
                    {"name": p, "count": pref_counts.get(p, 0)} for p in reg["prefectures"]
                ],
            }
            for reg in JAPAN_REGIONS
        ],
        "overseas_countries": overseas_with_counts,
        "categories": [
            {"name": k, "count": v}
            for k, v in sorted(category_counts.items(), key=lambda item: -item[1])
        ],
        "years": [
            {"year": k, "count": v}
            for k, v in sorted(year_counts.items(), key=lambda item: item[0], reverse=True)
        ],
        "playlists": [
            {
                "id": pl["id"],
                "title": pl["title"],
                "channel_key": pl["channel_key"],
                "channel_name": pl["channel_name"],
                "count": pl["count"],
                "video_ids": pl["video_ids"],
            }
            for pl in raw_playlists
            if pl.get("count", 0) > 0
        ],
        "videos": enriched_videos,
    }

    save_videos_dataset(dataset)
    return dataset


if __name__ == "__main__":
    ds = build_enriched_dataset()
    print(f"Total Enriched Videos: {ds['total_count']}")
    print("Channels:", ds["channels"])
    print("\n--- Honeymoon Seasons ---")
    for hm in ds["honeymoon_seasons"]:
        print(f"  {hm['title']} ({hm['subtitle']}): {hm['video_count']}本 (メイン:{hm['main_count']} / 日和:{hm['sub_count']})")
    print("\n--- Japan Regions ---")
    for r in ds["japan_regions"]:
        prefs_str = ", ".join(f"{p['name']}:{p['count']}" for p in r["prefectures"])
        print(f"  {r['name']} ({r['count']}本): {prefs_str}")
    print("\n--- Overseas Countries ---")
    for c in ds["overseas_countries"]:
        print(f"  {c['flag']} {c['name']} ({c['region']}): {c['count']}本")
    print("\n--- Categories ---")
    for cat in ds["categories"]:
        print(f"  {cat['name']}: {cat['count']}本")
