# booker/config.py

import json
import logging

# 获取一个专门用于此模块的logger实例
logger = logging.getLogger(__name__)

def load_app_config(path: str = 'config.json') -> dict:
    """
    加载JSON配置文件。
    :param path: 配置文件的路径。
    :return: 包含配置信息的字典。
    :raises FileNotFoundError: 如果文件不存在。
    :raises json.JSONDecodeError: 如果文件格式不正确。
    """
    try:
        with open(path, 'r') as f:
            config = json.load(f)
            logger.info(f"成功加载配置文件 '{path}'")
            return config
    except FileNotFoundError:
        logger.error(f"配置文件 '{path}' 未找到。")
        raise
    except json.JSONDecodeError:
        logger.error(f"配置文件 '{path}' 格式错误。")
        raise