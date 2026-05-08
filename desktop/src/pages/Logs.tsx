import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../services/api';
import type { RequestLogEntry } from '../types';

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<RequestLogEntry[]>([]);
  const [paused, setPaused] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // 初始加载历史日志
  useEffect(() => {
    (async () => {
      try {
        const res = await api.getLogs(200);
        setLogs(res.logs || []);
      } catch { /* ignore */ }
    })();
  }, []);

  // WebSocket 实时日志
  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    const connect = () => {
      try {
        ws = new WebSocket('ws://localhost:8765/admin/api/logs/stream');
        wsRef.current = ws;

        ws.onopen = () => setConnected(true);
        ws.onclose = () => { setConnected(false); reconnectTimer = setTimeout(connect, 3000); };
        ws.onerror = () => ws?.close();

        ws.onmessage = (event) => {
          try {
            const entry = JSON.parse(event.data);
            if (!paused) {
              setLogs((prev) => [entry, ...prev].slice(0, 500));
            }
          } catch { /* ignore */ }
        };
      } catch {
        reconnectTimer = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, [paused]);

  const handleClear = async () => {
    try {
      await api.clearLogs();
      setLogs([]);
    } catch { /* ignore */ }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h2>监控日志
          <span className={`ws-indicator ${connected ? 'running' : 'stopped'}`}>
            {connected ? '实时' : '断开'}
          </span>
        </h2>
        <div className="btn-row">
          <button className={`btn btn-sm ${paused ? 'btn-primary' : ''}`}
            onClick={() => setPaused(!paused)}>
            {paused ? '继续' : '暂停'}
          </button>
          <button className="btn btn-sm btn-danger" onClick={handleClear}>清空</button>
        </div>
      </div>

      <div className="log-list" ref={listRef}>
        {logs.length === 0 && <p className="muted">暂无请求日志</p>}
        {logs.map((log, i) => (
          <div key={i} className={`log-entry ${log.status_code >= 400 ? 'error' : ''}`}>
            <span className="log-time">{log.time}</span>
            <span className={`log-badge ${log.status_code < 400 ? 'running' : 'stopped'}`}>
              {log.status_code}
            </span>
            <span className="log-model">{log.model}</span>
            {log.provider && <span className="log-provider">{log.provider}/{log.target_model}</span>}
            <span className="log-endpoint">{log.endpoint}</span>
            <span className="log-elapsed">{log.elapsed_ms}ms</span>
            {log.tokens > 0 && <span className="log-tokens">{log.tokens} tokens</span>}
            {log.error && <span className="log-error">{log.error}</span>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Logs;
