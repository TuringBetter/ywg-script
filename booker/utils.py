# booker/utils.py

import logging
import os

def setup_logger():
    """配置并返回一个全局日志记录器"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_format = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('logs/gym_booking.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    # 返回根记录器
    return logging.getLogger()

def get_field_info(field_no: str) -> str:
    """根据场地编号获取场地名称"""
    try:
        field_num = int(field_no[3:])
        return f"健身房{field_num:02d}"
    except (ValueError, IndexError):
        return "未知场地"