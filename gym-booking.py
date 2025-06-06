import requests
import json
import time
from datetime import datetime
import urllib.parse
import logging
import os

# 配置日志
def setup_logger():
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 配置日志格式
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/gym_booking.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

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
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        
        # 解析响应内容
        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('type') == 1:
                    logger.info("抢票成功！")
                    return True
                else:
                    logger.warning(f"抢票失败: {result.get('message', '未知错误')}")
                    return False
            except json.JSONDecodeError:
                logger.error("响应解析失败")
                return False
        return False
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        return False

def main():
    field_no = "JSP014"
    field_name = "健身房14"
    begin_time = "09:00"
    end_time = "12:00"
    
    logger.info("开始抢票程序...")
    while True:
        current_time = datetime.now()
        # 检查是否到达中午12点且未超过12:10
        if current_time.hour == 12 and 0 <= current_time.minute <= 10:
            logger.info("开始尝试抢票...")
            success = book_field(field_no, field_name, begin_time, end_time)
            if success:
                logger.info("今日抢票成功，等待明天继续...")
                # 等待到明天
                time.sleep(23 * 60 * 60 + 40 * 60)
            else:
                logger.info("抢票失败，继续尝试...")
                time.sleep(0.5)  # 失败后等待0.5秒再试
        elif current_time.hour == 12 and current_time.minute > 10:
            logger.info("已超过12:10，今日抢票结束，等待明天...")
            # 计算到明天12点的时间
            tomorrow = current_time.replace(hour=12, minute=0, second=0, microsecond=0)
            tomorrow = tomorrow.replace(day=tomorrow.day + 1)
            wait_seconds = (tomorrow - current_time).total_seconds()
            time.sleep(wait_seconds)
        else:
            # 如果还没到12点，每分钟检查一次
            time.sleep(10)

if __name__ == "__main__":
    main() 