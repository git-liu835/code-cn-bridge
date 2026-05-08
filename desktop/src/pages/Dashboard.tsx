import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { ProxyStatus, ModelConfig } from '../types';

const Dashboard: React.FC = () => {
  const [status, setStatus] = useState<ProxyStatus | null>(null);
  const [models, setModels] = useState<ModelConfig[]>([]);

  const load = useCallback(async () => {
    try {
      const [s, m] = await Promise.all([api.getStatus(), api.getModels()]);
      setStatus(s);
      setModels(m.models || []);
    } catch {
      setStatus(null);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const uptime = status ? Math.floor(status.stats.uptime_seconds) : 0;
  const uptimeStr = `${Math.floor(uptime / 3600)}h ${Math.floor((uptime % 3600) / 60)}m ${uptime % 60}s`;

  return (
    <div className="page">
      <h2>仪表板</h2>

      <div className="cards-row">
        <div className="card status-card">
          <h3>代理状态</h3>
          <div className={`status-badge ${status?.running ? 'running' : 'stopped'}`}>
            {status?.running ? '运行中' : '已停止'}
          </div>
          {status?.running && (
            <div className="card-detail">
              <div>运行时间: {uptimeStr}</div>
              <div>版本: {status.version}</div>
            </div>
          )}
        </div>

        <div className="card stats-card">
          <h3>请求统计</h3>
          <div className="stats-grid">
            <div className="stat">
              <span className="stat-num">{status?.stats.request_count ?? 0}</span>
              <span className="stat-label">总请求</span>
            </div>
            <div className="stat success">
              <span className="stat-num">{status?.stats.success_count ?? 0}</span>
              <span className="stat-label">成功</span>
            </div>
            <div className="stat error">
              <span className="stat-num">{status?.stats.error_count ?? 0}</span>
              <span className="stat-label">失败</span>
            </div>
            <div className="stat">
              <span className="stat-num">{status?.stats.avg_latency_ms ?? 0}ms</span>
              <span className="stat-label">平均延迟</span>
            </div>
          </div>
        </div>
      </div>

      <h3>模型健康状态</h3>
      <div className="model-health-grid">
        {models.length === 0 && <p className="muted">尚未配置任何模型，前往"模型配置"添加。</p>}
        {models.map((m) => (
          <div key={m.alias} className="health-card">
            <div className="health-card-header">
              <span className={`dot ${m.enabled ? 'running' : 'stopped'}`} />
              <strong>{m.alias}</strong>
            </div>
            <div className="health-card-body">
              <div>{m.target_model}</div>
              <div className="muted">{m.provider} / {m.adapter}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="quick-actions">
        <button className="btn btn-primary" onClick={load}>刷新状态</button>
      </div>
    </div>
  );
};

export default Dashboard;
