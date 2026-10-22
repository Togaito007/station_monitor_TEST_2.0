const themeToggle = document.getElementById('themeToggle');
const currentTimeElement = document.getElementById('currentTime');
const lastCheckedElement = document.getElementById('lastChecked');
const statusFilter = document.getElementById('statusFilter');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

let lastKnownStations = [];
const recentAlertKeys = new Map();

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
    const serverTimeValue = data.ServerTime ?? data.server_time ?? station.server_time ?? station.last_checked ?? null;
    const serverTimeText = (() => {
        if (!serverTimeValue) return 'N/A';
        const date = new Date(serverTimeValue);
        if (!Number.isNaN(date.getTime())) {
            return date.toLocaleString([], {
                year: 'numeric',
                month: 'short',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
        return formatValue(serverTimeValue);
    })();

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
                    <div class="station-footer">
                        <span>Server time</span>
                        <strong>${serverTimeText}</strong>
                    </div>
                    ${missing.length ? `<div class="missing-summary">Missing values: ${missing.map(m => m.key).join(', ')}</div>` : ''}
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

function detectStateTransitions(previousStations, currentStations) {
    const previousByName = new Map((previousStations || []).map(s => [s.name, s]));
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

    return events;
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
