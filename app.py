import re
import requests
import time
import json
import random
import mysql.connector
from flask_cors import CORS
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify

# 创建连接
mydb = mysql.connector.connect(
  host="logs.lamp.run",          # 数据库主机地址
  user="root",     # 数据库用户名
  password="mmit7750", # 数据库密码
  database="keyword"  # 数据库名称，可选
)

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

def clearLen(list):
    newList = []
    for item in list:
        if (len(item) > 1 and len(item) < 6):
            newList.append(item)
    return newList

busyList = []
clearBusy = False
def clearData(url, strTemp, source):
    global clearBusy
    if (clearBusy):
        print('处理繁忙:' + url)
        busyList.append([url, strTemp, source])
        return
    print('开始处理:' + url)
    clearBusy = True
    if ('403 ' in strTemp):
        strTemp = ''
    strTemp = re.split(r'[ |,、，]|-', strTemp)
    # 清理空
    strTemp = [x for x in strTemp if x != ""]
    # 分词
    for key in strTemp:
        if (len(key) > 6):
            response = requests.request("GET", "https://api.pearktrue.cn/api/fenci/?word=" + key, headers={}, data={})
            fcData =  json.loads(response.text)
            strTemp = strTemp + fcData["data"]
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    strTemp = clearLen(strTemp)
    print(strTemp)
    cursor.execute("INSERT INTO `keyword` (url, data, source, likeNum, time) VALUES ('%s', \"%s\", '%s', '0', '%s')" % (url, strTemp, source, int(time.time())))

    mydb.commit()
    mydb.close()
    clearBusy = False
    if (len(busyList) > 0):
        removed = busyList.pop(0)
        clearData(removed[0], removed[1], removed[2])
    return strTemp

# 这个变量防止重复
hideURLList = []
def checkDom(url, source):
    global hideURLList
    if (url in hideURLList):
        return
    hideURLList.append(url)
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM `keyword` WHERE url ='" + url + "'")
    rows = cursor.fetchone()
    mydb.close()
    if (rows):
        print(rows)
        return rows[1]
    
    payload = {}
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        response.raise_for_status()
        # 指定编码为 'utf-8'（你可以根据需要更改为其他编码）
        response.encoding = 'utf-8'
        domStr = response.text
        soup = BeautifulSoup(domStr, 'html.parser')
        matchTemp = soup.find('meta', {'name': 'keywords'})
        if (matchTemp and matchTemp.get('content')):
            matchTemp = matchTemp.get('content')
            print('[keywords]' + matchTemp)
            return clearData(url, matchTemp, source)
        matchTemp = soup.find('meta', {'name': 'description'})
        if (matchTemp and matchTemp.get('content')):
            matchTemp = matchTemp.get('content')
            print('[description]' + matchTemp)
            return clearData(url, matchTemp, source)
        if (soup.title):
            matchTemp = soup.title.string
            if (matchTemp):
                print('[title]' + matchTemp)
                return clearData(url, matchTemp, source)
    except requests.HTTPError as error:
        print(f'HTTP error occurred: {error}')
    return clearData(url, '', source)

@app.route('/webSite', methods=['POST'])
def webSite():
    global clearBusy
    # 获取 JSON 数据
    data = request.json
    clearBusy = False   
    # 对于本示例，我们只是将接收到的数据返回为 JSON 响应
    for key in data['urlList']:
        if (key.startswith("http")):
            checkDom(key, data['source'])
    return jsonify({"err": 0})


@app.route('/deleteItem', methods=['POST'])
def deleteItem():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("DELETE FROM keyword WHERE id = '%s'" % (data["url"]))

    mydb.commit()
    mydb.close()
    return jsonify({"err": 0})

@app.route('/updataItem', methods=['POST'])
def updataItem():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("UPDATE keyword SET keyword = '?' WHERE url = '?';", (data["keyword"], data["url"]))

    mydb.commit()
    mydb.close()
    return jsonify({"err": 0})



@app.route('/searchItem', methods=['GET'])
def searchItem():
    key = request.args.get('key', default=None)  # default=None 意味着如果 'name' 参数不存在，则返回 None
    dataList = []
    if key:
        # 创建连接
        mydb = mysql.connector.connect(
            host="logs.lamp.run",          # 数据库主机地址
            user="root",     # 数据库用户名
            password="mmit7750", # 数据库密码
            database="keyword"  # 数据库名称，可选
        )
        cursor = mydb.cursor(buffered=True)
        cursor.execute("SELECT * FROM keyword WHERE keyword LIKE '%" + key + "%';")

        mydb.commit()
        dataList = cursor.fetchall()
        mydb.close()
    return jsonify({"err": 0, "data": dataList})

@app.route('/userInfo', methods=['GET'])
def userInfo():
    dataList = []
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM user;")

    mydb.commit()
    dataList = cursor.fetchall()
    mydb.close()
    return jsonify({"err": 0, "data": dataList})

@app.route('/register', methods=['POST'])
def register():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("INSERT INTO user (username, password, data) VALUES ('%s', '%s', '{}')" % (data["username"], data["password"]))

    mydb.commit()
    mydb.close()
    return jsonify({"err": 0, "msg": "注册成功!"})

