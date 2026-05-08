import React from 'react';
import { useApp } from '../App';

interface Props {
  proxyRunning: boolean;
  port: number;
  requestCount: number;
}

const StatusBar: React.FC<Props> = ({ proxyRunning, port, requestCount }) => {
  const { tl } = useApp();
  return (
    <footer className="status-bar">
      <span className={`status-indicator ${proxyRunning ? 'running' : 'stopped'}`} />
      <span>{tl('status.port')}: {port}</span>
      <span className="status-separator">|</span>
      <span>{tl('status.requests')}: {requestCount}</span>
    </footer>
  );
};

export default StatusBar;
