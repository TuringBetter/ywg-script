# cookie_listener.py (v2 with Log Viewer)

import json
import logging
import os
from flask import Flask, request, jsonify, render_template, abort, Response
from collections import deque

# --- 配置区 ---
CONFIG_FILE_PATH = 'config.json'
SECRET_TOKEN = "YourSuperSecretTokenGoesHere_ChangeMe" # 确保这个令牌足够安全
LOG_DIR = 'logs' # 日志文件所在的目录
ALLOWED_LOG_FILES = ['gym_booking.log', 'cookie_listener.log'] # 允许通过Web访问的日志文件名列表
LINES_TO_SHOW = 500 # 默认显示日志的最后500行

# --- 初始化 ---
app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# 如果你想让这个监听服务也记录到文件，可以取消下面这行注释
# logging.getLogger().addHandler(logging.FileHandler(os.path.join(LOG_DIR, 'cookie_listener.log')))

# --- 辅助函数 ---
def read_log_file(filename):
    """高效地读取日志文件的最后N行。"""
    filepath = os.path.join(LOG_DIR, filename)
    if not os.path.exists(filepath):
        return f"错误：日志文件 '{filepath}' 不存在。"
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            # 使用deque可以高效地获取文件的末尾行
            last_lines = deque(f, LINES_TO_SHOW)
            return "".join(last_lines)
    except Exception as e:
        return f"读取文件时发生错误: {e}"

# --- 主API路由 ---
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
    logging.info(f"成功接收到新的Cookie: ...{new_cookie[-20:]}")
    try:
        # 读取现有的配置，以保留其他设置（如booking_params）
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {}
        config_data['cookie'] = new_cookie

        # 写回配置文件
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        logging.info(f"'{CONFIG_FILE_PATH}' 中的Cookie已成功更新！")
        return jsonify({"status": "success", "message": "Cookie updated successfully"}), 200

    except Exception as e:
        logging.error(f"更新配置文件时发生错误: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

# --- 新增的日志查看路由 ---

@app.route('/logs', methods=['GET'])
def list_logs():
    """日志文件列表页面。"""
    token = request.args.get('token')
    if token != SECRET_TOKEN:
        abort(403) # 访问被禁止
    
    html = "<h1>可选日志文件</h1><ul>"
    for filename in ALLOWED_LOG_FILES:
        # 构造每个日志文件的链接，并附上token
        html += f'<li><a href="/logs/view/{filename}?token={token}">{filename}</a></li>'
    html += "</ul>"
    return html

@app.route('/logs/view/<filename>', methods=['GET'])
def view_log(filename):
    """渲染日志查看器HTML页面。"""
    token = request.args.get('token')
    if token != SECRET_TOKEN:
        abort(403)
    
    # 安全检查：确保请求的文件名在白名单内，防止路径遍历攻击
    if filename not in ALLOWED_LOG_FILES:
        abort(404) # 文件未找到
    
    log_content = read_log_file(filename)
    return render_template('log_viewer.html', log_content=log_content, filename=filename, token=token)

@app.route('/api/logs/<filename>', methods=['GET'])
def get_log_api(filename):
    """为前端JS提供纯文本日志内容的API。"""
    token = request.args.get('token')
    if token != SECRET_TOKEN:
        abort(403)
    
    if filename not in ALLOWED_LOG_FILES:
        abort(404)
        
    log_content = read_log_file(filename)
    # 返回纯文本内容
    return Response(log_content, mimetype='text/plain')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)