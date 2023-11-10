import re
import requests
import time
import json
import random
import mysql.connector
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

def clearLen(list):
    newList = []
    for item in list:
        if (len(item) > 1 and len(item) < 600):
            newList.append(item)
    return newList

busyList = []
clearBusy = False
def clearData(url, strTemp, source):
    global busyList
    global clearBusy
    if (clearBusy):
        print('处理繁忙:' + url)
        busyList.append([url, strTemp, source])
        return
    print('开始处理:' + url)
    clearBusy = True
    if ('403 ' in strTemp):
        strTemp = ''
    strTemp = strTemp.replace("'", " ")
    strTemp = strTemp.replace('"', " ")
    strTemp = re.split(r'[ |,、，#@]|-', strTemp)
    # 清理空
    strTemp = [x for x in strTemp if x != ""]
    # 分词
    for key in strTemp:
        if (len(key) > 600):
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
    sqlTemp = "INSERT IGNORE INTO `keyword` (url, data, source, likeNum, time) VALUES ('%s', \"%s\", '%s', '0', '%s')" % (url, strTemp, source, int(time.time()))
    print(sqlTemp)
    cursor.execute(sqlTemp)

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
        # 判断是否需要编码转换
        if ('charset=gb2312"' in domStr):
            response = requests.request("GET", url, headers=headers, data=payload)
            response.raise_for_status()
            response.encoding = 'gb2312'
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
    data["keyword"] = json.dumps(data["keyword"], ensure_ascii=False)
    sqlTemp = "UPDATE `keyword` SET data = '%s' WHERE id = '%s';" % (data["keyword"], data["url"])
    print(sqlTemp)
    cursor.execute(sqlTemp)

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
    if (data["username"] == ''):
        return jsonify({"err": 1, "msg": "用户名不能为空!"})
    if (data["password"] == ''):
        return jsonify({"err": 1, "msg": "密码不能为空!"})
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
        cursor.execute("INSERT INTO user (username, password, data, loginTime, `like`) VALUES ('%s', '%s', '{}', '%s', '[]')" % (data["username"],str(yzm), int(time.time())))
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
        if (int(time.time()) - int(dataTemp[5]) > 300):
            return jsonify({"err": 1, "msg": "验证码过期!"})
        return jsonify({"err": 0, "msg": "登录成功!", "data": dataTemp})
    else:
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})

