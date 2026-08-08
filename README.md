# Delivery Status Tracker

## Quick start

## Architecture

<svg viewBox="0 0 680 380" width="100%" role="img">
  <title>Delivery Status Tracker 系统架构</title>
  <desc>三层架构：React 前端、FastAPI 后端、PostgreSQL 数据库，以及 CSV 数据导入流程</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>

<text x="340" y="28" text-anchor="middle" style="font-size:15px;font-weight:500;fill:#2C2C2A">Delivery Status Tracker — 系统架构</text>

  <g class="c-blue">
    <rect x="40" y="60" width="160" height="70" rx="12" fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
    <text x="120" y="88" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#0C447C">React Web UI</text>
    <text x="120" y="108" text-anchor="middle" style="font-size:12px;fill:#378ADD">Vite + React Query</text>
  </g>

  <g class="c-purple">
    <rect x="260" y="60" width="160" height="70" rx="12" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
    <text x="340" y="88" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#3C3489">FastAPI Backend</text>
    <text x="340" y="108" text-anchor="middle" style="font-size:12px;fill:#7F77DD">SQLAlchemy + Pydantic</text>
  </g>

  <g class="c-teal">
    <rect x="480" y="60" width="160" height="70" rx="12" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.5"/>
    <text x="560" y="88" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#085041">PostgreSQL</text>
    <text x="560" y="108" text-anchor="middle" style="font-size:12px;fill:#1D9E75">shipments + history</text>
  </g>

  <line x1="200" y1="95" x2="260" y2="95" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="230" y="85" text-anchor="middle" style="font-size:11px;fill:#5F5E5A">HTTP/JSON</text>

  <line x1="420" y1="95" x2="480" y2="95" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="450" y="85" text-anchor="middle" style="font-size:11px;fill:#5F5E5A">SQL</text>

  <g class="c-amber">
    <rect x="260" y="200" width="160" height="56" rx="8" fill="#FAEEDA" stroke="#854F0B" stroke-width="0.5"/>
    <text x="340" y="222" text-anchor="middle" style="font-size:13px;font-weight:500;fill:#633806">CSV Seed Script</text>
    <text x="340" y="240" text-anchor="middle" style="font-size:12px;fill:#BA7517">shipments.csv → DB</text>
  </g>

  <line x1="340" y1="200" x2="340" y2="130" stroke="#5F5E5A" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arrow)"/>

  <g class="c-gray">
    <rect x="40" y="200" width="160" height="56" rx="8" fill="#F1EFE8" stroke="#5F5E5A" stroke-width="0.5"/>
    <text x="120" y="222" text-anchor="middle" style="font-size:13px;font-weight:500;fill:#444441">pytest</text>
    <text x="120" y="240" text-anchor="middle" style="font-size:12px;fill:#888780">transition + API tests</text>
  </g>

  <line x1="200" y1="228" x2="260" y2="228" stroke="#5F5E5A" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arrow)"/>

  <g class="c-coral">
    <rect x="40" y="300" width="600" height="50" rx="8" fill="#FAECE7" stroke="#993C1D" stroke-width="0.5"/>
    <text x="340" y="322" text-anchor="middle" style="font-size:13px;font-weight:500;fill:#712B13">单命令启动: docker compose up 或 make dev</text>
    <text x="340" y="340" text-anchor="middle" style="font-size:12px;fill:#D85A30">DB + API + UI 全部就绪, CSV 自动加载</text>
  </g>
</svg>

## Status lifecycle

<svg viewBox="0 0 680 320" width="100%" role="img">
  <title>货物状态流转状态机</title>
  <desc>状态生命周期：created → picked_up → in_transit → delivered，任何非 delivered 状态均可转为 failed</desc>
  <defs>
    <marker id="arrow2" viewBox="0 0 10 10" refX="8" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>

<text x="340" y="28" text-anchor="middle" style="font-size:15px;font-weight:500;fill:#2C2C2A">Status lifecycle — 状态流转状态机</text>

  <g class="c-blue">
    <rect x="40" y="100" width="120" height="56" rx="8" fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
    <text x="100" y="122" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#0C447C">created</text>
    <text x="100" y="140" text-anchor="middle" style="font-size:11px;fill:#378ADD">已创建</text>
  </g>

  <g class="c-purple">
    <rect x="200" y="100" width="120" height="56" rx="8" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
    <text x="260" y="122" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#3C3489">picked_up</text>
    <text x="260" y="140" text-anchor="middle" style="font-size:11px;fill:#7F77DD">已取件</text>
  </g>

  <g class="c-amber">
    <rect x="360" y="100" width="120" height="56" rx="8" fill="#FAEEDA" stroke="#854F0B" stroke-width="0.5"/>
    <text x="420" y="122" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#633806">in_transit</text>
    <text x="420" y="140" text-anchor="middle" style="font-size:11px;fill:#BA7517">运输中</text>
  </g>

  <g class="c-teal">
    <rect x="520" y="100" width="120" height="56" rx="8" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.5"/>
    <text x="580" y="122" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#085041">delivered</text>
    <text x="580" y="140" text-anchor="middle" style="font-size:11px;fill:#1D9E75">已送达 (终态)</text>
  </g>

  <line x1="160" y1="128" x2="200" y2="128" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <line x1="320" y1="128" x2="360" y2="128" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#arrow2)"/>
  <line x1="480" y1="128" x2="520" y2="128" stroke="#5F5E5A" stroke-width="1.5" marker-end="url(#arrow2)"/>

  <g class="c-red">
    <rect x="280" y="220" width="120" height="56" rx="8" fill="#FCEBEB" stroke="#A32D2D" stroke-width="0.5"/>
    <text x="340" y="242" text-anchor="middle" style="font-size:14px;font-weight:500;fill:#791F1F">failed</text>
    <text x="340" y="260" text-anchor="middle" style="font-size:11px;fill:#E24B4A">异常 (终态)</text>
  </g>

  <path d="M100 156 Q 100 220 280 248" fill="none" stroke="#A32D2D" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arrow2)"/>
  <path d="M260 156 Q 260 200 280 235" fill="none" stroke="#A32D2D" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arrow2)"/>
  <path d="M420 156 Q 420 200 400 235" fill="none" stroke="#A32D2D" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arrow2)"/>

<text x="180" y="200" style="font-size:11px;fill:#A32D2D">任意非 delivered 状态 → failed</text>
</svg>

## Testing

## Key decisions

## AI usage note

## Todo
