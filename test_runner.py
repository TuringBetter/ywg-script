# test_runner.py (增强版)

import sys
from datetime import datetime
from booker.core import GymBooker
from booker.utils import setup_logger

def run_test_at_simulated_time():
    logger = setup_logger()
    try:
        logger.info("========== 模拟时间测试模式启动 ==========")
        booker = GymBooker(config_path='config.json', logger=logger)

        simulated_now = datetime.now()

        logger.info(f"即将以模拟时间 ({simulated_now}) 调用任务...")
        # 将模拟时间注入到任务函数中
        booker.daily_booking_task(start_time=simulated_now)

        logger.info("========== 模拟时间测试模式结束 ==========")

    except Exception as e:
        logger.critical(f"测试过程中遇到严重错误: {e}", exc_info=True)

if __name__ == "__main__":
    run_test_at_simulated_time()