@app.route('/sendSMS', methods=['POST'])
def sendSMS():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM user WHERE username = '%s';" % (data["username"]))

    mydb.commit()
    dataTemp = cursor.fetchone()
    yzm = int(random.uniform(1000, 9999))
    if (dataTemp):
        # 有的话直接发短信更新
        cursor.execute("UPDATE user SET password = '%s', loginTime = '%s' WHERE username = '%s';" % (str(yzm), int(time.time()), data["username"]))
        mydb.commit()
        mydb.close()
    else:
        cursor.execute("INSERT INTO user (username, password, data, loginTime, like) VALUES ('%s', '%s', '{}', '%s', '[]')" % (data["username"],str(yzm), int(time.time())))
        mydb.commit()
        mydb.close()
    sendSMSTo(str(yzm), data["username"])
    return jsonify({"err": 0, "msg": "发送成功!"})

@app.route('/login', methods=['POST'])
def login():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM user WHERE username = '" + data["username"] + "' AND password = '" + data["password"] + "';")

    mydb.commit()
    dataTemp = cursor.fetchone()
    mydb.close()
    if dataTemp:
        return jsonify({"err": 0, "msg": "登录成功!", "data": dataTemp})
    else:
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})

@app.route('/like', methods=['POST'])
def like():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT data FROM user WHERE username = '" + data["username"] + "';")

    mydb.commit()
    
    dataTemp = cursor.fetchone()
    
    if dataTemp:
        dataTemp = json.loads(dataTemp[0])
        
        if (data["url"] not in dataTemp):
            dataTemp[data["url"]] = 1
            
        dataTemp[data["url"]] = dataTemp[data["url"]] + 1
        print("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))
        cursor.execute("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))
        cursor.execute("UPDATE keyword SET likeNum = likeNum + 1 WHERE url = '%s';" % (data["url"]))
        mydb.commit()
        mydb.close()
        return jsonify({"err": 0, "msg": "成功"})
    else:
        mydb.close()
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})

@app.route('/unLike', methods=['POST'])
def unLike():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT data FROM user WHERE username = '" + data["username"] + "';")

    mydb.commit()
    dataTemp = cursor.fetchone()
    
    if dataTemp:
        dataTemp = json.loads(dataTemp[0])
        
        if (data["url"] not in dataTemp):
            dataTemp[data["url"]] = -1
            
        dataTemp[data["url"]] = dataTemp[data["url"]] - 1
        print("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))
        cursor.execute("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))

        mydb.commit()
        mydb.close()
        return jsonify({"err": 0, "msg": "成功"})
    else:
        mydb.close()
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})


@app.route('/recommend', methods=['GET'])
def recommend():
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM `keyword`")
    rows = cursor.fetchall()
    mydb.close()
    return jsonify({"err": 0, "data": rows[int(random.uniform(0, len(rows) - 1))]})

@app.route('/addKeyWord', methods=['POST'])
def addKeyWord():
    # 获取 JSON 数据
    data = request.json
    if ('user' not in data):
        if ('source' in data):
            data['user'] = data['source']
    if ('user' not in data):
        return jsonify({"err": 1, "msg": "user字段不存在"})
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    for item in data["list"]:
        cursor.execute("SELECT * FROM `keyword` WHERE url ='" + item["url"] + "'")
        rows = cursor.fetchone()
        
        if (not rows):
            clearData(item["url"], item["matchTemp"], data["user"])
    mydb.close()
    return jsonify({"err": 0, "msg": "操作已提交"})



@app.route('/getValue', methods=['POST'])
def getValue():
    # 获取 JSON 数据
    data = request.json
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    if ('key' in data and data['key'] != ''):
        if ('url' in data and data['url'] != ''):
            cursor.execute("SELECT * FROM `keyword` WHERE url LIKE '%" + data['url'] + "%'")
        else:
            cursor.execute("SELECT * FROM `keyword` WHERE data LIKE '%" + data['key'] + "%'")
    else:
        cursor.execute("SELECT * FROM `keyword`")
    rows = cursor.fetchall()
    mydb.close()
    return jsonify({"data": rows})

@app.route('/gjcCheck', methods=['GET'])
def gjcCheck():
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM `keyword`")
    keywordTemp = cursor.fetchall()
    cursor.execute("SELECT * FROM `user`")
    userTemp = cursor.fetchall()
    
    keywordTemp2 = {}
    userTemp2 = {}
    for item in keywordTemp:
        # print(item)
        keywordTemp2[item[1]] = item[2]
    for item in userTemp:
        # print(item)
        userLikeData = json.loads(item[3])
        for userLikeUrl in userLikeData:
            # print(keywordTemp2)
            if (userLikeUrl in keywordTemp2):
                keywordTemp2[userLikeUrl] = keywordTemp2[userLikeUrl].replace("'", '"')
                keywordTemp2[userLikeUrl] = json.loads(keywordTemp2[userLikeUrl])
                # print(keywordTemp2[userLikeUrl].replace("'", '"'))
                for urlKeyTemp in keywordTemp2[userLikeUrl]:
                    # print(urlKeyTemp)
                    # print(userLikeData)
                    if (item[0] not in userTemp2):
                        userTemp2[item[0]] = {}
                    if (urlKeyTemp not in userTemp2[item[0]]):
                        userTemp2[item[0]][urlKeyTemp] = userLikeData[userLikeUrl]
                    else:
                        userTemp2[item[0]][urlKeyTemp] += userLikeData[userLikeUrl]
    # 更新数据
    for userID in userTemp2:
        cursor.execute("UPDATE user SET `like` = '%s' WHERE id = '%s';" % (json.dumps(list(userTemp2[userID].keys()), ensure_ascii=False), userID))
    mydb.commit()
    mydb.close()
    return jsonify({"data": userTemp2})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")