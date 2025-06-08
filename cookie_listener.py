# cookie_listener.py (v3 with Hot-Reloadable External Config)

import json
import logging
import os
import time
from flask import Flask, request, jsonify, render_template, abort, Response, g
from collections import deque

# --- 配置管理器 ---

class ConfigManager:
    """一个简单的配置管理器，支持从JSON文件热加载。"""
    def __init__(self, config_path):
        self.config_path = config_path
        self._config = {}
        self._last_mtime = 0
        self._load_config()

    def _load_config(self):
        """加载或重新加载配置文件。"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            self._last_mtime = os.path.getmtime(self.config_path)
            logging.info(f"配置 '{self.config_path}' 已成功加载/重新加载。")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"无法加载配置文件 '{self.config_path}': {e}")
            # 在无法加载时提供一个最小化的默认配置，以防服务完全崩溃
            self._config = {
                "SECURITY": {"SECRET_TOKEN": "default_fallback_token"},
                "LOG_VIEWER": {"ALLOWED_LOG_FILES": []}
            }
            
    def check_and_reload(self):
        """检查文件修改时间，如果文件已更新则重新加载。"""
        try:
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._last_mtime:
                logging.info("检测到配置文件已更改，将执行热重载。")
                self._load_config()
        except FileNotFoundError:
            logging.warning("配置文件未找到，无法检查更新。")

    def get(self, section, key, default=None):
        """安全地获取配置项。"""
        return self._config.get(section, {}).get(key, default)

# --- 初始化 ---

LISTENER_CONFIG_PATH = 'listener_config.json'
BOOKING_CONFIG_PATH = 'config.json'

app = Flask(__name__)
config_manager = ConfigManager(LISTENER_CONFIG_PATH)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# 可选：让服务自身也记录到文件
# log_dir = config_manager.get("LOG_VIEWER", "LOG_DIR", "logs")
# if not os.path.exists(log_dir): os.makedirs(log_dir)
# logging.getLogger().addHandler(logging.FileHandler(os.path.join(log_dir, 'cookie_listener.log')))


@app.before_request
def before_request_hook():
    """在每个请求处理之前，检查并重新加载配置。"""
    config_manager.check_and_reload()
    # 将当前配置值存入Flask的全局对象g，方便在单次请求中重复使用
    g.SECRET_TOKEN = config_manager.get("SECURITY", "SECRET_TOKEN")
    g.ALLOWED_LOG_FILES = config_manager.get("LOG_VIEWER", "ALLOWED_LOG_FILES", [])
    g.LOG_DIR = config_manager.get("LOG_VIEWER", "LOG_DIR", "logs")
    g.LINES_TO_SHOW = config_manager.get("LOG_VIEWER", "LINES_TO_SHOW", 500)

# --- 辅助函数 ---
def read_log_file(filename):
    """高效地读取日志文件的最后N行。"""
    filepath = os.path.join(g.LOG_DIR, filename)
    if not os.path.exists(filepath):
        return f"错误：日志文件 '{filepath}' 不存在。"
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            last_lines = deque(f, g.LINES_TO_SHOW)
            return "".join(last_lines)
    except Exception as e:
        return f"读取文件时发生错误: {e}"

# --- 路由 ---

@app.route('/update-cookie', methods=['POST'])
def update_cookie():
    auth_token = request.headers.get('X-Auth-Token')
    if auth_token != g.SECRET_TOKEN:
        abort(403)
    
    new_cookie = request.get_json().get('cookie')
    if not new_cookie:
        return jsonify({"status": "error", "message": "Cookie is empty"}), 400
    
    logging.info(f"成功接收到新的Cookie: ...{new_cookie[-20:]}")
    try:
        if os.path.exists(BOOKING_CONFIG_PATH):
            with open(BOOKING_CONFIG_PATH, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {}
        config_data['cookie'] = new_cookie
        with open(BOOKING_CONFIG_PATH, 'w') as f:
            json.dump(config_data, f, indent=2)
        logging.info(f"'{BOOKING_CONFIG_PATH}' 中的Cookie已成功更新！")
        return jsonify({"status": "success", "message": "Cookie updated successfully"}), 200
    except Exception as e:
        logging.error(f"更新抢票配置文件时发生错误: {e}")
        return jsonify({"status": "error", "message": "Internal Server Error"}), 500

@app.route('/logs', methods=['GET'])
def list_logs():
    token = request.args.get('token')
    if token != g.SECRET_TOKEN:
        abort(403)
    
    html = "<h1>可选日志文件</h1><ul>"
    for filename in g.ALLOWED_LOG_FILES:
        html += f'<li><a href="/logs/view/{filename}?token={token}">{filename}</a></li>'
    html += "</ul>"
    return html

@app.route('/logs/view/<filename>', methods=['GET'])
def view_log(filename):
    token = request.args.get('token')
    if token != g.SECRET_TOKEN:
        abort(403)
    
    if filename not in g.ALLOWED_LOG_FILES:
        abort(404)
    
    log_content = read_log_file(filename)
    return render_template('log_viewer.html', log_content=log_content, filename=filename, token=token)

@app.route('/api/logs/<filename>', methods=['GET'])
def get_log_api(filename):
    token = request.args.get('token')
    if token != g.SECRET_TOKEN:
        abort(403)
    
    if filename not in g.ALLOWED_LOG_FILES:
        abort(404)
        
    log_content = read_log_file(filename)
    return Response(log_content, mimetype='text/plain')

if __name__ == '__main__':
    # 从配置管理器启动服务
    host = config_manager.get("SERVER_SETTINGS", "HOST", "0.0.0.0")
    port = config_manager.get("SERVER_SETTINGS", "PORT", 5000)
    app.run(host=host, port=port, debug=False)