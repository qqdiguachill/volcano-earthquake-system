import requests
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime
import unicodedata

DB_NAME = "volcano.db"
XML_URL = "https://www.data.jma.go.jp/developer/xml/feed/eqvol_l.xml"
NS = {"atom": "http://www.w3.org/2005/Atom"}

# 火山名稱清單（略，保留你原本的 VOLCANO_NAMES）
VOLCANO_NAMES = [
    "桜島","西之島","雌阿寒岳","岩手山","浅間山","草津白根山（白根山（湯釜付近））",
    "薩摩硫黄島","諏訪之瀬島","霧島山（新燃岳）","硫黄島","アトサヌプリ","大雪山","十勝岳",
    "樽前山","倶多楽","有珠山","北海道駒ヶ岳","恵山","岩木山","八甲田山","十和田","秋田焼山",
    "秋田駒ヶ岳","鳥海山","栗駒山","蔵王山","吾妻山","安達太良山","磐梯山","那須岳","日光白根山",
    "新潟焼山","弥陀ヶ原","焼岳","乗鞍岳","御嶽山","白山","富士山","箱根山","伊豆東部火山群",
    "伊豆大島","新島","神津島","三宅島","八丈島","青ヶ島","草津白根山（本白根山）","九重山",
    "阿蘇山","雲仙岳","口永良部島","鶴見岳・伽藍岳","霧島山（御鉢）","霧島山（えびの高原（硫黄山）周辺）",
    "霧島山（大幡池）","知床硫黄山","羅臼岳","摩周丸山","恵庭岳","渡島大島","利尻山","羊蹄山",
    "ニセコ","天頂山","雄阿寒岳","茂世路岳","散布山","指臼岳","小田萌山","択捉焼山","択捉阿登佐岳",
    "ベルタルベ山","爺爺岳","羅臼山","泊山","ルルイ岳","恐山","八幡平","鳴子","燧ヶ岳","肘折","沼沢",
    "赤城山","榛名山","草津白根山","妙高山","伊豆鳥島","高原山","横岳","アカンダナ山","利島","御蔵島",
    "男体山","三瓶山","霧島山","開聞岳","中之島","阿武火山群","由布岳","福江火山群","米丸・住吉池",
    "池田・山川","口之島","硫黄鳥島"
]

def find_volcano_name(text: str) -> str:
    """從文字內容比對火山名稱"""
    if not text:
        return "empty"
    for name in VOLCANO_NAMES:
        if name in text:
            return name
    return "地震情報"

# === 初始化資料庫 ===
def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS eqvol (
        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        volcano_name TEXT,
        title TEXT,
        updated TEXT,
        link TEXT,
        content TEXT
    )
    """)
    conn.commit()
    
# === 清理空格 ===
def clean_content(text: str) -> str:
    """清理 content 欄位：全形空格轉半形，連續全形空格移除"""
    if not text:
        return text
    # 先把兩個連續的全形空格去掉
    text = text.replace("　　", "")
    # 再把單個全形空格換成半形空格
    text = text.replace("　", " ")
    return text
# === 清理a
def clean_title(title: str) -> str:
    if title and title.endswith("a"):
        return title[:-1]
    return title

# === JMA Feed 主程式 ===
# 火山報告
VOLCANO_REPORT_TITLES = [
    "噴火に関する火山観測報",
    "降灰予報（定時）",
    "推定噴煙流向報"
]

def jma(conn):
    response = requests.get(XML_URL)
    response.encoding = "utf-8"
    root = ET.fromstring(response.text)

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"=== {today} 的 JMA 資料已下載 ===")

    cursor = conn.cursor()
    for entry in root.findall("atom:entry", NS):
        raw_title = entry.find("atom:title", NS).text if entry.find("atom:title", NS) is not None else None
        title = clean_title(raw_title)
        updated = entry.find("atom:updated", NS).text if entry.find("atom:updated", NS) is not None else ""
        link = entry.find("atom:link", NS).attrib.get("href") if entry.find("atom:link", NS) is not None else ""
        content = entry.find("atom:content", NS).text if entry.find("atom:content", NS) is not None else ""

        if today in updated and link:
            try:
                dt = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
                updated_fmt = dt.strftime("%Y年%m月%d日 %H:%M")
            except Exception:
                updated_fmt = updated

            volcano_name = find_volcano_name(title + (content or ""))

            # print(f"標題: {title}")
            # print(f"更新時間: {updated_fmt}")
            # print(f"連結: {link}")
            # print(f"火山名稱: {volcano_name}")
            # print("-" * 40)

            # 火山報告名單
            if title in VOLCANO_REPORT_TITLES:
                # print(f" 火山報告：{title}")
                content_clean = clean_content(content)
                cursor.execute("""
                    INSERT INTO eqvol (volcano_name, title, updated, link, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (volcano_name, title, updated_fmt, link, content_clean))
                continue

            # 不寫入資料庫
            if volcano_name == "地震情報" and (title is None):
                # print("跳過存入volcano_name == '地震情報' and title is None")
                continue
            else:
                #火山資料（一般）
                content_clean = clean_content(content)
                cursor.execute("""
                INSERT INTO eqvol (volcano_name, title, updated, link, content)
                VALUES (?, ?, ?, ?, ?)
                """, (volcano_name, title, updated_fmt, link, content_clean))

    conn.commit()

# === 主流程 ===
def main():
    conn = sqlite3.connect(DB_NAME)
    init_db(conn)
    jma(conn)
    conn.close()

if __name__ == "__main__":
    main()
