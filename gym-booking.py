import requests
import json
import time
from datetime import datetime
import urllib.parse

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def create_checkdata(field_no, field_name, begin_time, end_time):
    return [{
        "FieldNo": field_no,
        "FieldTypeNo": "006",
        "FieldName": field_name,
        "BeginTime": begin_time,
        "Endtime": end_time,
        "Price": "2.00"
    }]

def book_field(field_no, field_name, begin_time, end_time, dateadd=2, venue_no="01"):
    config = load_config()
    
    # 构建完整的URL，与Postman测试用例保持一致
    checkdata = create_checkdata(field_no, field_name, begin_time, end_time)
    checkdata_str = urllib.parse.quote(json.dumps(checkdata))
    url = f"https://tybsouthgym.xidian.edu.cn/Field/OrderField?checkdata={checkdata_str}&dateadd={dateadd}&VenueNo={venue_no}"
    
    # 只使用必要的请求头
    headers = {
        'Cookie': config['cookie']
    }
    
    try:
        # 使用与Postman测试用例相同的方式发送请求
        response = requests.request("GET", url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        return response
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None

def main():
    # 示例：预订健身房14，时间段9:00-12:00
    field_no = "JSP014"
    field_name = "健身房14"
    begin_time = "09:00"
    end_time = "12:00"
    
    book_field(field_no, field_name, begin_time, end_time)

    # print("开始抢票...")
    # while True:
    #     current_time = datetime.now()
    #     if current_time.hour == 0 and current_time.minute == 0:
    #         print("开始尝试预订...")
    #         response = book_field(field_no, field_name, begin_time, end_time)
    #         if response and response.status_code == 200:
    #             print("预订成功！")
    #             break
    #         else:
    #             print("预订失败，等待重试...")
    #     time.sleep(1)

if __name__ == "__main__":
    main() 