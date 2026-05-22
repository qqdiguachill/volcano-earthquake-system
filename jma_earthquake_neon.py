import requests
import xml.etree.ElementTree as ET
import psycopg2
from datetime import datetime

import os

DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# 建立表格（如果不存在）
cur.execute("""
CREATE TABLE IF NOT EXISTS EarthquakeReports(
    id SERIAL PRIMARY KEY,
    report_datetime TEXT,
    headline_text TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS EarthquakeIntensities (
    id SERIAL PRIMARY KEY,
    report_id INTEGER,
    intensity TEXT,
    area_name TEXT,
    FOREIGN KEY(report_id) REFERENCES EarthquakeReports(id)
)
""")

# 首頁 Feed
feed_url = "https://www.data.jma.go.jp/developer/xml/feed/eqvol_l.xml"
resp = requests.get(feed_url)
root = ET.fromstring(resp.content)

# Atom feed namespace
ns_feed = {"atom": "http://www.w3.org/2005/Atom"}

# 遍歷所有 entry
for entry in root.findall("atom:entry", ns_feed):
    title = entry.find("atom:title", ns_feed).text
    if title == "震度速報":   
        link = entry.find("atom:link", ns_feed).attrib["href"]
        updated_raw = entry.find("atom:updated", ns_feed).text

        # 整理時間格式：轉成 YYYY-MM-DD HH:MM:SS 原始格式: 2025-12-10T14:55:01Z
        # updated_dt = datetime.strptime(updated_raw, "%Y-%m-%dT%H:%M:%SZ")
        # updated = updated_dt.strftime("%Y-%m-%d %H:%M:%S")
        updated_dt = datetime.strptime(updated_raw, "%Y-%m-%dT%H:%M:%SZ")
        updated = updated_dt.strftime("%Y年%m月%d日 %H:%M:%S")

        # 進入內頁 XML
        resp_detail = requests.get(link)
        detail_root = ET.fromstring(resp_detail.content)

        ns = {"h": "http://xml.kishou.go.jp/jmaxml1/informationBasis1/"}

        # 1. 抓取 <Headline><Text>
        headline_text = detail_root.find(".//h:Headline/h:Text", ns).text


        cur.execute("""
                    SELECT id
                    FROM EarthquakeReports
                    WHERE report_datetime = %s
                    AND headline_text = %s
            """, (updated, headline_text))
        
        existing = cur.fetchone()
        if existing:
            report_id = existing[0]
        else:
            cur.execute("""
                        INSERT INTO EarthquakeReports
                        (report_datetime, headline_text)
                        VALUES (%s, %s)
                        RETURNING id
                    """, (updated, headline_text))
            report_id = cur.fetchone()[0]


        # 2. 抓取 <Information type="震度速報">
        info = detail_root.find(".//h:Information[@type='震度速報']", ns)
        for item in info.findall("h:Item", ns):
            kind = item.find("h:Kind/h:Name", ns).text
            for area in item.findall("h:Areas/h:Area", ns):
                name = area.find("h:Name", ns).text
                # 存入 EarthquakeIntensities
                cur.execute("""
                            SELECT 1
                            FROM EarthquakeIntensities
                            WHERE report_id = %s
                            AND intensity = %s
                            AND area_name = %s
                        """, (report_id, kind, name))
                exists = cur.fetchone()
                if not exists:
                    cur.execute("""
                                INSERT INTO EarthquakeIntensities
                                (report_id, intensity, area_name)
                                VALUES (%s, %s, %s)
                        """, (report_id, kind, name))

today = datetime.now().strftime("%Y-%m-%d")
print(f"=== {today} 的 JMA 資料已下載 ===")
conn.commit()
conn.close()