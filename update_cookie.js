// ==UserScript==
// @name         西电体育馆Cookie自动同步器
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  自动检测并发送最新的Cookie到指定的服务器，用于自动化抢票脚本。
// @author       YourName
// @match        https://tybsouthgym.xidian.edu.cn/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_xmlhttpRequest
// @connect      120.27.130.202
// ==/UserScript==

(function() {
    'use strict';

    // --- 配置区 ---
    // 你的服务器地址和端口
    const SERVER_URL = 'http://120.27.130.202:5000/update-cookie';
    // 必须与服务器端 cookie_listener.py 中设置的 SECRET_TOKEN 完全一致
    const SECRET_TOKEN = 'YourSuperSecretTokenGoesHere_ChangeMe';

    // --- 主逻辑 ---
    console.log('Cookie自动同步脚本已启动...');

    const currentCookie = document.cookie;
    const lastSentCookie = GM_getValue('lastSentCookie', ''); // 从油猴存储中读取上次发送的cookie

    // 检查Cookie是否存在，并且是否与上次发送的不同
    if (currentCookie && currentCookie !== lastSentCookie) {
        console.log('检测到新的或已更新的Cookie，准备发送...');

        GM_xmlhttpRequest({
            method: 'POST',
            url: SERVER_URL,
            headers: {
                'Content-Type': 'application/json',
                'X-Auth-Token': SECRET_TOKEN // 发送安全令牌
            },
            data: JSON.stringify({ cookie: currentCookie }),
            onload: function(response) {
                if (response.status === 200) {
                    console.log('Cookie发送成功！服务器响应:', response.responseText);
                    // 发送成功后，将当前cookie保存到油猴存储中，防止重复发送
                    GM_setValue('lastSentCookie', currentCookie);
                } else {
                    console.error('Cookie发送失败！服务器状态:', response.status, '响应:', response.responseText);
                }
            },
            onerror: function(response) {
                console.error('发生网络错误或服务器无响应。', response);
            }
        });

    } else if (!currentCookie) {
        console.log('当前页面没有Cookie。');
    } else {
        console.log('Cookie未发生变化，无需发送。');
    }
})();