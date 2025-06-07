# booker/core.py

import requests
import json
import time
import schedule
from datetime import datetime, timedelta
import urllib.parse
import logging

# 从同级模块中导入函数
from .config import load_app_config
from .utils import get_field_info

class GymBooker:
    """
    封装了所有抢票业务逻辑的核心类。
    """
    BASE_URL = "https://tybsouthgym.xidian.edu.cn/Field/OrderField"

    def __init__(self, config_path: str, logger: logging.Logger):
        self.config_path = config_path
        self.logger = logger
        self.session = requests.Session()
        
        # 初始化时，调用一次加载逻辑
        self._reload_params()
    
    def _reload_params(self):
        """从文件重新加载所有业务参数到实例属性中。"""
        self.logger.info("正在从 config.json 重新加载业务参数...")
        
        # 重新读取整个配置文件
        self.config = load_app_config(self.config_path)
        
        # 更新 session 中的 cookie
        self.session.headers.update({'Cookie': self.config.get('cookie', '')})
        
        # 重新加载业务参数
        params = self.config.get('booking_params', {})
        self.begin_time = params.get('begin_time', '09:00')
        self.end_time = params.get('end_time', '12:00')
        self.schedule_time = params.get('schedule_time', '12:00')
        self.window_minutes = params.get('window_minutes', 10)
        self.total_fields = params.get('total_fields', 30)

        self.logger.info("业务参数加载完成:")
        self.logger.info(f"  - 预定时间段: {self.begin_time} - {self.end_time}")
        self.logger.info(f"  - 每日执行时间: {self.schedule_time}")
        self.logger.info(f"  - 抢票窗口: {self.window_minutes} 分钟")
        self.logger.info(f"  - 场地总数: {self.total_fields}")

    def _refresh_state(self):
        """从文件重新加载配置和Cookie。"""
        self.logger.info("刷新配置和Cookie...")
        self.config = load_app_config(self.config_path)
        self.session.headers.update({'Cookie': self.config.get('cookie', '')})
        self.logger.info("状态刷新完成。")

    def _create_checkdata(self, field_no, field_name):
        return [{
            "FieldNo": field_no, "FieldTypeNo": "006", "FieldName": field_name,
            "BeginTime": self.begin_time, "Endtime": self.end_time, "Price": "2.00"
        }]

    def _book_single_field(self, field_no, field_name):
        checkdata_str = urllib.parse.quote(json.dumps(self._create_checkdata(field_no, field_name)))
        url = f"{self.BASE_URL}?checkdata={checkdata_str}&dateadd=2&VenueNo=01"
        
        try:
            response = self.session.get(url, timeout=5)
            self.logger.info(f"尝试 {field_name} - 状态码: {response.status_code}")
            
            # 检查登录状态
            try:
                decoded_text = response.content.decode('utf-8')
                if "用户类型选择" in decoded_text or "体育场馆预订系统" in decoded_text:
                    self.logger.error("Cookie已失效，需要重新登录")
                    return False, "cookie_expired"
            except UnicodeDecodeError:
                try:
                    decoded_text = response.content.decode('gbk')
                    if "用户类型选择" in decoded_text or "体育场馆预订系统" in decoded_text:
                        self.logger.error("Cookie已失效，需要重新登录")
                        return False, "cookie_expired"
                except UnicodeDecodeError:
                    self.logger.error("无法解码响应内容")
                    return False, "decode_error"
            
            if response.status_code == 200:
                result = response.json()
                message = result.get('message', '未知错误')
                if result.get('type') == 1:
                    self.logger.info(f"🎉 抢票成功！场地：{field_name}, 响应: {result}")
                    return True, "success"
                self.logger.warning(f"抢票失败: {message}")
                if "已被其他人抢跑" in message: return False, "skip"
                if "下单速度过快" in message: return False, "slow"
                return False, "retry"
            
        except (requests.RequestException, json.JSONDecodeError) as e:
            self.logger.error(f"请求或解析失败 for {field_name}: {e}")
            return False, "request_error"
        
        return False, "retry"

    def daily_booking_task(self, start_time: datetime = None):
        """
        每日执行的抢票任务单元。
        :param start_time: 用于测试的可选参数，如果提供，则基于此时间进行判断。
        """

        self._reload_params()

        self.logger.info("="*50)

        # 如果没有提供测试时间，就使用当前真实时间
        now = start_time or datetime.now()

        self.logger.info(f"触发每日抢票任务 @ {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self._refresh_state()

        # 基于 now 来计算结束时间
        booking_end_time = now + timedelta(minutes=self.window_minutes)
        skipped_fields = set()

        while datetime.now() < booking_end_time:
            if len(skipped_fields) == self.total_fields:
                self.logger.info("所有场地都已被抢完，今日任务结束。")
                return
            for i in range(1, self.total_fields + 1):
                field_no = f"JSP{i:03d}"
                if field_no in skipped_fields: continue
                field_name = get_field_info(field_no)
                success, status = self._book_single_field(field_no, field_name)
                if success:
                    self.logger.info("今日抢票成功，任务结束。")
                    return
                if status == "cookie_expired":
                    self.logger.error("Cookie已失效，任务终止")
                    return
                if status == "skip": skipped_fields.add(field_no)
                elif status == "slow": time.sleep(3)
                else: time.sleep(0.5)
        self.logger.info("抢票时间窗口已过，今日任务结束。")

    def run(self):
        self.logger.info(f"调度器已启动。任务将在每天 {self.booking_time_str} 执行。")
        # schedule 调用时，会无参数地调用 self.daily_booking_task
        # 这样 start_time 就会是 None，函数会使用 datetime.now()
        schedule.every().day.at(self.booking_time_str).do(self.daily_booking_task)
        while True:
            schedule.run_pending()
            time.sleep(1)