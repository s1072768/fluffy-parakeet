import requests
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("serviceAccountKey.json")
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
    action =  req.get("queryResult").get("action")
    if(action == "Order"):
        category = req.get("queryResult").get("parameters").get("Category")
        info = "您選擇的分類是："+ category + "\n"
        
        db = firestore.client()
        collection_ref = db.collection("Mcdonald")
        docs = collection_ref.get()
        result = ""
        for doc in docs:
            dict = doc.to_dict()
            if category in dict["category"]:
                result += "餐名：" + dict["name"] + "\n"
                result += "價格：" + dict["price"] + "\n"
        info += result

    elif(action == "MealChoice"):
        meal = req.get("queryResult").get("parameters").get("name")
        info = "您選擇的餐點是："+ meal + "\n"
        db = firestore.client()
        collection_ref = db.collection("Mcdonald")
        docs = collection_ref.get()
        result = ""
        for doc in docs:
            dict = doc.to_dict()
            if meal in dict["name"]:
                result += "分類：" + dict["category"] + "\n"
                result += "餐名：" + dict["name"] + "\n"
                result += "價格：" + dict["price"] + "\n\n"
                result += "是否還有其他需要的 ?\n"
        info += result
if __name__ == "__main__":
    app.run(debug=True)
