import re
import requests
import sqlite3
from flask import Flask, render_template, request, jsonify



app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

def clearData(url, strTemp):
    print(strTemp)
    
    strTemp = re.split(r'[ |,、]|-', strTemp)
    # 清理空
    strTemp = [x for x in strTemp if x != ""]
    # 连接到数据库，如果不存在，则创建一个新的数据库
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    print(strTemp)
    cursor.execute("INSERT INTO keyword (url, keyword) VALUES (?, ?)", (url, str(strTemp)))

    conn.commit()
    conn.close()
    return strTemp


def checkDom(url):
    # 连接到数据库，如果不存在，则创建一个新的数据库
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM `keyword` WHERE url ='" + url + "'")
    rows = cursor.fetchone()
    conn.close()
    if (rows):
        print(rows)
        return rows[1]
    
    payload = {}
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    domStr = response.text
    match = re.search(r'name="keywords" content="(.*?)"', domStr)
    if (match):
        matchTemp = match.group(1)
        print('[keywords]' + matchTemp)
        return clearData(url, matchTemp)
    match = re.search(r'name="description" content="(.*?)"', domStr)
    if (match):
        matchTemp = match.group(1)
        print('[description]' + matchTemp)
        return clearData(url, matchTemp)
    match = re.search(r'title>(.*?)</title', domStr)
    if (match):
        matchTemp = match.group(1)
        print('[title]' + matchTemp)
        return clearData(url, matchTemp)

@app.route('/webSite', methods=['POST'])
def post_example():
    # 获取 JSON 数据
    data = request.json

    # 获取 form 数据
    # data = request.form

    # 获取普通 POST 数据
    # value = request.form.get('key')

    # 对于本示例，我们只是将接收到的数据返回为 JSON 响应
    for key in data['urlList']:
        if (key.startswith("http")):
            keyWOrdData = checkDom(key)
    return jsonify({"data": keyWOrdData})

@app.route('/getValue', methods=['POST'])
def getValue():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM `keyword`")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"data": rows})

if __name__ == "__main__":
    app.run(debug=True)