import requests
import psycopg2
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup

import os
DATABASE_URL = os.getenv("DATABASE_URL")



BASE_URL = "https://tenki.jp"
headers = {"User-Agent": "Mozilla/5.0"}

# === 初始化資料庫 ===
def init_db(conn):
    cursor = conn.cursor()
    # 總表：火山清單 + 詳細資訊
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS volcano_list (
        id INTEGER PRIMARY KEY NOT NULL,         -- 使用網址中的數字作為主鍵
        level_name TEXT NOT NULL,
        volcano_name TEXT NOT NULL,
        url TEXT NOT NULL,
        level TEXT,
        latitude REAL,
        longitude REAL,
        elevation TEXT
    )
    """)
    # 活動表：所有火山的活動紀錄，外來鍵對應 volcano_list.id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS volcano_activity (
        id SERIAL PRIMARY KEY,
        volcano_id INTEGER NOT NULL,
        published TEXT,
        phenomenon TEXT,
        link TEXT,
        FOREIGN KEY(volcano_id) REFERENCES volcano_list(id)
    )
    """)
    conn.commit()

# === 抓火山清單 ===
def fetch_volcano_list():
    res = requests.get(BASE_URL + "/bousai/volcano/", headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    rows = soup.select("table.volcano-level-table tr")
    data = []
    td_count = 0
    for tr in rows:
        th = tr.find("th", class_="volcano-level-index-name")
        td = tr.find("td")
        if td:
            td_count += 1
            level_name = th.get_text(strip=True) if th else f"(第{td_count}格)"
            links = td.select("a")
            for a in links:
                name = a.get_text(strip=True)
                href = a.get("href")
                full_url = urljoin(BASE_URL, href)
                # 從 URL 抓出火山 ID
                volcano_id = int(re.search(r'/volcano/(\d+)/', full_url).group(1))
                data.append((volcano_id, level_name, name, full_url))
            if td_count >= 7:
                break
    return data

# === 抓火山詳細資訊 ===
def fetch_volcano_info(url):
    res = requests.get(url, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.select_one("table.volcano-forecast-info-table")
    rows = table.select("tr")

    level = None
    latitude = None
    longitude = None
    elevation = None

    for tr in rows:
        th = tr.find("th")
        td = tr.find("td")
        if not th or not td:
            continue
        label = th.get_text(strip=True)
        if "警戒レベル" in label:
            level = td.get_text(strip=True)
        elif "位置・標高" in label:
            for p in td.stripped_strings:
                if p.startswith("北緯"):
                    latitude = float(p.replace("北緯：", "").replace("度", ""))
                elif p.startswith("東経"):
                    longitude = float(p.replace("東経：", "").replace("度", ""))
                elif p.startswith("標高"):
                    elevation = p.replace("標高：", "")
    return level, latitude, longitude, elevation

# === 抓火山活動紀錄 ===
def fetch_volcano_activity(url):
    res = requests.get(url, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    rows = soup.select("#volcano-live-entries-list tr")
    data = []
    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if th and td:
            link = th.find("a")["href"]
            published = th.get_text(strip=True)
            phenomenon = td.get_text(strip=True)
            data.append({
                "published": published,
                "phenomenon": phenomenon,
                "link": urljoin(BASE_URL, link)
            })
    return data

# === 主流程 ===
def main():
    conn = psycopg2.connect(DATABASE_URL)
    init_db(conn)

    cursor = conn.cursor()
    volcanoes = fetch_volcano_list()
    for volcano_id, level_name, name, url in volcanoes:
        print(f"處理火山: {name} ({url})")
        level, lat, lon, elev = fetch_volcano_info(url)

        

        

        # 存入總表
        cursor.execute("""
                       INSERT INTO volcano_list
                        (id, level_name, volcano_name, url, level, latitude, longitude, elevation)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id)
                        DO UPDATE SET
                        level_name = EXCLUDED.level_name,
                        volcano_name = EXCLUDED.volcano_name,
                        url = EXCLUDED.url,
                        level = EXCLUDED.level,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        elevation = EXCLUDED.elevation
                """, (
                    volcano_id,
                    level_name,
                    name,
                    url,
                    level,
                    lat,
                    lon,
                    elev))


        # 存入活動表
        activities = fetch_volcano_activity(url)

        for act in activities:
            cursor.execute("""
                           SELECT 1
                           FROM volcano_activity
                           WHERE volcano_id = %s
                           AND published = %s
                           AND phenomenon = %s
                           AND link = %s
                    """,(
                        volcano_id,
                        act["published"],
                        act["phenomenon"],
                        act["link"]
                        ))
            exists = cursor.fetchone()
            if not exists:
                cursor.execute("""
                           INSERT INTO volcano_activity
                            (volcano_id, published, phenomenon, link)
                            VALUES (%s, %s, %s, %s)
                    """, (
                        volcano_id,
                        act["published"],
                        act["phenomenon"],
                        act["link"]
                        ))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()