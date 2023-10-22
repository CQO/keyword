import re
import requests
import sqlite3
import json
import random
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify



app = Flask(__name__)
CORS(app)  # 默认允许所有域名进行跨域请求

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/page2')
def page2():
    return render_template('index2.html')

@app.route('/page3')
def page3():
    return render_template('index3.html')

def sendSMSTo(yzm, phone):
    """
    能用接口发短信
    """
 
    params = {'account': "YZM2321213", 'password' : "M95zKEWLQ2f5da", 'msg': "【大米剧本杀】您的登陆验证码是：" + yzm + "，请不要把验证码泄漏给其他人，如非本人请勿操作。", 'phone':phone, 'report' : 'false'}
    payload=json.dumps(params)
    print(params)
    headers = {
    'Content-type': 'application/json'
    }

    response = requests.request("POST", "https://smssh1.253.com/msg/v1/send/json", headers=headers, data=payload)

    return response.text


def clearData(url, strTemp):
    if ('403 ' in strTemp):
        strTemp = ''
    strTemp = re.split(r'[ |,、，]|-', strTemp)
    # 清理空
    strTemp = [x for x in strTemp if x != ""]
    # 分词
    for key in strTemp:
        if (len(key) > 12):
            strTemp.remove(key)
            response = requests.request("GET", "https://www.jsonin.com/fenci.php?msg=" + key, headers={}, data={})
            fcData =  json.loads(response.text)
            strTemp = strTemp +fcData
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
    # 指定编码为 'utf-8'（你可以根据需要更改为其他编码）
    response.encoding = 'utf-8'
    domStr = response.text
    soup = BeautifulSoup(domStr, 'html.parser')
    matchTemp = soup.find('meta', {'name': 'keywords'})
    if (matchTemp and matchTemp.get('content')):
        matchTemp = matchTemp.get('content')
        print('[keywords]' + matchTemp)
        return clearData(url, matchTemp)
    matchTemp = soup.find('meta', {'name': 'description'})
    if (matchTemp and matchTemp.get('content')):
        matchTemp = matchTemp.get('content')
        print('[description]' + matchTemp)
        return clearData(url, matchTemp)
    matchTemp = soup.title.string
    if (matchTemp):
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

@app.route('/deleteItem', methods=['POST'])
def deleteItem():
    # 获取 JSON 数据
    data = request.json
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keyword WHERE url = ?", (data["url"],))

    conn.commit()
    conn.close()
    return jsonify({"err": 0})

@app.route('/updataItem', methods=['POST'])
def updataItem():
    # 获取 JSON 数据
    data = request.json
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE keyword SET keyword = '?' WHERE url = '?';", (data["keyword"], data["url"]))

    conn.commit()
    conn.close()
    return jsonify({"err": 0})



@app.route('/searchItem', methods=['GET'])
def searchItem():
    key = request.args.get('key', default=None)  # default=None 意味着如果 'name' 参数不存在，则返回 None
    dataList = []
    if key:
        conn = sqlite3.connect('mydatabase.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM keyword WHERE keyword LIKE '%" + key + "%';")

        conn.commit()
        dataList = cursor.fetchall()
        conn.close()
    return jsonify({"err": 0, "data": dataList})

@app.route('/register', methods=['POST'])
def register():
    # 获取 JSON 数据
    data = request.json
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user (username, password, data) VALUES (?, ?, '{}')", (data["username"], data["password"]))

    conn.commit()
    conn.close()
    return jsonify({"err": 0, "msg": "注册成功!"})

@app.route('/sendSMS', methods=['POST'])
def sendSMS():
    # 获取 JSON 数据
    data = request.json
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE username = '" + data["username"] + "';")

    conn.commit()
    dataTemp = cursor.fetchone()
    yzm = int(random.uniform(1000, 9999))
    if (dataTemp):
        # 有的话直接发短信更新
        cursor.execute("UPDATE user SET password = '%s' WHERE username = '%s';" % (str(yzm), data["username"]))
        conn.commit()
    else:
        cursor.execute("INSERT INTO user (username, password, data) VALUES (?, ?, '{}')", (data["username"], str(yzm)))
        conn.commit()
    sendSMSTo(str(yzm), data["username"])
    conn.close()
    return jsonify({"err": 0, "msg": "发送成功!"})

@app.route('/login', methods=['POST'])
def login():
    # 获取 JSON 数据
    data = request.json
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE username = '" + data["username"] + "' AND password = '" + data["password"] + "';")

    conn.commit()
    dataTemp = cursor.fetchone()
    conn.close()
    if dataTemp:
        return jsonify({"err": 0, "msg": "登录成功!", "data": dataTemp})
    else:
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})

@app.route('/updataLike', methods=['POST'])
def updataLike():
    # 获取 JSON 数据
    data = request.json
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM user WHERE username = '" + data["username"] + "' AND password = '" + data["password"] + "';")

    conn.commit()
    dataTemp = cursor.fetchone()
    
    if dataTemp:
        dataTemp = json.loads(dataTemp[0])
        
        if (data["url"] not in dataTemp):
            dataTemp[data["url"]] = data["num"]
            
        dataTemp[data["url"]] = dataTemp[data["url"]] + data["num"]
        print("UPDATE user SET data = '?' WHERE username = '?';", (json.dumps(dataTemp), data["username"]))
        cursor.execute("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))

        conn.commit()
        conn.close()
        return jsonify({"err": 0, "msg": "成功"})
    else:
        conn.close()
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})

@app.route('/getValue', methods=['POST'])
def getValue():
    conn = sqlite3.connect('mydatabase.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM `keyword`")
    rows = cursor.fetchall()
    conn.close()
    return jsonify({"data": rows})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")