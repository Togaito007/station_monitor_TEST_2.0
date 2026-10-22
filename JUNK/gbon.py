import math
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="GBON Station Monitor Dashboard", version="1.0.0")


def render_dashboard_html() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GBON Station Surveillance Dashboard</title>
    <style>
        :root {
            --bg: #07111f;
            --bg-alt: #0d1b2c;
            --panel: rgba(16, 28, 45, 0.88);
            --panel-strong: rgba(12, 22, 36, 0.96);
            --line: rgba(148, 163, 184, 0.18);
            --text: #e5edf7;
            --muted: #9bb0c5;
            --green: #2dd4bf;
            --green-soft: rgba(45, 212, 191, 0.12);
            --orange: #fbbf24;
            --orange-soft: rgba(251, 191, 36, 0.14);
            --red: #f87171;
            --red-soft: rgba(248, 113, 113, 0.12);
            --blue: #60a5fa;
            --shadow: 0 18px 42px rgba(2, 6, 23, 0.45);
            --card-front: rgba(12, 23, 38, 0.9);
            --card-back: rgba(13, 20, 31, 0.96);
            --surface: rgba(15, 23, 42, 0.6);
            --toggle-bg: rgba(15, 23, 42, 0.7);
            --toggle-text: #e5edf7;
            --warning-bg: rgba(120, 52, 14, 0.14);
        }

        body.light-mode {
            --bg: #edf4ff;
            --bg-alt: #dfeafc;
            --panel: rgba(255, 255, 255, 0.9);
            --panel-strong: rgba(255, 255, 255, 0.98);
            --line: rgba(51, 65, 85, 0.12);
            --text: #142033;
            --muted: #52657d;
            --green: #0f9f8b;
            --green-soft: rgba(15, 159, 139, 0.12);
            --orange: #d97706;
            --orange-soft: rgba(217, 119, 6, 0.12);
            --red: #dc2626;
            --red-soft: rgba(220, 38, 38, 0.10);
            --blue: #2563eb;
            --shadow: 0 18px 42px rgba(15, 23, 42, 0.12);
            --card-front: rgba(255, 255, 255, 0.96);
            --card-back: rgba(243, 247, 255, 0.98);
            --surface: rgba(255, 255, 255, 0.7);
            --toggle-bg: rgba(226, 232, 240, 0.9);
            --toggle-text: #0f172a;
            --warning-bg: rgba(253, 230, 138, 0.22);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: Inter, "Segoe UI", Roboto, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(59,130,246,0.18), transparent 25%),
                radial-gradient(circle at bottom right, rgba(16,185,129,0.12), transparent 30%),
                var(--bg);
            color: var(--text);
            transition: background 0.25s ease, color 0.25s ease;
        }

        .shell {
            max-width: 1500px;
            margin: 0 auto;
            padding: 32px 20px 48px;
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
            gap: 16px;
            flex-wrap: wrap;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-mark {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--green), var(--blue));
            box-shadow: 0 0 18px rgba(45, 212, 191, 0.8);
        }

        h1 {
            margin: 0;
            font-size: clamp(1.8rem, 2vw, 2.5rem);
            letter-spacing: 0.02em;
        }

        .top-actions {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .filter-box {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--text);
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 9px 12px;
            box-shadow: var(--shadow);
        }

        .filter-box label {
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
        }

        .filter-box select {
            background: transparent;
            color: var(--text);
            border: none;
            outline: none;
            font-size: 0.82rem;
            font-weight: 600;
            padding: 4px 2px;
            min-width: 120px;
        }

        .refresh-box, .theme-toggle {
            border: 1px solid var(--line);
            background: var(--surface);
            color: var(--text);
            border-radius: 999px;
            padding: 10px 14px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            box-shadow: var(--shadow);
        }

        .refresh-box {
            min-width: 220px;
            justify-content: center;
        }

        .refresh-box .label {
            opacity: 0.8;
        }

        .refresh-box .value {
            font-weight: 700;
        }

        .theme-toggle {
            cursor: pointer;
            background: var(--toggle-bg);
            color: var(--toggle-text);
            border: 1px solid var(--line);
            transition: transform 0.2s ease;
        }

        .theme-toggle:hover {
            transform: translateY(-1px);
        }

        .status-pills {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .pill {
            padding: 10px 14px;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(15, 23, 42, 0.7);
            color: var(--muted);
            font-size: 0.82rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        body.light-mode .pill {
            background: rgba(255, 255, 255, 0.65);
        }

        .pill .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 22px;
        }

        .card {
            background: linear-gradient(180deg, rgba(15, 23, 42, 0.9), rgba(11, 17, 27, 0.96));
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: var(--shadow);
        }

        body.light-mode .card {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(245,249,255,0.98));
        }

        .stat-card {
            padding: 18px 20px;
            min-height: 110px;
        }

        .stat-label {
            color: var(--muted);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .stat-value {
            margin-top: 14px;
            font-size: clamp(1.7rem, 2vw, 2.4rem);
            font-weight: 700;
            line-height: 1;
        }

        .layout {
            display: grid;
            grid-template-columns: minmax(0, 1.8fr) minmax(260px, 0.9fr);
            gap: 22px;
        }

        .panel {
            padding: 18px 18px 14px;
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            gap: 10px;
        }

        .panel-header h2 {
            margin: 0;
            font-size: 1.02rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--muted);
            font-weight: 700;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
        }

        .station-card {
            perspective: 1200px;
            min-height: 320px;
            cursor: pointer;
        }

        .station-card-inner {
            position: relative;
            width: 100%;
            min-height: 320px;
            transform-style: preserve-3d;
            transition: transform 0.7s ease;
        }

        .station-card.is-flipped .station-card-inner {
            transform: rotateY(180deg);
        }

        .station-card-front,
        .station-card-back {
            position: absolute;
            inset: 0;
            min-height: 320px;
            backface-visibility: hidden;
            -webkit-backface-visibility: hidden;
            border-radius: 18px;
            border: 1px solid var(--line);
            background: linear-gradient(180deg, var(--card-front), rgba(7,16,25,0.96));
            box-shadow: var(--shadow);
            padding: 16px;
        }

        body.light-mode .station-card-front,
        body.light-mode .station-card-back {
            background: linear-gradient(180deg, var(--card-front), rgba(234,241,255,0.96));
        }

        .station-card-back {
            transform: rotateY(180deg);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .station-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }

        .station-name {
            font-size: 1.08rem;
            font-weight: 700;
            line-height: 1.4;
            word-break: break-word;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            border-radius: 999px;
            padding: 7px 10px;
            font-size: 0.71rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            font-weight: 700;
            border: 1px solid transparent;
        }

        .badge::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            background: currentColor;
            box-shadow: 0 0 8px currentColor;
        }

        .badge.up {
            color: var(--green);
            background: var(--green-soft);
            border-color: rgba(45, 212, 191, 0.3);
        }

        .badge.down {
            color: var(--red);
            background: var(--red-soft);
            border-color: rgba(248, 113, 113, 0.34);
        }

        .badge.unknown {
            color: var(--orange);
            background: var(--orange-soft);
            border-color: rgba(251, 191, 36, 0.34);
        }

        .station-ip {
            font-size: 0.78rem;
            color: var(--muted);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }

        .station-ip strong {
            color: var(--text);
            font-size: 0.8rem;
        }

        .meta {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 10px 12px;
            margin-top: 8px;
            font-size: 0.88rem;
            color: var(--muted);
        }

        .meta strong {
            color: var(--text);
        }

        .battery {
            font-weight: 700;
        }

        .battery.low {
            color: var(--red);
        }

        .battery.ok {
            color: var(--green);
        }

        .data-list {
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid var(--line);
            display: grid;
            gap: 8px;
        }

        .data-item {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            font-size: 0.82rem;
            color: var(--muted);
        }

        .data-item .label {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .data-item .value {
            color: var(--text);
            font-weight: 600;
            text-align: right;
        }

        .missing {
            color: var(--red);
            font-weight: 700;
        }

        .card-back-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.74rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 12px;
        }

        .backup-list {
            display: grid;
            gap: 12px;
            font-size: 0.9rem;
        }

        .backup-item {
            padding: 10px 12px;
            border-radius: 12px;
            background: rgba(148, 163, 184, 0.08);
            border: 1px solid var(--line);
        }

        .backup-item strong {
            display: block;
            margin-top: 4px;
            color: var(--text);
        }

        .card-hint {
            font-size: 0.76rem;
            text-align: center;
            color: var(--muted);
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .alert-panel {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .alert-box {
            border-radius: 14px;
            border: 1px solid var(--line);
            background: rgba(15, 23, 42, 0.82);
            padding: 12px 14px;
        }

        .alert-box.warning {
            border-color: rgba(251, 191, 36, 0.35);
            background: var(--warning-bg);
        }

        .alert-box.error {
            border-color: rgba(248, 113, 113, 0.32);
            background: rgba(69, 10, 10, 0.18);
        }

        .alert-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 6px;
            font-weight: 700;
        }

        .alert-title .tag {
            font-size: 0.7rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 4px 7px;
            border-radius: 999px;
        }

        .alert-box.warning .tag {
            background: rgba(251, 191, 36, 0.16);
            color: var(--orange);
        }

        .alert-box.error .tag {
            background: rgba(248, 113, 113, 0.15);
            color: var(--red);
        }

        .alert-content {
            font-size: 0.9rem;
            color: var(--text);
            line-height: 1.5;
        }

        .empty-state {
            padding: 18px;
            border: 1px dashed rgba(148, 163, 184, 0.35);
            border-radius: 14px;
            text-align: center;
            color: var(--muted);
            background: rgba(15, 23, 42, 0.36);
        }

        @media (max-width: 980px) {
            .layout {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 620px) {
            .stats {
                grid-template-columns: repeat(2, minmax(140px, 1fr));
            }
        }
    </style>
</head>
<body>
    <div class="toast-container" id="toastContainer"></div>
    <div class="shell">
        <div class="topbar">
            <div class="brand">
                <span class="brand-mark"></span>
                <h1>GBON Surveillance Dashboard</h1>
            </div>

            <div class="top-actions">
                <div class="filter-box">
                    <label for="statusFilter">Filter</label>
                    <select id="statusFilter">
                        <option value="all">All</option>
                        <option value="up">Up Only</option>
                        <option value="down">Down Only</option>
                    </select>
                </div>
                <div class="refresh-box"><span class="label">Current Time</span> <span class="value" id="currentTime">--:--:--</span></div>
                <div class="refresh-box"><span class="label">Last Checked</span> <span class="value" id="lastChecked">--:--:--</span></div>
                <button id="themeToggle" class="theme-toggle" type="button">🌙 Dark</button>
            </div>
        </div>

        <div class="status-pills">
            <span class="pill"><span class="dot" style="background: var(--green);"></span>Live Feed</span>
            <span class="pill"><span class="dot" style="background: var(--blue);"></span>Auto Refresh</span>
        </div>

        <div class="stats" style="margin-top: 18px;">
            <div class="card stat-card">
                <div class="stat-label">Stations</div>
                <div class="stat-value" id="totalStations">0</div>
            </div>
            <div class="card stat-card">
                <div class="stat-label">Online</div>
                <div class="stat-value" id="onlineStations" style="color: var(--green);">0</div>
            </div>
            <div class="card stat-card">
                <div class="stat-label">Alerts</div>
                <div class="stat-value" id="alertCount" style="color: var(--red);">0</div>
            </div>
            <div class="card stat-card">
                <div class="stat-label">Notifications</div>
                <div class="stat-value" id="notificationCount" style="color: var(--orange);">0</div>
            </div>
        </div>

        <div class="layout">
            <div class="card panel">
                <div class="panel-header">
                    <h2>Monitored Stations</h2>
                </div>
                <div id="stationsGrid" class="grid"></div>
            </div>

            <div class="card panel">
                <div class="panel-header">
                    <h2>Alerts & Notifications</h2>
                </div>
                <div id="alertsPanel" class="alert-panel"></div>
            </div>
        </div>
    </div>

    <script>
        const themeToggle = document.getElementById('themeToggle');
        const currentTimeElement = document.getElementById('currentTime');
        const lastCheckedElement = document.getElementById('lastChecked');
        const statusFilter = document.getElementById('statusFilter');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        function applyStoredTheme() {
            const saved = localStorage.getItem('gbon-theme');
            const useLight = saved ? saved === 'light' : !prefersDark;
            document.body.classList.toggle('light-mode', useLight);
            themeToggle.textContent = useLight ? '☀️ Light' : '🌙 Dark';
        }

        function updateCurrentTime() {
            currentTimeElement.textContent = new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }

        function updateLastCheckedTime(stations) {
            if (!stations || !stations.length) {
                lastCheckedElement.textContent = '--:--:--';
                return;
            }

            const latest = stations
                .map(s => new Date(s.last_checked))
                .filter(date => !isNaN(date))
                .sort((a, b) => b - a)[0];

            if (!latest) {
                lastCheckedElement.textContent = '--:--:--';
                return;
            }

            lastCheckedElement.textContent = latest.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }

        themeToggle.addEventListener('click', () => {
            const isLight = document.body.classList.toggle('light-mode');
            localStorage.setItem('gbon-theme', isLight ? 'light' : 'dark');
            themeToggle.textContent = isLight ? '☀️ Light' : '🌙 Dark';
        });

        statusFilter.addEventListener('change', () => {
            loadDashboard();
        });

        function parseStationIp(url) {
            try {
                const parsed = new URL(url);
                return parsed.hostname || 'Unknown';
            } catch (error) {
                return url || 'Unknown';
            }
        }

        function isMissingValue(value) {
            if (value === null || value === undefined) return true;
            if (typeof value === 'string' && value.trim() === '') return true;
            if (typeof value === 'string' && ['nan', 'none', 'null'].includes(value.trim().toLowerCase())) return true;
            if (typeof value === 'number' && Number.isNaN(value)) return true;
            return false;
        }

        function formatValue(value) {
            if (value === null || value === undefined) return 'Missing';
            if (typeof value === 'number') {
                if (Number.isNaN(value)) return 'Missing';
                if (Number.isInteger(value)) return value.toString();
                return value.toFixed(2);
            }
            if (typeof value === 'string') {
                if (['nan', 'none', 'null'].includes(value.trim().toLowerCase())) return 'Missing';
                return value;
            }
            return String(value);
        }

        function summariseMissingData(data) {
            const missing = [];
            if (!data || typeof data !== 'object') return missing;
            for (const [key, value] of Object.entries(data)) {
                if (isMissingValue(value)) {
                    missing.push({ key, value });
                }
            }
            return missing;
        }

        function getBatteryDisplay(station) {
            const voltage = Number(station.battery_voltage);
            if (station.status === 'down') {
                return { text: 'Unavailable', className: 'battery ok', color: 'var(--muted)' };
            }
            if (!Number.isFinite(voltage)) {
                return { text: 'N/A', className: 'battery ok', color: 'var(--muted)' };
            }
            const isLow = voltage <= 11.0;
            return {
                text: `${voltage.toFixed(2)} V`,
                className: isLow ? 'battery low' : 'battery ok',
                color: isLow ? 'var(--red)' : 'var(--green)'
            };
        }

        function renderStationCard(station) {
            const data = station.data || {};
            const missing = summariseMissingData(data);
            const batteryInfo = getBatteryDisplay(station);
            const ip = parseStationIp(station.url);
            const dataItems = Object.entries(data).slice(0, 6).map(([key, value]) => {
                const isMissing = isMissingValue(value);
                const display = formatValue(value);
                return `
                    <div class="data-item">
                        <span class="label">${key}</span>
                        <span class="value ${isMissing ? 'missing' : ''}">${display}</span>
                    </div>
                `;
            }).join('') || '<div class="data-item"><span class="label">No instrument data</span></div>';

            const badgeClass = station.status === 'up' ? 'up' : station.status === 'down' ? 'down' : 'unknown';
            const batteryColor = batteryInfo.color;

            return `
                <article class="station-card" data-station-name="${station.name}">
                    <div class="station-card-inner">
                        <div class="station-card-front">
                            <div class="station-top">
                                <div class="station-name">${station.name}</div>
                                <span class="badge ${badgeClass}">${station.status}</span>
                            </div>
                            <div class="station-ip">
                                <span>IP</span>
                                <strong>${ip}</strong>
                            </div>
                            <div class="meta">
                                <span>Battery</span>
                                <strong class="${batteryInfo.className}" style="color:${batteryColor};">${batteryInfo.text}</strong>
                            </div>
                            <div class="data-list">
                                ${dataItems}
                            </div>
                            ${missing.length ? `<div style="margin-top: 12px; color: var(--red); font-size: 0.8rem; font-weight: 700;">Missing values: ${missing.map(m => m.key).join(', ')}</div>` : ''}
                        </div>

                        <div class="station-card-back">
                            <div>
                                <div class="card-back-header">
                                    <span>Backup info</span>
                                    <span>Station</span>
                                </div>
                                <div class="backup-list">
                                    <div class="backup-item">
                                        <span>Primary station</span>
                                        <strong>${station.name}</strong>
                                    </div>
                                    <div class="backup-item">
                                        <span>Primary IP</span>
                                        <strong>${ip}</strong>
                                    </div>
                                    <div class="backup-item">
                                        <span>Backup station</span>
                                        <strong>Not configured yet</strong>
                                    </div>
                                    <div class="backup-item">
                                        <span>Status</span>
                                        <strong>${station.status}</strong>
                                    </div>
                                </div>
                            </div>
                            <div class="card-hint">Click to flip back</div>
                        </div>
                    </div>
                </article>
            `;
        }

        function renderAlertBox(type, title, message) {
            return `
                <div class="alert-box ${type === 'error' ? 'error' : 'warning'}">
                    <div class="alert-title">
                        <span>${title}</span>
                        <span class="tag">${type === 'error' ? 'alert' : 'notice'}</span>
                    </div>
                    <div class="alert-content">${message}</div>
                </div>
            `;
        }

        async function fetchJson(url) {
            const response = await fetch(url, { cache: 'no-store' });
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        }

        async function loadDashboard() {
            try {
                const [stations, notifications] = await Promise.all([
                    fetchJson(`${window.location.origin}/stations/status`),
                    fetchJson(`${window.location.origin}/notifications`)
                ]);

                const stationList = Array.isArray(stations) ? stations : [];
                const filteredStations = statusFilter.value === 'all'
                    ? stationList
                    : stationList.filter(station => station.status === statusFilter.value);

                const notificationList = Array.isArray(notifications.notifications) ? notifications.notifications : [];

                const total = filteredStations.length;
                const online = filteredStations.filter(s => s.status === 'up').length;
                const alertList = [];

                filteredStations.forEach(station => {
                    const missing = summariseMissingData(station.data || {});
                    if (missing.length) {
                        missing.forEach(item => {
                            alertList.push({
                                type: 'error',
                                title: `${station.name} - Missing data`,
                                message: `Instrument value missing for "${item.key}" in ${station.name}.`
                            });
                        });
                    }

                    const battery = Number(station.battery_voltage);
                    if (station.status === 'up' && Number.isFinite(battery) && battery <= 11.0) {
                        alertList.push({
                            type: 'warning',
                            title: `${station.name} - Low battery`,
                            message: `Battery voltage is ${battery.toFixed(2)} V and is below the 11.0 V threshold.`
                        });
                    }
                });

                notificationList.forEach(item => {
                    if (!item || typeof item !== 'object') return;
                    if (!shouldDisplayNotification(item, 60000)) return;
                    const isInstrument = item.type === 'instrument_down';
                    alertList.push({
                        type: isInstrument ? 'error' : 'warning',
                        title: item.station
                            ? `${item.station}${isInstrument && item.instrument ? ` - ${item.instrument}` : ''}`
                            : 'Station alert',
                        message: item.message || 'Monitoring alert received from the API.'
                    });
                });

                document.getElementById('totalStations').textContent = String(total);
                document.getElementById('onlineStations').textContent = String(online);
                document.getElementById('alertCount').textContent = String(alertList.length);
                document.getElementById('notificationCount').textContent = String(notificationList.length);

                document.getElementById('stationsGrid').innerHTML = filteredStations.length
                    ? filteredStations.map(renderStationCard).join('')
                    : '<div class="empty-state">No stations match the selected filter.</div>';

                const alertsContainer = document.getElementById('alertsPanel');
                alertsContainer.innerHTML = alertList.length
                    ? alertList.map(alert => renderAlertBox(alert.type, alert.title, alert.message)).join('')
                    : '<div class="empty-state">No active alerts. All monitored parameters are healthy.</div>';

                updateLastCheckedTime(filteredStations);

                const events = detectStateTransitions(lastKnownStations, stationList);
                const dedupedEvents = events.filter(event => shouldDisplayStateEvent(event, 60000));
                for (const event of dedupedEvents) {
                    showToast(event.severity, event.title, event.message);
                    notifyDesktop(event.title, event.message);
                }
                lastKnownStations = stationList;
            } catch (error) {
                document.getElementById('stationsGrid').innerHTML = '<div class="empty-state">Unable to load station data from the API.</div>';
                document.getElementById('alertsPanel').innerHTML = `<div class="alert-box error"><div class="alert-title"><span>API Error</span><span class="tag">alert</span></div><div class="alert-content">${error.message}</div></div>`;
            }
        }

        function detectStateTransitions(previousStations, currentStations) {
            const previousByName = new Map((previousStations || []).map(s => [s.name, s]));
            const currentByName = new Map((currentStations || []).map(s => [s.name, s]));

            const events = [];
            for (const station of currentStations || []) {
                const prev = previousByName.get(station.name);
                if (!prev) continue;

                if (prev.status !== station.status) {
                    if (station.status === 'down') {
                        events.push({
                            type: 'station',
                            title: 'Station down',
                            message: `${station.name} is down.`,
                            severity: 'error'
                        });
                    } else {
                        events.push({
                            type: 'station',
                            title: 'Station back up',
                            message: `${station.name} is back online.`,
                            severity: 'warning'
                        });
                    }
                }

                const prevData = prev.data || {};
                const currentData = station.data || {};
                const keys = new Set([...Object.keys(prevData), ...Object.keys(currentData)]);

                for (const key of keys) {
                    const prevValue = prevData[key];
                    const curValue = currentData[key];
                    const prevMissing = prevValue === null || prevValue === undefined || String(prevValue).toLowerCase() === 'nan' || String(prevValue).toLowerCase() === 'none';
                    const curMissing = curValue === null || curValue === undefined || String(curValue).toLowerCase() === 'nan' || String(curValue).toLowerCase() === 'none';

                    if (prevMissing !== curMissing) {
                        if (curMissing) {
                            events.push({
                                type: 'instrument',
                                title: 'Instrument down',
                                message: `${station.name}: ${key} is missing or unavailable.`,
                                severity: 'error'
                            });
                        } else {
                            events.push({
                                type: 'instrument',
                                title: 'Instrument back up',
                                message: `${station.name}: ${key} is now available again.`,
                                severity: 'warning'
                            });
                        }
                    }
                }
            }

            for (const station of currentStations || []) {
                const prev = previousByName.get(station.name);
                if (!prev && station.status === 'down') {
                    events.push({
                        type: 'station',
                        title: 'Station down',
                        message: `${station.name} is down.`,
                        severity: 'error'
                    });
                }
            }

            return events;
        }

        let lastKnownStations = [];
        const recentAlertKeys = new Map();

        function normalizeNotificationKey(item) {
            if (!item || typeof item !== 'object') return null;
            return [
                item.type || 'notification',
                item.station || 'unknown-station',
                item.instrument || '',
                item.message || ''
            ].join('|');
        }

        function shouldDisplayNotification(item, ttlMs = 60000) {
            const key = normalizeNotificationKey(item);
            if (!key) return false;

            const now = Date.now();
            const previous = recentAlertKeys.get(key);
            if (previous && (now - previous) < ttlMs) {
                return false;
            }

            recentAlertKeys.set(key, now);
            return true;
        }

        function eventKeyForState(event) {
            if (!event || typeof event !== 'object') return null;
            return [event.title || '', event.message || '', event.type || ''].join('|');
        }

        function shouldDisplayStateEvent(event, ttlMs = 60000) {
            const key = eventKeyForState(event);
            if (!key) return false;

            const now = Date.now();
            const previous = recentAlertKeys.get(key);
            if (previous && (now - previous) < ttlMs) {
                return false;
            }

            recentAlertKeys.set(key, now);
            return true;
        }

        const toastContainer = document.getElementById('toastContainer');
        const notifyPermissionKey = 'gbon-notify-permission';

        function showToast(type, title, message) {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerHTML = `
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            `;
            toastContainer.appendChild(toast);

            setTimeout(() => {
                toast.remove();
            }, 5000);
        }

        function requestBrowserNotificationPermission() {
            if (!('Notification' in window)) return;
            const stored = localStorage.getItem(notifyPermissionKey);
            if (stored === 'granted') {
                Notification.requestPermission().then(() => {});
                return;
            }

            Notification.requestPermission().then((permission) => {
                localStorage.setItem(notifyPermissionKey, permission);
            }).catch(() => {});
        }

        function notifyDesktop(title, message) {
            if (!('Notification' in window)) return;
            if (Notification.permission !== 'granted') return;
            new Notification(title, { body: message, tag: title });
        }

        async function loadDashboard() {
            try {
                const [stations, notifications] = await Promise.all([
                    fetchJson(`${window.location.origin}/stations/status`),
                    fetchJson(`${window.location.origin}/notifications`)
                ]);

                const stationList = Array.isArray(stations) ? stations : [];
                const filteredStations = statusFilter.value === 'all'
                    ? stationList
                    : stationList.filter(station => station.status === statusFilter.value);

                const notificationList = Array.isArray(notifications.notifications) ? notifications.notifications : [];

                const total = filteredStations.length;
                const online = filteredStations.filter(s => s.status === 'up').length;
                const alertList = [];

                filteredStations.forEach(station => {
                    const missing = summariseMissingData(station.data || {});
                    if (missing.length) {
                        missing.forEach(item => {
                            alertList.push({
                                type: 'error',
                                title: `${station.name} - Missing data`,
                                message: `Instrument value missing for "${item.key}" in ${station.name}.`
                            });
                        });
                    }

                    const battery = Number(station.battery_voltage);
                    if (station.status === 'up' && Number.isFinite(battery) && battery <= 11.0) {
                        alertList.push({
                            type: 'warning',
                            title: `${station.name} - Low battery`,
                            message: `Battery voltage is ${battery.toFixed(2)} V and is below the 11.0 V threshold.`
                        });
                    }
                });

                notificationList.forEach(item => {
                    if (!item || typeof item !== 'object') return;
                    if (!shouldDisplayNotification(item, 60000)) return;
                    const isInstrument = item.type === 'instrument_down';
                    alertList.push({
                        type: isInstrument ? 'error' : 'warning',
                        title: item.station
                            ? `${item.station}${isInstrument && item.instrument ? ` - ${item.instrument}` : ''}`
                            : 'Station alert',
                        message: item.message || 'Monitoring alert received from the API.'
                    });
                });

                document.getElementById('totalStations').textContent = String(total);
                document.getElementById('onlineStations').textContent = String(online);
                document.getElementById('alertCount').textContent = String(alertList.length);
                document.getElementById('notificationCount').textContent = String(notificationList.length);

                document.getElementById('stationsGrid').innerHTML = filteredStations.length
                    ? filteredStations.map(renderStationCard).join('')
                    : '<div class="empty-state">No stations match the selected filter.</div>';

                const alertsContainer = document.getElementById('alertsPanel');
                alertsContainer.innerHTML = alertList.length
                    ? alertList.map(alert => renderAlertBox(alert.type, alert.title, alert.message)).join('')
                    : '<div class="empty-state">No active alerts. All monitored parameters are healthy.</div>';

                updateLastCheckedTime(filteredStations);

                const events = detectStateTransitions(lastKnownStations, stationList);
                const dedupedEvents = events.filter(event => shouldDisplayStateEvent(event, 60000));
                for (const event of dedupedEvents) {
                    showToast(event.severity, event.title, event.message);
                    notifyDesktop(event.title, event.message);
                }
                lastKnownStations = stationList;
            } catch (error) {
                document.getElementById('stationsGrid').innerHTML = '<div class="empty-state">Unable to load station data from the API.</div>';
                document.getElementById('alertsPanel').innerHTML = `<div class="alert-box error"><div class="alert-title"><span>API Error</span><span class="tag">alert</span></div><div class="alert-content">${error.message}</div></div>`;
            }
        }

        document.addEventListener('click', function (event) {
            const card = event.target.closest('.station-card');
            if (!card) return;
            card.classList.toggle('is-flipped');
        });

        requestBrowserNotificationPermission();
        applyStoredTheme();
        updateCurrentTime();
        loadDashboard();
        setInterval(updateCurrentTime, 1000);
        setInterval(loadDashboard, 15000);
    </script>
</body>
</html>
    """


@app.get("/", response_class=HTMLResponse)
async def dashboard_root():
    return HTMLResponse(content=render_dashboard_html())


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    return HTMLResponse(content=render_dashboard_html())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gbon-dashboard"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gbon:app", host="0.0.0.0", port=8000, reload=False)
