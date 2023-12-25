import requests
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("s1072768mis-firebase-adminsdk-t6iad-3e1e6e12ac.json")
firebase_admin.initialize_app(cred)


from flask import Flask, render_template, request
from datetime import datetime, timezone, timedelta




app = Flask(__name__)

@app.route("/")
def index():
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    homepage = "<h1>Python網頁</h1>"
    homepage += "<a href=/mis>MIS</a><br>"
    homepage += "<a href=/today>顯示日期時間</a><br>"
    homepage += "<a href=/welcome?nick=tcyang>傳送使用者暱稱</a><br>"
    homepage += "<a href=/about>簡介網頁</a><br>"
    homepage += "<br><a href=/movie>讀取開眼電影即將上映影片，寫入Firestore</a><br>" 
    homepage += "<a href =/spider>子青老師的課程名稱及網址</a><br>"
    homepage += "<a href=/search_movie>查詢開眼電影即將上映影片</a><br>"
    return homepage

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1>"

@app.route("/today")
def today():
    tz = timezone(timedelta(hours=+8))
    now = datetime.now(tz)
    return render_template("today.html", datetime = str(now))

@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    user = request.values.get("nick")
    return render_template("welcome.html", name=user)

@app.route("/about")
def about():
    return render_template("aboutme.html")

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")
    
@app.route("/movie")
def movie():
  url = "http://www.atmovies.com.tw/movie/next/"
  Data = requests.get(url)
  Data.encoding = "utf-8"
  sp = BeautifulSoup(Data.text, "html.parser")
  result=sp.select(".filmListAllX li")
  lastUpdate = sp.find("div", class_="smaller09").text[5:]

  for item in result:
    picture = item.find("img").get("src").replace(" ", "")
    title = item.find("div", class_="filmtitle").text
    movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
    hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
    show = item.find("div", class_="runtime").text.replace("上映日期：", "")
    show = show.replace("片長：", "")
    show = show.replace("分", "")
    showDate = show[0:10]
    showLength = show[13:]

    doc = {
        "title": title,
        "picture": picture,
        "hyperlink": hyperlink,
        "showDate": showDate,
        "showLength": showLength,
        "lastUpdate": lastUpdate
      }

    db = firestore.client()
    doc_ref = db.collection("電影").document(movie_id)
    doc_ref.set(doc)    
  return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate 

@app.route("/spider")
def spider():
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".team-box")
    info = ""
    for x in result:
        info += "<a href=" + x.find("a").get("href") + ">" + x.text + "</a><br>"
        info += x.find("a").get("href") + "<br><br>"
    return info
@app.route("/search_movie", methods=["POST","GET"])
def searchQ():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = ""
        db = firestore.client()     
        collection_ref = db.collection("電影")
        docs = collection_ref.order_by("showDate").get()
        for doc in docs:
            if MovieTitle in doc.to_dict()["title"]: 
                info += "片名：" + doc.to_dict()["title"] + "<br>" 
                info += "影片介紹：" + doc.to_dict()["hyperlink"] + "<br>"
                info += "片長：" + doc.to_dict()["showLength"] + " 分鐘<br>" 
                info += "上映日期：" + doc.to_dict()["showDate"] + "<br><br>"           
        return info
    else:  
        return render_template("input.html")
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    action =  req["queryResult"]["action"]       
    if(action == "category"):
        cond = req["queryResult"]["parameters"]["category"]
        keyword = req["queryResult"]["parameters"]["information"]
        info = "這裡是關於" + cond + "的全部料理" +"\n\n"
        if(keyword == "資訊"):
            db = firestore.client()
            collection_ref = db.collection("mcdonald")
            docs = collection_ref.get()
            found = False
            for doc in docs:
                dict = doc.to_dict()
                if cond in dict()["category"]:
                    found = True
                    info += "名稱：" +  dict()["name"] + "\n"
                    info += "價格：" +  dict()["price"]+ "\n\n"
            if not found:
                info += "沒有這東東，你要不要看看自己在寫甚麼？"

            
    elif(action == "order"):
        meal = req["queryResult"]["parameters"]["any"]
        info = ""
        db = firestore.client()
        collection_ref = db.collection("mcdonald")
        docs = collection_ref.get()
        found = False
        for doc in docs:
                if cond in doc.to_dict()["name"]:
                    found = True
                    info += "一份" + meal + "。請問您還需要什麼來增加自己的體脂？"
        if not found:
                info = "沒有這東東，你要不要看看自己在寫甚麼？"

    elif(action == "information"):
        meal = req["queryResult"]["parameters"]["any"]
        keyword = req["queryResult"]["parameters"]["information"]
        info = "您要查詢的是" + meal + "的" + information + "\n\n"
        collection_ref = db.collection("mcdonald")
        docs = collection_ref.get()
        for doc in docs:
                dict = doc.to_dict()
                if meal in doc.to_dict()["name"]:
                    found = True
                    info += "這些是" + cond + "的資訊。放心，我們不會放上卡洛里的。\n\n"
                    info += "類別：" + doc.to_dict["category"] + "\n"
                    info += "名稱：" + doc.to_dict["name"] + "\n"
                    info += "價格：" + doc.to_dict["price"] + "\n"       
        if not found:
                info = "沒有這東東，您要不要看看自己在寫甚麼？"
    return make_response(jsonify({"fulfillmentText": info}))

if __name__ == "__main__":
    app.run(debug=True)
