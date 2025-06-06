# main.py

import sys
from booker.core import GymBooker
from booker.utils import setup_logger

# 程序的唯一入口
if __name__ == "__main__":
    # 1. 初始化日志
    logger = setup_logger()

    # 2. 启动应用
    try:
        logger.info("应用启动...")
        booker = GymBooker(config_path='config.json', logger=logger)
        booker.run()
    except FileNotFoundError:
        logger.critical("无法启动：请确保 config.json 文件存在于项目根目录。")
        sys.exit(1) # 异常退出
    except Exception as e:
        logger.critical(f"应用遇到未知严重错误并终止: {e}", exc_info=True)
        sys.exit(1) # 异常退出