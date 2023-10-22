#!/usr/local/bin/python

import json
import requests


def send_sms(text, phone):
    """
    能用接口发短信
    """
 
    params = {'account': "YZM2321213", 'password' : "M95zKEWLQ2f5da", 'msg': text, 'phone':phone, 'report' : 'false'}
    params=json.dumps(params)
    print(params)
    # headers = {"Content-type": "application/json"}
    # conn = httplib.HTTPConnection(host, port=port, timeout=30)
    # conn.request("POST", sms_send_uri, params, headers)
    # response = conn.getresponse()
    # response_str = response.read()
    # conn.close()
    # return response_str 
    url = "https://smssh1.253.com/msg/v1/send/json"

    payload = params
    headers = {
    'Content-type': 'application/json'
    }

    response = requests.request("POST", "https://smssh1.253.com/msg/v1/send/json", headers=headers, data=payload)

    return response.text

if __name__ == '__main__':

    phone = "18092852085"
	#设置您要发送的内容：其中“【】”中括号为运营商签名符号，多签名内容前置添加提交
    text = "【大米剧本杀】您的登陆验证码是：1234，请不要把验证码泄漏给其他人，如非本人请勿操作。"


    #调用智能匹配模版接口发短信
    print(send_sms(text, phone))