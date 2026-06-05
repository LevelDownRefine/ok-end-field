// ==UserScript==
// @name         终末地坐标转发工具(国服+国际服)
// @namespace    http://tampermonkey.net/
// @version      2026-06-05
// @description  转发游戏原始WebSocket JSON包到本地WS服务器，并自动恢复位置同步
// @author       LinTx (modified by Grok + ChatGPT)
// @match        https://game.skland.com/map/endfield*
// @match        https://game.skport.com/map/endfield*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    let ws = null;
    let reconnectTimer = null;

    const RECONNECT_INTERVAL = 3000;

    // 最后收到非心跳消息时间
    let lastMessageTime = Date.now();

    // =========================
    // 本地WS连接
    // =========================

    function connectToLocalServer() {

        if (ws && (
            ws.readyState === WebSocket.OPEN ||
            ws.readyState === WebSocket.CONNECTING
        )) {
            return;
        }

        try {

            ws = new WebSocket('ws://localhost:3001');

            ws.onopen = () => {
                console.log(
                    '[坐标转发] 已连接到本地服务器 ws://localhost:3001'
                );
            };

            ws.onclose = () => {

                console.log(
                    '[坐标转发] 本地WS断开，准备重连...'
                );

                scheduleReconnect();
            };

            ws.onerror = (err) => {

                console.log(
                    '[坐标转发] 本地WS错误',
                    err
                );
            };

        } catch (e) {

            console.error(
                '[坐标转发] 创建本地WS失败',
                e
            );

            scheduleReconnect();
        }
    }

    function scheduleReconnect() {

        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
        }

        reconnectTimer = setTimeout(
            connectToLocalServer,
            RECONNECT_INTERVAL
        );
    }

    // =========================
    // 转发原始JSON
    // =========================

    function sendRawPacket(rawData) {

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            return;
        }

        try {

            ws.send(rawData);

        } catch (e) {

            console.error(
                '[坐标转发] 转发失败',
                e
            );
        }
    }

    // =========================
    // 自动开启位置同步
    // =========================

    function clickLocationSyncOpen() {

        try {

            // ---------------------
            // 新版组件（国服/国际服）
            // ---------------------

            const row = document.querySelector(
                '[class*="PointSwitch__SwitchRow"]'
            );

            if (row) {

                const btn = row.querySelector(
                    '[class*="PointSwitch__ToggleBtn"]'
                );

                if (btn) {

                    btn.click();

                    console.log(
                        '[坐标转发] 已点击位置同步(新版组件)'
                    );

                    return true;
                }
            }
            return false;

        } catch (e) {

            console.error(
                '[坐标转发] 点击位置同步失败',
                e
            );

            return false;
        }
    }

    // =========================
    // 启动时自动开启一次
    // =========================

    function ensureLocationSyncEnabled() {

        const timer = setInterval(() => {

            if (clickLocationSyncOpen()) {

                clearInterval(timer);
            }

        }, 1000);

        setTimeout(() => {

            clearInterval(timer);

        }, 30000);
    }

    // =========================
    // 超时恢复
    // =========================

    function startHeartbeatMonitor() {

        setInterval(() => {

            const now = Date.now();

            if (
                now - lastMessageTime >= 5000
            ) {

                console.log(
                    '[坐标转发] 超过5秒未收到有效消息，尝试恢复位置同步'
                );

                clickLocationSyncOpen();

                // 防止连续狂点
                lastMessageTime = now;
            }

        }, 1000);
    }

    // =========================
    // 判断是否为地图WS
    // =========================

    function isEndfieldMapSocket(url) {

        if (!url) {
            return false;
        }

        return /\/ws\/v1\/game\/endfield\/map/.test(url);
    }

    // =========================
    // 拦截 WebSocket
    // =========================

    const originalAddEventListener =
        WebSocket.prototype.addEventListener;

    WebSocket.prototype.addEventListener = function (
        type,
        listener,
        options
    ) {

        if (
            type === 'message' &&
            isEndfieldMapSocket(this.url)
        ) {

            return Reflect.apply(
                originalAddEventListener,
                this,
                [
                    type,
                    (ev) => {

                        try {

                            const data =
                                JSON.parse(ev.data);

                            // 忽略心跳包
                            if (data.type !== 4) {

                                lastMessageTime =
                                    Date.now();

                                sendRawPacket(ev.data);
                            }

                            if (
                                data.type === 1012 &&
                                data.data &&
                                data.data.pos
                            ) {

                                const pos =
                                    data.data.pos;

                                console.log(
                                    `[坐标转发] 玩家位置: ` +
                                    `x=${pos.x.toFixed(2)}, ` +
                                    `y=${pos.y.toFixed(2)}, ` +
                                    `z=${pos.z.toFixed(2)}`
                                );
                            }

                        } catch (_) {
                            // 忽略解析错误
                        }

                        if (
                            typeof listener ===
                            'function'
                        ) {

                            listener.call(
                                this,
                                ev
                            );

                        } else if (
                            listener &&
                            typeof listener.handleEvent ===
                            'function'
                        ) {

                            listener.handleEvent(
                                ev
                            );
                        }
                    },
                    options
                ]
            );
        }

        return Reflect.apply(
            originalAddEventListener,
            this,
            [type, listener, options]
        );
    };

    // =========================
    // 初始化
    // =========================

    function init() {

        console.log(
            '%c[坐标转发工具] 已加载',
            'color:#0f0;font-weight:bold'
        );

        connectToLocalServer();

        ensureLocationSyncEnabled();

        startHeartbeatMonitor();

        window.addEventListener(
            'beforeunload',
            () => {

                if (ws) {
                    ws.close();
                }
            }
        );
    }

    init();

})();