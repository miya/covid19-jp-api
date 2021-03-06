import os
import requests
from time import sleep
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timedelta, timezone

service_account_key = {
  "type": os.environ.get("type"),
  "project_id":  os.environ.get("project_id"),
  "private_key_id":  os.environ.get("private_key_id"),
  "private_key": os.environ.get("private_key").replace("\\n", "\n"),
  "client_email":  os.environ.get("client_email"),
  "client_id": os.environ.get("client_id"),
  "auth_uri":  os.environ.get("auth_uri"),
  "token_uri":  os.environ.get("token_uri"),
  "auth_provider_x509_cert_url":  os.environ.get("auth_provider_x509_cert_url"),
  "client_x509_cert_url":  os.environ.get("client_x509_cert_url")
}

cred = credentials.Certificate(service_account_key)
firebase_admin.initialize_app(cred)
db = firestore.client()

# 都道府県の単位を合わせる用 東京 => 東京都
t = ["東京"]
f = ["大阪", "京都"]
k = [
    "青森", "岩手", "宮城", "秋田", "山形", "福島",
    "茨城", "栃木", "群馬", "埼玉", "千葉", "神奈川",
    "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜",
    "静岡", "愛知", "三重", "滋賀", "兵庫", "奈良", "和歌山",
    "鳥取", "島根", "岡山", "広島", "山口", "徳島", "香川",
    "愛媛", "高知", "福岡", "佐賀", "長崎", "熊本", "大分",
    "宮崎", "鹿児島", "沖縄"
]

# アップデート時間
jst = timezone(timedelta(hours=+9), "JST")
now = datetime.now(jst).strftime("%Y-%m-%d %H:%M")

# API
base_url = "https://covid19-japan-web-api.now.sh/api/v1/prefectures"

# 公開用dictionary
data_dic = {
    "detail": {
        "update": now,
        "data_source": base_url
    },
    "prefectures": {
        "": {
            "cases": 0,
            "deaths": 0
        }
    },
    "total": {
        "total_cases": 0,
        "total_deaths": 0
    }
}

def create_json():
    prefectures = {}
    json_dic = {}
    total_cases = 0
    total_deaths = 0
    cnt = 0

    for i in range(5):
        r = requests.get(base_url)
        s = r.status_code
        if s == 200:
            json_dic = r.json()
            break
        else:
            cnt += 1
            sleep(1)
        if cnt >= 4:
            print("データを取得できませんでした。")
            exit()

    for i in json_dic:

        # 都道府県名の単位の修正
        name_ja = i["name_ja"]
        if name_ja in t:
            i["name_ja"] = name_ja + "都"
        elif name_ja in f:
            i["name_ja"] = name_ja + "府"
        elif name_ja in k:
            i["name_ja"] = name_ja + "県"

        # 各都道府県の感染者数・死亡者数を加算
        total_cases += i["cases"]
        total_deaths += i["deaths"]

        # 都道府県名、感染者数、死亡者数を格納
        prefectures.update({
            i["name_ja"]: {
                "cases": i["cases"],
                "deaths": i["deaths"]
            }
        })

    # 公開用jsonにデータを格納
    data_dic.update({
        "prefectures": prefectures,
        "total": {
            "total_cases": total_cases,
            "total_deaths": total_deaths
        }
    })


if __name__ == "__main__":
    create_json()
    doc_num = str(datetime.now(jst).hour)
    db.collection("data").document(doc_num).set(data_dic)


