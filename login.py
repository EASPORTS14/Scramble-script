# encoding=utf-8
import datetime
import ast
import requests
import json
from ids_encrypt import encryptAES
from bs4 import BeautifulSoup
# 用于验证码处理库
from PIL import Image 
from io import BytesIO
#文字识别库 需要安装tesseract ,并添加环境变量 但是不如国产好用
import pytesseract 
import ddddocr
import base64
import matplotlib.pyplot as plt

# 登录信息门户，返回登录后的session
def login(cardnum, password, ehall):
    ss = requests.Session()
    form = {"username": cardnum}
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"}
    ss.headers = headers
    #  获取登录页面表单，解析加密隐藏值
    #url = "https://newids.seu.edu.cn/authserver/login?goto=http://my.seu.edu.cn/index.portal"      # 这是主页，但是session带不到重定向后的页面，所以不如直接用下面这个网址登录
    url = "https://newids.seu.edu.cn/authserver/login?service=http%3A%2F%2Fyuyue.seu.edu.cn%2Feduplus%2Forder%2FgetContacts.do%3FsclId%3D1%26flag%3Dcontact"
    # 上面这个网址是预约界面的快捷入口，防止从主页登进去之后，重定向又要你登录？？
    res = ss.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    attrs = soup.select('[tabid="01"] input[type="hidden"]')
    for k in attrs:
        if k.has_attr('name'):
            form[k['name']] = k['value']
        elif k.has_attr('id'):
            form[k['id']] = k['value']
    form['password'] = encryptAES(password, form['pwdDefaultEncryptSalt'])
    # 登录认证
    res = ss.post(url, data=form)
    if ehall == 1:
      # 登录ehall(存在多次302)
      res = ss.get(
        'http://ehall.seu.edu.cn/login?service=http://ehall.seu.edu.cn/new/index.html')
      # 获取登录信息（验证结果）
      res = ss.get('http://ehall.seu.edu.cn/jsonp/userDesktopInfo.json')
      json_res = json.loads(res.text)
      try:
          name = json_res["userName"]
          print(name, "终于登陆成功！")
      except Exception:
          print("认证失败！")
          return False
    return ss


def recognize_captcha(img_path, method):
    #验证码识别
    if method == 1:
        with open(img_path,'rb') as f:
             img_bytes = f.read()
        ocr = ddddocr.DdddOcr()
        print("handling the image............")
        result = ocr.classification(img_bytes)
        return result
    else:
        im = Image.open(img_path)
        im = im.convert("L")
        # 1. threshold the image 色块两极化  就是去噪  判断的准
        threshold = 140
        table = [0]*threshold + [1]*(256-threshold)
        out = im.point(table, '1')
        # 2. recognize with tesseract
        num = pytesseract.image_to_string(out)
        return num.replace("\n", "") # 处理结果带了换行符，很奇怪，这里加了个小处理

def doTableTennis(session,method):
    url = "http://yuyue.seu.edu.cn/eduplus/order/order/judgeOrder.do?sclId=1"
    rday = "2022-10-14"
    rtime = "19:00-20:00"
    useTime = rday + " " + rtime
    Data1 = {
                'itemId':'7',
                'dayInfo':rday,
                'time': rtime
    }
    while 1:
         res = session.post(url, data=Data1)
         msg = res.text         # should be success
         print(msg)
         if msg[0] == 's':
              url_image = 'http://yuyue.seu.edu.cn/eduplus/validateimage' # 获取验证码
              r2 = session.get(url_image)
              if method == 1:
                  tempIm = './code.jpg'
                  with open(tempIm,'wb') as f:
                       f.write(r2.content)
              else:
                  tempIm = BytesIO(r2.content)
              validcode = recognize_captcha(tempIm,method)  # 验证码识别
              if len(validcode) == 0 or validcode[0] == ' ':
                    print("未能识别"+ validcode)
                    continue
              else:
                    print("识别到了： "+ validcode)
                    Data2 = {
                                'ids': '',
                                'useTime': useTime,
                                'itemId': 7,
                                'allowHalf': 2,
                                'validateCode': validcode,
                                'phone': '17302582025',
                                'remark': '',
                                'useUserIds': ''
                    } 
                    url2 = "http://yuyue.seu.edu.cn/eduplus/order/order/order/judgeUseUser.do?sclId=1"
                    r3 = session.post(url2,data=Data2)
                    # 没找到成功的回显
         else:
             print("-----没能跳出弹窗------")
             break
       
    
def doLecture(session, method):
    # 登陆之后直接进入对应的APP
    res = session.get("http://ehall.seu.edu.cn/appShow?appId=5736122417335219")
    url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/queryActivityList.do?_=1665620624185"
    Data1 = {
             'pageIndex':1,
             'pageSize':10,
             'sortField':'',
             'sortOrder':''
    }
    res = session.post(url,data=Data1)
    dictionary1 = ast.literal_eval(res.text)
    data_list = dictionary1['datas']       # 每个元素是字典
    lectureNumber = 3  
    wid = data_list[lectureNumber]["WID"]
    print("我要预约的是： " + data_list[lectureNumber]["JZMC"] + "WID: " + wid)
    count = 0
    # 掐一下时间
    while 1:
        break
        curr_time = datetime.datetime.now()
        if curr_time.minute == 59 and curr_time.second == 59:
            break
    print("开始预约！")
    while 1:
        url = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/vcode.do"
        res = session.get(url)
        data_list =  res.text.split("\"")
        #with open('vimage.txt','r',encoding='utf-8') as f:
        #      content = f.read()
        #data_list = content.split("\"")
        img_str = data_list[3]
        img_str = img_str.split(',')[1]
        base64_data_bytes = img_str.encode('utf-8')
        image_data = base64.b64decode(base64_data_bytes)
        print(type(image_data))
        # 下面是得到验证码，并且发给处理函数路径
        if method == 1:
            tempIm = './code.jpg'
            with open(tempIm,'wb') as f:
                 f.write(image_data)
        else:
            tempIm = BytesIO(image_data)
        validcode = recognize_captcha(tempIm,method)  # 验证码识别
        print("识别到了： "+validcode)
        Data2 = {
                   "HD_WID": wid,
                   "vcode": validcode
        }
        dj = json.dumps(Data2)
        # 一定要先转成字符串，作为字典的值！！！
        js = {"paramJson":dj}
        url_final = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/yySave.do"
        json_str = json.dumps(Data2) 
        res_final = session.post(url_final, data=js)
        print(res_final.text)
        '''
        url_test = "http://ehall.seu.edu.cn/gsapp/sys/jzxxtjapp/hdyy/queryNotice.do"
        Data3 = {
                    'WID':wid,
                    'pageIndex':1,
                    'pageSize':1
                }
        res_test = session.post(url_test,data=Data3)
        print(res_test.text)
        count = count + 1
        '''
        if datetime.datetime.now().minute >= 1:
            break


    



if __name__ == '__main__':
   # 加载全局配置
   with open("./config.json", "r", encoding="utf-8") as f:
       configs = f.read()
   configs = json.loads(configs)
   cardnum = configs['user']['cardnum']
   password = configs['user']['password']
   ehall = 1
   method = 1
   ss = login(cardnum, password, ehall)
   #doTableTennis(ss,method)
   doLecture(ss,method)





