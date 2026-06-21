import { useEffect, useRef, useCallback, useState } from 'react';
import type { ThemeMode } from '@/theme';

/**
 * WebSocket Hook
 * 支持多频道订阅、心跳、重连降级
 */

interface WSSubscription {
  channel: 'market' | 'signals' | 'backtest' | 'orders' | 'risk';
  symbols?: string[];
}

interface WSMessage {
  type: string;
  channel: string;
  payload: unknown;
  timestamp: string;
}

interface UseWebSocketReturn {
  connected: boolean;
  channels: string[];
  lastMessage: WSMessage | null;
  subscribe: (sub: WSSubscription) => void;
  unsubscribe: (channel: string) => void;
  send: (data: Record<string, unknown>) => void;
}

const RECONNECT_DELAYS = [1000, 2000, 4000, 8000, 16000, 30000]; // 指数退避
const HEARTBEAT_INTERVAL = 30000; // 30s
const MAX_RECONNECT_ATTEMPTS = 5;

export function useWebSocket(
  initialChannels: string[] = [],
  themeMode: ThemeMode = 'dark'
): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [channels, setChannels] = useState<string[]>(initialChannels);
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const heartbeatTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.host}/ws/multi`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WS] 连接成功');
      setConnected(true);
      reconnectAttempts.current = 0;

      // 发送初始订阅
      channels.forEach((ch) => {
        ws.send(JSON.stringify({ action: 'subscribe', channel: ch }));
      });

      // 启动心跳
      startHeartbeat();
    };

    ws.onmessage = (event) => {
      try {
        const data: WSMessage = JSON.parse(event.data);
        setLastMessage(data);
      } catch (e) {
        console.error('[WS] 消息解析失败', e);
      }
    };

    ws.onclose = () => {
      console.log('[WS] 连接关闭');
      setConnected(false);
      stopHeartbeat();

      // 重连
      if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_DELAYS[Math.min(reconnectAttempts.current, RECONNECT_DELAYS.length - 1)];
        console.log(`[WS] ${delay}ms 后重连...`);
        reconnectTimer.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, delay);
      }
    };

    ws.onerror = (error) => {
      console.error('[WS] 错误', error);
    };
  }, [channels]);

  const startHeartbeat = useCallback(() => {
    stopHeartbeat();
    heartbeatTimer.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL);
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatTimer.current) {
      clearInterval(heartbeatTimer.current);
      heartbeatTimer.current = null;
    }
  }, []);

  const subscribe = useCallback((sub: WSSubscription) => {
    const ch = sub.channel;
    if (!channels.includes(ch)) {
      setChannels((prev) => [...prev, ch]);
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'subscribe', ...sub }));
      }
    }
  }, [channels]);

  const unsubscribe = useCallback((channel: string) => {
    setChannels((prev) => prev.filter((ch) => ch !== channel));
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'unsubscribe', channel }));
    }
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  // 初始连接
  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      stopHeartbeat();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    connected,
    channels,
    lastMessage,
    subscribe,
    unsubscribe,
    send,
  };
}