@app.route('/like', methods=['POST'])
def like():
    # 获取 JSON 数据
    data = request.json
    if ('username' not in data):
        return jsonify({"err": 1, "msg": "缺少username字段!"})
    if ('url' not in data):
        return jsonify({"err": 1, "msg": "缺少url字段!"})
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
            dataTemp[data["url"]] = 0
            
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
    if ('username' not in data):
        return jsonify({"err": 1, "msg": "缺少username字段!"})
    if ('url' not in data):
        return jsonify({"err": 1, "msg": "缺少url字段!"})
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
            dataTemp[data["url"]] = 0
            
        dataTemp[data["url"]] = dataTemp[data["url"]] - 1
        print("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))
        cursor.execute("UPDATE user SET data = '%s' WHERE username = '%s';" % (json.dumps(dataTemp), data["username"]))

        mydb.commit()
        mydb.close()
        return jsonify({"err": 0, "msg": "成功"})
    else:
        mydb.close()
        return jsonify({"err": 1, "msg": "用户名或密码错误!"})

useRecommendTemp = {}
@app.route('/recommend', methods=['GET'])
def recommend():
    global useRecommendTemp
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    cursor.execute("SELECT * FROM `keyword`;")
    rows = cursor.fetchall()
    # 先获取用户数据
    userName = request.args.get('user')
    cursor.execute("SELECT * FROM `user` WHERE username = '%s';" % (userName))
    userInfo = cursor.fetchone()
    
    if (len(rows) < 1):
        return jsonify({"err": 1, "data": "网址数量不足!"})
    if (userInfo):
        print(userInfo[3])
        returnItem = rows[int(random.uniform(0, len(rows) - 1))]
        # 找到他喜欢的
        if (int(random.uniform(1000, 9999)) < 3000):
            # 随机选一个他喜欢的分类
            if (len(userInfo[4]) > 0):
                if (isinstance(userInfo[4], str)):
                    tempObj = userInfo[4].replace("'", '"')
                    tempObj = json.loads(tempObj)
                    print(tempObj)
                    likeStr = tempObj[int(random.uniform(0, len(tempObj) - 1))]
                    cursor.execute("SELECT * FROM `keyword` WHERE data LIKE '%" + likeStr[0] + "%';")
                    rows = cursor.fetchall()
                    if (len(rows) > 0):
                        returnItem = rows[int(random.uniform(0, len(rows) - 1))]
        if (userName not in useRecommendTemp):
            useRecommendTemp[userName] = []
        # 第一次随机推
        if (returnItem[1] in useRecommendTemp[userName]):
            returnItem = rows[int(random.uniform(0, len(rows) - 1))]
        # 第二次随机推
        if (returnItem[1] in useRecommendTemp[userName]):
            returnItem = rows[int(random.uniform(0, len(rows) - 1))]
        useRecommendTemp[userName].append(useRecommendTemp[userName])
        mydb.close()
        return jsonify({"err": 0, "data": returnItem, "like": returnItem[1] in userInfo[3]})
    else:
        mydb.close()
        return jsonify({"err": 1, "data": "用户不存在!"})

@app.route('/checkLike', methods=['POST'])
def checkLike():
    # 获取 JSON 数据
    data = request.json
    if ('user' not in data):
        return jsonify({"err": 1, "msg": "user字段不存在"})
    if ('url' not in data):
        return jsonify({"err": 1, "msg": "url字段不存在"})
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    # 先获取用户数据
    userName = request.args.get('user')
    cursor.execute("SELECT * FROM `user` WHERE username = '%s';" % (data['user']))
    userInfo = cursor.fetchone()
    mydb.close()
    if (data['url'] in userInfo[3]):
        if (isinstance(userInfo[3], str)):
            tempObj = userInfo[3].replace("'", '"')
            tempObj = json.loads(tempObj)
        print(tempObj)
        return jsonify({"err": 0, "like": tempObj[data['url']]})
    else:
        return jsonify({"err": 0, "like": 0})

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
    # mydb = mysql.connector.connect(
    #     host="logs.lamp.run",          # 数据库主机地址
    #     user="root",     # 数据库用户名
    #     password="mmit7750", # 数据库密码
    #     database="keyword"  # 数据库名称，可选
    # )
    
    # cursor = mydb.cursor(buffered=True)
    for item in data["list"]:
        # cursor.execute("SELECT * FROM `keyword` WHERE url ='" + item["url"] + "'")
        # rows = cursor.fetchone()
        
        # if (not rows):
        if ("matchTemp" in item and "url" in item):
            clearData(item["url"], item["matchTemp"], data["user"])
    # mydb.close()
    return jsonify({"err": 0, "msg": "操作已提交"})



@app.route('/getValue', methods=['POST'])
def getValue():
    # 获取 JSON 数据
    data = request.json
    print(data["page"])
    if ("page" not in data):
        data["page"] = 1
    # 创建连接
    mydb = mysql.connector.connect(
        host="logs.lamp.run",          # 数据库主机地址
        user="root",     # 数据库用户名
        password="mmit7750", # 数据库密码
        database="keyword"  # 数据库名称，可选
    )
    cursor = mydb.cursor(buffered=True)
    if ('key' in data and data['key'] != ''):
        cursor.execute("SELECT * FROM `keyword` WHERE data LIKE '%" + data['key'] + "%'")
    else:
        if ('url' in data and data['url'] != ''):
            cursor.execute("SELECT * FROM `keyword` WHERE url LIKE '%" + data['url'] + "%'")
        else:
            cursor.execute("SELECT * FROM `keyword` LIMIT 20 OFFSET " + str((int(data["page"]) - 1) * 20))
    rows = cursor.fetchall()
    if (int(data["page"]) == 1):
        cursor.execute("SELECT COUNT(*) FROM `keyword`;")
        contNum = cursor.fetchone()
        mydb.close()
        return jsonify({"data": rows, "num": contNum[0]})
    else:
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
                print(keywordTemp2[userLikeUrl])
                if (isinstance(keywordTemp2[userLikeUrl], str)):
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
        # 根据字典的值进行排序（降序），并提取前十个条目
        temp = sorted(userTemp2[userID].items(), key=lambda x: x[1], reverse=True)[:10]
        # temp = list(userTemp2[userID].keys())
        # temp = temp[0:10]
        cursor.execute("UPDATE user SET `like` = '%s' WHERE id = '%s';" % (json.dumps(temp, ensure_ascii=False), userID))
    mydb.commit()
    mydb.close()
    return jsonify({"err": 0})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")