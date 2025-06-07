# cookie_listener.py

import json
import logging
import os
from flask import Flask, request, jsonify

# --- 配置区 ---
CONFIG_FILE_PATH = 'config.json' # 确保路径正确
# 设置一个简单的密码/令牌，防止任何人都能调用这个接口
# 请务必修改成一个你自己知道的、足够复杂的字符串
SECRET_TOKEN = "YourSuperSecretTokenGoesHere_ChangeMe" 

# --- 初始化 ---
app = Flask(__name__)

# 配置日志，以便我们能看到接收记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/update-cookie', methods=['POST'])
def update_cookie():
    """
    监听POST请求，用于更新config.json中的cookie。
    """
    # 1. 安全验证：检查请求头中是否包含正确的令牌
    auth_token = request.headers.get('X-Auth-Token')
    if auth_token != SECRET_TOKEN:
        logging.warning(f"接收到未授权的请求，IP: {request.remote_addr}")
        return jsonify({"status": "error", "message": "Forbidden"}), 403

    # 2. 获取数据：从请求的JSON体中获取cookie
    try:
        data = request.get_json()
        new_cookie = data['cookie']
    except Exception as e:
        logging.error(f"解析请求数据失败: {e}")
        return jsonify({"status": "error", "message": "Bad Request"}), 400

    if not new_cookie:
        logging.warning("接收到的cookie为空。")
        return jsonify({"status": "error", "message": "Cookie is empty"}), 400

    logging.info(f"成功接收到新的Cookie: ...{new_cookie[-20:]}") # 只打印后20位，保护隐私

    # 3. 更新配置文件
    try:
        # 读取现有的配置，以保留其他设置（如booking_params）
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {} # 如果文件不存在，则创建一个新的

        # 更新cookie值
        config_data['cookie'] = new_cookie

        # 写回配置文件
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logging.info(f"'{CONFIG_FILE_PATH}' 中的Cookie已成功更新！")
        return jsonify({"status": "success", "message": "Cookie updated successfully"}), 200

    except Exception as e:
        logging.error(f"更新配置文件时发生错误: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

if __name__ == '__main__':
    # 监听所有网络接口的5000端口
    # 在生产环境中，建议使用Gunicorn等WSGI服务器来运行
    app.run(host='0.0.0.0', port=5000)