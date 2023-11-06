import sched
import time
import json
import mysql.connector

scheduler = sched.scheduler(time.time, time.sleep)

def runJob():
# 这里写你想要执行的代码
    print("执行了方法")
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
runJob()
def your_method(sc): 
    runJob()
    # 再次调度这个方法，10分钟后再次运行
    sc.enter(600, 1, your_method, (sc,))

scheduler.enter(600, 1, your_method, (scheduler,))
scheduler.run()