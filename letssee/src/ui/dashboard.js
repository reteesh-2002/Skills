// PulseMesh Telemetry HUD Controller
// Tactile interactions, Web Audio synthesized clicks, live stream feed, and LED meter rendering

(function() {
  'use strict';

  // State
  let audioCtx = null;
  let bufferStats = { enqueued: 1420, flushed: 1380, dropped: 0, capacity: 500, current: 40 };

  // Audio synthesizer for mechanical tactile click
  function playMechanicalClick(frequency = 800, duration = 0.015) {
    try {
      if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) audioCtx = new AudioContextClass();
      }
      if (audioCtx && audioCtx.state === 'running') {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(frequency, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
      }
    } catch {
      // Audio not permitted or headless environment
    }
  }

  // Update Clock
  function updateClock() {
    const clockEl = document.getElementById('clock-display');
    if (clockEl) {
      clockEl.textContent = new Date().toISOString();
    }
  }
  setInterval(updateClock, 1000);
  updateClock();

  // Render LED bar
  function renderLedMeter(percentage) {
    const ticks = document.querySelectorAll('.led-tick');
    const totalTicks = ticks.length;
    const activeCount = Math.round((percentage / 100) * totalTicks);

    ticks.forEach((tick, idx) => {
      tick.className = 'led-tick';
      if (idx < activeCount) {
        if (idx < totalTicks * 0.6) {
          tick.classList.add('active-green');
        } else if (idx < totalTicks * 0.85) {
          tick.classList.add('active-amber');
        } else {
          tick.classList.add('active-red');
        }
      }
    });

    const pctEl = document.getElementById('buffer-pct-label');
    if (pctEl) pctEl.textContent = `${percentage.toFixed(1)}%`;
  }

  // Append stream line
  function appendLog(badgeType, badgeText, content) {
    const stream = document.getElementById('telemetry-log-stream');
    if (!stream) return;

    const line = document.createElement('div');
    line.className = 'stream-line';

    const time = document.createElement('span');
    time.className = 'line-time';
    time.textContent = new Date().toISOString();

    const badge = document.createElement('span');
    badge.className = `line-badge ${badgeType}`;
    badge.textContent = badgeText;

    const body = document.createElement('span');
    body.className = 'line-content';
    body.textContent = content;

    line.appendChild(time);
    line.appendChild(badge);
    line.appendChild(body);

    stream.appendChild(line);
    stream.scrollTop = stream.scrollHeight;

    // Prune stream to keep memory flat
    while (stream.children.length > 50) {
      stream.removeChild(stream.firstChild);
    }
  }

  // Update readouts
  function updateReadouts() {
    const enq = document.getElementById('stat-enqueued');
    const flu = document.getElementById('stat-flushed');
    const dro = document.getElementById('stat-dropped');
    if (enq) enq.textContent = bufferStats.enqueued;
    if (flu) flu.textContent = bufferStats.flushed;
    if (dro) dro.textContent = bufferStats.dropped;

    const pct = (bufferStats.current / bufferStats.capacity) * 100;
    renderLedMeter(pct);
  }

  // Bind controls
  const flushBtn = document.getElementById('btn-manual-flush');
  if (flushBtn) {
    flushBtn.addEventListener('click', () => {
      playMechanicalClick(1200, 0.02);
      bufferStats.flushed += bufferStats.current;
      bufferStats.current = 0;
      updateReadouts();
      appendLog('badge-sys', '[FLUSH]', 'Manual batch flush executed to WAL database.');
    });
  }

  const toggle = document.getElementById('toggle-zero-trust');
  if (toggle) {
    toggle.addEventListener('change', (e) => {
      playMechanicalClick(600, 0.03);
      if (e.target.checked) {
        appendLog('badge-allow', '[SEC-POLICY]', 'Zero-Trust strict boundary enforcement ENABLED.');
      } else {
        appendLog('badge-block', '[SEC-WARN]', 'Zero-Trust strict enforcement BYPASSED by operator override.');
      }
    });
  }

  // Periodic synthetic stream tick for live HUD feel
  setInterval(() => {
    bufferStats.enqueued += Math.floor(Math.random() * 5) + 1;
    bufferStats.current = Math.min(bufferStats.capacity, bufferStats.current + Math.floor(Math.random() * 3));
    if (bufferStats.current >= 450) {
      bufferStats.flushed += 400;
      bufferStats.current -= 400;
      appendLog('badge-sys', '[WAL-BATCH]', `Committed 400 audit events to WAL in 2.1ms`);
    }
    updateReadouts();
  }, 1500);

  updateReadouts();
})();
