import React from 'react';

const About: React.FC = () => (
  <div className="page">
    <h2>关于 code CN Bridge</h2>

    <div className="about-card">
      <div className="about-logo">&#9653;</div>
      <h3>code CN Bridge</h3>
      <p className="version">v0.1.0</p>
      <p className="about-desc">
        本地代理工具，将 OpenAI Responses API 翻译为 Chat Completions API，
        使 code CLI 无缝接入通义千问、DeepSeek、Kimi 等国产大模型。
      </p>

      <div className="about-features">
        <div className="feature">
          <strong>协议转换</strong>
          <p>Responses API ↔ Chat Completions API 双向转换，支持流式输出</p>
        </div>
        <div className="feature">
          <strong>多模型支持</strong>
          <p>内置通义千问、DeepSeek、Kimi 适配器，支持自定义扩展</p>
        </div>
        <div className="feature">
          <strong>桌面管理</strong>
          <p>Electron 桌面应用，系统托盘驻留，图形化管理所有配置</p>
        </div>
      </div>

      <div className="about-links">
        <a href="#" onClick={(e) => {
          e.preventDefault();
          window.electronAPI?.openExternal('https://github.com/anthropics/claude-code');
        }}>
          项目主页
        </a>
        <span className="separator">|</span>
        <a href="#" onClick={(e) => {
          e.preventDefault();
          window.electronAPI?.openExternal('https://github.com/anthropics/claude-code/issues');
        }}>
          问题反馈
        </a>
      </div>

      <p className="muted" style={{ marginTop: 16 }}>
        License: MIT | Built with Electron + React + FastAPI
      </p>
    </div>
  </div>
);

export default About;
