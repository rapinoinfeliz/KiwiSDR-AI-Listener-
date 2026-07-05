const btnStart = document.getElementById('btn-start');
const btnStartMock = document.getElementById('btn-start-mock');
const btnStop = document.getElementById('btn-stop');
const statusBadge = document.getElementById('app-status');

const valNode = document.getElementById('val-node');
const valFreq = document.getElementById('val-freq');
const valScore = document.getElementById('val-score');
const valConf = document.getElementById('val-conf');

const logsContainer = document.getElementById('logs-container');

// State
let ws = null;
let reconnectInterval = null;

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

    ws.onopen = () => {
        console.log("WebSocket connected");
        clearInterval(reconnectInterval);
        fetchStatus();
    };

    ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        handleEvent(payload.event, payload.data);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected. Retrying...");
        statusBadge.textContent = "WS DISCONNECTED";
        statusBadge.className = "status-badge error";
        reconnectInterval = setTimeout(connectWebSocket, 3000);
    };
}

function handleEvent(eventType, data) {
    if (eventType === 'status') {
        if (data.state === 'running' || data.state === 'starting') {
            statusBadge.textContent = data.state === 'starting' ? "STARTING..." : "LIVE";
            statusBadge.className = "status-badge running";
            btnStart.disabled = true;
            btnStartMock.disabled = true;
            btnStop.disabled = false;
        } else {
            statusBadge.textContent = "STOPPED";
            statusBadge.className = "status-badge";
            btnStart.disabled = false;
            btnStartMock.disabled = false;
            btnStop.disabled = true;
        }
        appendLog(`Engine status: ${data.state}`, 'status');
        if (data.message) appendLog(data.message, 'error');
    }
    else if (eventType === 'node') {
        valNode.textContent = data.name;
        appendLog(`Connected to node: ${data.name} (${data.host})`, 'status');
    }
    else if (eventType === 'ui_event') {
        if (data.type === 'tuning') {
            valFreq.textContent = data.frequency.toFixed(1) + " kHz";
            appendLog(`Tuning to ${data.frequency.toFixed(1)} kHz`, 'tuning');
        }
        else if (data.type === 'transcription') {
            valScore.textContent = data.score.toFixed(2);
            valConf.textContent = data.confidence.toFixed(2);
            valFreq.textContent = data.frequency.toFixed(1) + " kHz";
            valNode.textContent = data.node_name || valNode.textContent;
            
            appendTranscription(data);
        }
    }
}

function appendLog(message, type) {
    const div = document.createElement('div');
    div.className = `log-entry event-${type}`;
    
    const time = new Date().toLocaleTimeString();
    div.innerHTML = `<div class="log-meta">[${time}] ${type.toUpperCase()}</div>
                     <div class="log-text">${message}</div>`;
    
    logsContainer.appendChild(div);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function appendTranscription(data) {
    const div = document.createElement('div');
    div.className = `log-entry event-transcription`;
    
    const time = new Date().toLocaleTimeString();
    let html = `<div class="log-meta">[${time}] ASR | Freq: ${data.frequency.toFixed(1)} kHz | Score: ${data.score.toFixed(2)}</div>
                <div class="log-text">${data.text}</div>`;
                
    if (data.translation) {
        html += `<div class="log-translation">PT: ${data.translation}</div>`;
    }
    
    div.innerHTML = html;
    logsContainer.appendChild(div);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        if (data.running) {
            statusBadge.textContent = "LIVE";
            statusBadge.className = "status-badge running";
            btnStart.disabled = true;
            btnStartMock.disabled = true;
            btnStop.disabled = false;
        } else {
            statusBadge.textContent = "STOPPED";
            statusBadge.className = "status-badge";
            btnStart.disabled = false;
            btnStartMock.disabled = false;
            btnStop.disabled = true;
        }
        
        if (data.node) valNode.textContent = data.node;
        if (data.frequency) valFreq.textContent = data.frequency.toFixed(1) + " kHz";
    } catch (e) {
        console.error("Error fetching status", e);
    }
}

async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        
        // Render history backwards so oldest is top
        data.reverse().forEach(intercept => {
            appendTranscription(intercept);
        });
        appendLog("Carregado histórico anterior do banco de dados.", "status");
    } catch (e) {
        console.error("Error fetching history", e);
    }
}

btnStart.addEventListener('click', () => fetch('/api/start?mock=false', { method: 'POST' }));
btnStartMock.addEventListener('click', () => fetch('/api/start?mock=true', { method: 'POST' }));
btnStop.addEventListener('click', () => fetch('/api/stop', { method: 'POST' }));

// Init
connectWebSocket();
loadHistory();
