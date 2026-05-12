from flask import Flask, render_template, request, jsonify

import sqlite3
import os

DB_NAME = "volcano.db"

app = Flask(__name__)

# 取得資料庫連線
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# 首頁：降灰情報（eqvol）

@app.route("/")
def index():
    filter_type = request.args.get("type", "")  # 取得下拉選單的值

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    if filter_type:
        rows = conn.execute("""
            SELECT *
            FROM eqvol
            WHERE title = ?
            ORDER BY id DESC
        """, (filter_type,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT *
            FROM eqvol
            ORDER BY id DESC
        """).fetchall()

    conn.close()

    return render_template("index.html",
                           title="降灰情報",
                           items=rows,
                           filter_type=filter_type)


# 火山等級頁面（valcano_list + valcano_activity）
@app.route("/volcano-levels")
def volcano_levels():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    # 排序順序
    order = [
        "レベル5(避難)",
        "居住地域厳重警戒",
        "レベル4(高齢者等避難)",
        "レベル3(入山規制)",
        "入山危険",
        "レベル2(火口周辺規制)",
        "火口周辺危険"
    ]

    case_sql = " ".join([f"WHEN ? THEN {i}" for i in range(len(order))])

    volcano_rows = conn.execute(f"""
        SELECT *
        FROM volcano_list
        ORDER BY CASE level_name
            {case_sql}
            ELSE 999 END
    """, order).fetchall()

    # 活動資料
    activity_rows = conn.execute("""
        SELECT *
        FROM volcano_activity
    """).fetchall()

    conn.close()

    return render_template("volcano_levels.html",
                           title="火山等級",
                           items=volcano_rows,
                           activities=activity_rows)



# 地震速報頁面（EarthquakeReports + EarthquakeIntensities）
@app.route("/earthquake")
def earthquake_page():
    conn = get_db_connection()

    reports = conn.execute("""
        SELECT *
        FROM EarthquakeReports
        ORDER BY id DESC
    """).fetchall()

    intensities = conn.execute("""
        SELECT *
        FROM EarthquakeIntensities
    """).fetchall()

    conn.close()

    return render_template("earthquake.html",
                           title="地震速報",
                           reports=reports,
                           intensities=intensities)
region_map = {
    # 北海道地方
    "北海道地方": "北海道地方",
    "道北": "北海道地方",
    "道東": "北海道地方",
    "道央": "北海道地方",
    "道南": "北海道地方",
    "根室地方": "北海道地方",
    "渡島地方": "北海道地方",
    "渡島地方東部": "北海道地方",
    "渡島地方西部": "北海道地方",

    # 東北地方
    "東北地方": "東北地方",
    "青森県": "東北地方",
    "岩手県": "東北地方",
    "宮城県": "東北地方",
    "秋田県": "東北地方",
    "山形県": "東北地方",
    "福島県": "東北地方",

    # 関東・甲信地方
    "関東・甲信地方": "関東・甲信地方",
    "東京都": "関東・甲信地方",
    "神奈川県": "関東・甲信地方",
    "埼玉県": "関東・甲信地方",
    "千葉県": "関東・甲信地方",
    "茨城県": "関東・甲信地方",
    "栃木県": "関東・甲信地方",
    "群馬県": "関東・甲信地方",
    "山梨県": "関東・甲信地方",
    "長野県": "関東・甲信地方",

    # 北陸地方
    "北陸地方": "北陸地方",
    "新潟県": "北陸地方",
    "富山県": "北陸地方",
    "石川県": "北陸地方",
    "福井県": "北陸地方",

    # 東海地方
    "東海地方": "東海地方",
    "愛知県": "東海地方",
    "岐阜県": "東海地方",
    "静岡県": "東海地方",
    "三重県": "東海地方",

    # 近畿地方
    "近畿地方": "近畿地方",
    "大阪府": "近畿地方",
    "兵庫県": "近畿地方",
    "京都府": "近畿地方",
    "滋賀県": "近畿地方",
    "奈良県": "近畿地方",
    "和歌山県": "近畿地方",

    # 中国地方
    "中国地方": "中国地方",
    "鳥取県": "中国地方",
    "島根県": "中国地方",
    "岡山県": "中国地方",
    "広島県": "中国地方",
    "山口県": "中国地方",

    # 四国地方
    "四国地方": "四国地方",
    "徳島県": "四国地方",
    "香川県": "四国地方",
    "愛媛県": "四国地方",
    "高知県": "四国地方",

    # 九州地方
    "九州地方": "九州地方",
    "福岡県": "九州地方",
    "佐賀県": "九州地方",
    "長崎県": "九州地方",
    "熊本県": "九州地方",
    "大分県": "九州地方",
    "宮崎県": "九州地方",
    "鹿児島県": "九州地方",

    # 沖縄地方
    "沖縄地方": "沖縄地方",
    "沖縄県": "沖縄地方",
}
# @app.route("/count")
# def count_page():
#     conn = get_db_connection()
#     reports = conn.execute("SELECT area_name FROM EarthquakeIntensities").fetchall()
#     conn.close()

#     region_counts = {}
#     for r in reports:
#         place = r["area_name"]
#         for key in region_map:
#             if key in place:
#                 region = region_map[key]
#                 region_counts[region] = region_counts.get(region, 0) + 1
#                 break

#     labels = list(region_counts.keys())
#     data = list(region_counts.values())

#     return render_template("count.html",
#                            title="地震統計",
#                            labels=labels,
#                            data=data)

@app.route("/count")
def count_page():
    conn = get_db_connection()
    reports = conn.execute("SELECT report_id, area_name FROM EarthquakeIntensities").fetchall()
    volcano_rows = conn.execute("SELECT published FROM volcano_activity").fetchall()
    conn.close()

    # 地震統計
    seen_reports = set()
    region_counts = {}
    for r in reports:
        report_id = r["report_id"]
        if report_id in seen_reports:
            continue
        seen_reports.add(report_id)
        place = r["area_name"]
        for key in region_map:
            if key in place:
                region = region_map[key]
                region_counts[region] = region_counts.get(region, 0) + 1
                break
    labels = list(region_counts.keys())
    data = list(region_counts.values())

    # 火山每日統計
    import re
    from collections import Counter
    daily_counts = Counter()
    for v in volcano_rows:
        pub = v["published"]
        m = re.search(r"(\d{4})年(\d{2})月(\d{2})日", pub)
        if m:
            date_str = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            daily_counts[date_str] += 1
    volcano_labels = list(daily_counts.keys())
    volcano_data = list(daily_counts.values())

    return render_template("count.html",
                           title="統計圖表",
                           labels=labels,
                           data=data,
                           volcano_labels=volcano_labels,
                           volcano_data=volcano_data)



@app.route("/api/eqvol")
def api_eqvol():
    conn = get_db_connection()

    rows = conn.execute("""
        SELECT id, volcano_name, title, updated, link, content
        FROM eqvol
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])

# 主程式
if __name__ == "__main__":
    print("Flask 正在使用資料庫：", os.path.abspath(DB_NAME))
    app.run(debug=True)