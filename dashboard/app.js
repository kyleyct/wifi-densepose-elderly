/* app.js — Fall Detection Dashboard Logic */
(function () {
  'use strict';

  // ============================================
  // STATE
  // ============================================
  let mode = 'demo'; // 'demo' | 'live'
  let demoInterval = null;
  let alertInterval = null;
  let activityChart = null;
  let timelineChart = null;

  const ROOMS = ['客廳', '睡房', '浴室', '廚房'];
  const ROOM_IDS = { '客廳': 'living', '睡房': 'bedroom', '浴室': 'bathroom', '廚房': 'kitchen' };
  const ACTIVITIES = ['站立', '坐下', '行走', '躺臥'];
  const ACTIVITY_ICONS = { '站立': '🧍', '坐下': '🪑', '行走': '🚶', '躺臥': '🛌' };
  const PERSONS = ['長者A', '長者B'];

  let state = {
    systemOnline: true,
    persons: [],
    todayAlerts: 0,
    fallAlerts: 0,
    lyingAlerts: 0,
    avgResponseMs: 0,
    responseTimes: [],
    safetyRating: 'normal', // 'normal' | 'caution' | 'danger'
    activityFeed: [],
    alertHistory: [],
    activityCounts: { '站立': 0, '坐下': 0, '行走': 0, '躺臥': 0 },
    hourlyActivity: new Array(24).fill(0),
  };

  // ============================================
  // THEME TOGGLE
  // ============================================
  (function () {
    const toggle = document.querySelector('[data-theme-toggle]');
    const root = document.documentElement;
    let theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    root.setAttribute('data-theme', theme);

    if (toggle) {
      toggle.addEventListener('click', () => {
        theme = theme === 'dark' ? 'light' : 'dark';
        root.setAttribute('data-theme', theme);
        toggle.setAttribute('aria-label', theme === 'dark' ? '切換淺色模式' : '切換深色模式');
        toggle.innerHTML = theme === 'dark'
          ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>'
          : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        updateChartColors();
      });
    }
  })();

  // ============================================
  // MODE TOGGLE
  // ============================================
  const btnDemo = document.getElementById('btn-demo');
  const btnLive = document.getElementById('btn-live');
  const connStatus = document.getElementById('connection-status');

  btnDemo.addEventListener('click', () => {
    if (mode === 'demo') return;
    mode = 'demo';
    btnDemo.classList.add('active');
    btnDemo.setAttribute('aria-pressed', 'true');
    btnLive.classList.remove('active');
    btnLive.setAttribute('aria-pressed', 'false');
    connStatus.innerHTML = '<span class="status-dot-sm green"></span><span>模擬運行中</span>';
    startDemo();
  });

  btnLive.addEventListener('click', () => {
    if (mode === 'live') return;
    mode = 'live';
    btnLive.classList.add('active');
    btnLive.setAttribute('aria-pressed', 'true');
    btnDemo.classList.remove('active');
    btnDemo.setAttribute('aria-pressed', 'false');
    connStatus.innerHTML = '<span class="status-dot-sm yellow"></span><span>連接 localhost:8000...</span>';
    stopDemo();
    startLive();
  });

  // ============================================
  // UTILITY
  // ============================================
  function rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function now() {
    return new Date();
  }

  function timeStr(d) {
    return d.toLocaleTimeString('zh-Hant', { hour12: false });
  }

  function dateTimeStr(d) {
    return d.toLocaleString('zh-Hant', {
      month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
      hour12: false
    });
  }

  function animateValue(el, newText) {
    el.textContent = newText;
    el.classList.add('bump');
    setTimeout(() => el.classList.remove('bump'), 200);
  }

  // ============================================
  // DEMO DATA GENERATION
  // ============================================
  function generatePersons() {
    const count = rand(1, 2);
    const persons = [];
    const usedRooms = [];

    for (let i = 0; i < count; i++) {
      let room;
      do { room = pick(ROOMS); } while (usedRooms.includes(room));
      usedRooms.push(room);

      // Weight activities - mostly normal, occasionally lying
      const actWeights = [0.3, 0.3, 0.25, 0.15]; // stand, sit, walk, lie
      const r = Math.random();
      let cumulative = 0;
      let activity = ACTIVITIES[0];
      for (let j = 0; j < actWeights.length; j++) {
        cumulative += actWeights[j];
        if (r < cumulative) { activity = ACTIVITIES[j]; break; }
      }

      persons.push({
        name: PERSONS[i],
        room: room,
        activity: activity,
        confidence: (85 + Math.random() * 14.9).toFixed(1)
      });
    }
    return persons;
  }

  function updateDemoState() {
    state.persons = generatePersons();

    // Update activity counts
    state.persons.forEach(p => {
      state.activityCounts[p.activity] = (state.activityCounts[p.activity] || 0) + 1;
    });

    // Update hourly
    const h = now().getHours();
    state.hourlyActivity[h] += state.persons.length;

    // Response time simulation
    const rt = rand(80, 220);
    state.responseTimes.push(rt);
    if (state.responseTimes.length > 50) state.responseTimes.shift();
    state.avgResponseMs = Math.round(
      state.responseTimes.reduce((a, b) => a + b, 0) / state.responseTimes.length
    );

    // Activity feed + auto-alert for lying in risky rooms
    state.persons.forEach(p => {
      const isRiskyLying = p.activity === '躺臥' && (p.room === '浴室' || p.room === '廚房');
      if (isRiskyLying) {
        // Auto-trigger a lying alert for bathroom/kitchen lying
        state.lyingAlerts++;
        state.todayAlerts++;
        const t = now();
        const alert = {
          time: dateTimeStr(t),
          person: p.name,
          location: p.room,
          event: '長時間躺臥',
          confidence: p.confidence,
          status: '監控中',
          type: 'lying',
          sortTime: t.getTime()
        };
        state.alertHistory.unshift(alert);
        if (state.alertHistory.length > 20) state.alertHistory.pop();
        addFeedItem('warning', `⚡ ${p.name} 在${p.room}躺臥 — 信心度 ${p.confidence}%`, timeStr(t));
        showToast('躺臥提醒', `${p.name} 在${p.room}偵測到躺臥`, 'warning');
        flashKPI('kpi-alerts');
      } else {
        addFeedItem(
          'normal',
          `${p.name} 在${p.room} — ${ACTIVITY_ICONS[p.activity]} ${p.activity} (${p.confidence}%)`,
          timeStr(now())
        );
      }
    });

    // Safety rating
    if (state.fallAlerts >= 3) {
      state.safetyRating = 'danger';
    } else if (state.fallAlerts >= 1 || state.lyingAlerts >= 2) {
      state.safetyRating = 'caution';
    } else {
      state.safetyRating = 'normal';
    }

    renderAll();
  }

  function simulateAlert() {
    const isFall = Math.random() < 0.5;
    const person = pick(PERSONS);
    const room = pick(ROOMS);
    const confidence = (88 + Math.random() * 11.9).toFixed(1);
    const t = now();
    const rt = rand(90, 250);

    if (isFall) {
      state.fallAlerts++;
      state.todayAlerts++;

      const alert = {
        time: dateTimeStr(t),
        person: person,
        location: room,
        event: '跌倒',
        confidence: confidence,
        status: Math.random() < 0.3 ? '已處理' : '警報中',
        type: 'fall',
        sortTime: t.getTime()
      };
      state.alertHistory.unshift(alert);
      if (state.alertHistory.length > 20) state.alertHistory.pop();

      addFeedItem('alert', `⚠️ ${person} 在${room}跌倒！信心度 ${confidence}%`, timeStr(t));
      showToast('跌倒警報', `${person} 在${room}偵測到跌倒事件`, 'error');
      flashKPI('kpi-alerts');
    } else {
      state.lyingAlerts++;
      state.todayAlerts++;

      const alert = {
        time: dateTimeStr(t),
        person: person,
        location: room,
        event: '長時間躺臥',
        confidence: confidence,
        status: Math.random() < 0.4 ? '已處理' : '監控中',
        type: 'lying',
        sortTime: t.getTime()
      };
      state.alertHistory.unshift(alert);
      if (state.alertHistory.length > 20) state.alertHistory.pop();

      addFeedItem('warning', `⚡ ${person} 在${room}長時間躺臥 — 信心度 ${confidence}%`, timeStr(t));
      showToast('躺臥提醒', `${person} 在${room}偵測到長時間躺臥`, 'warning');
      flashKPI('kpi-alerts');
    }

    state.responseTimes.push(rt);
    if (state.responseTimes.length > 50) state.responseTimes.shift();
    state.avgResponseMs = Math.round(
      state.responseTimes.reduce((a, b) => a + b, 0) / state.responseTimes.length
    );

    // Update safety
    if (state.fallAlerts >= 3) {
      state.safetyRating = 'danger';
    } else if (state.fallAlerts >= 1 || state.lyingAlerts >= 2) {
      state.safetyRating = 'caution';
    } else {
      state.safetyRating = 'normal';
    }

    renderAll();
  }

  // ============================================
  // ACTIVITY FEED
  // ============================================
  function addFeedItem(type, msg, time) {
    state.activityFeed.unshift({ type, msg, time });
    if (state.activityFeed.length > 50) state.activityFeed.pop();
  }

  function renderFeed() {
    const container = document.getElementById('activity-feed');
    const countEl = document.getElementById('feed-count');

    if (state.activityFeed.length === 0) {
      container.innerHTML = '<div class="feed-empty">等待資料中...</div>';
      countEl.textContent = '0 筆';
      return;
    }

    countEl.textContent = `${state.activityFeed.length} 筆`;

    const items = state.activityFeed.slice(0, 30);
    container.innerHTML = items.map((item, i) => {
      const cls = item.type === 'alert' ? 'alert-item' : item.type === 'warning' ? 'warning-item' : '';
      const dotCls = item.type === 'alert' ? 'alert' : item.type === 'warning' ? 'warning' : 'normal';
      return `
        <div class="feed-item ${cls}" style="animation-delay:${i * 20}ms">
          <span class="feed-dot ${dotCls}"></span>
          <div class="feed-text">
            <div class="feed-msg">${item.msg}</div>
            <div class="feed-time">${item.time}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ============================================
  // TOAST
  // ============================================
  function showToast(title, body, type) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'warning' ? 'toast-warning' : ''}`;
    const iconSvg = type === 'error'
      ? '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
      : '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';

    toast.innerHTML = `
      ${iconSvg}
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-body">${body}</div>
      </div>
      <button class="toast-close" aria-label="關閉通知" onclick="this.closest('.toast').classList.add('removing'); setTimeout(() => this.closest('.toast').remove(), 200);">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
      </button>
    `;

    container.appendChild(toast);

    // Auto remove after 5s
    setTimeout(() => {
      if (toast.parentNode) {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 200);
      }
    }, 5000);
  }

  // ============================================
  // FLASH KPI
  // ============================================
  function flashKPI(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove('alert-flash');
    void el.offsetWidth; // trigger reflow
    el.classList.add('alert-flash');
  }

  // ============================================
  // RENDER
  // ============================================
  function renderKPIs() {
    // System status
    const statusVal = document.getElementById('kpi-status-value');
    if (state.systemOnline) {
      statusVal.innerHTML = '<span class="status-indicator green"></span><span>正常</span>';
    } else {
      statusVal.innerHTML = '<span class="status-indicator red"></span><span>離線</span>';
    }

    // Persons
    const personsVal = document.getElementById('kpi-persons-value');
    const personsSub = document.getElementById('kpi-persons-sub');
    personsVal.textContent = state.persons.length;
    const roomsUsed = [...new Set(state.persons.map(p => p.room))];
    personsSub.textContent = state.persons.length > 0
      ? `分佈在 ${roomsUsed.length} 個房間`
      : '無人偵測';

    // Alerts
    const alertsVal = document.getElementById('kpi-alerts-value');
    const alertsSub = document.getElementById('kpi-alerts-sub');
    alertsVal.textContent = state.todayAlerts;
    if (state.todayAlerts > 0) {
      alertsVal.style.color = 'var(--color-error)';
      alertsSub.textContent = `${state.fallAlerts} 跌倒 · ${state.lyingAlerts} 躺臥`;
    } else {
      alertsVal.style.color = '';
      alertsSub.textContent = '無警報';
    }

    // Response
    const responseVal = document.getElementById('kpi-response-value');
    const responseSub = document.getElementById('kpi-response-sub');
    if (state.avgResponseMs > 0) {
      responseVal.innerHTML = `${state.avgResponseMs}<span class="kpi-unit">ms</span>`;
      const delta = rand(-15, 5);
      responseSub.textContent = delta < 0 ? `較昨日 ↓${Math.abs(delta)}%` : `較昨日 ↑${delta}%`;
    }

    // Safety
    const safetyVal = document.getElementById('kpi-safety-value');
    const safetySub = document.getElementById('kpi-safety-sub');
    const ratings = {
      'normal': { dot: 'green', text: '正常', sub: '無風險' },
      'caution': { dot: 'yellow', text: '留意', sub: '需要關注' },
      'danger': { dot: 'red', text: '危險', sub: '立即處理' }
    };
    const r = ratings[state.safetyRating];
    safetyVal.innerHTML = `<span class="safety-dot ${r.dot}"></span><span>${r.text}</span>`;
    safetySub.textContent = r.sub;
  }

  function renderRooms() {
    const timeEl = document.getElementById('room-time');
    timeEl.textContent = timeStr(now());

    ROOMS.forEach(room => {
      const id = ROOM_IDS[room];
      const card = document.getElementById(`room-${id}`);
      const peopleEl = document.getElementById(`room-${id}-people`);
      const actEl = document.getElementById(`room-${id}-activity`);

      const personsInRoom = state.persons.filter(p => p.room === room);

      card.classList.remove('occupied', 'alert', 'warning');

      if (personsInRoom.length > 0) {
        const hasAlert = state.alertHistory.some(a =>
          a.location === room && a.status === '警報中' && a.event === '跌倒'
        );
        const hasWarning = state.alertHistory.some(a =>
          a.location === room && a.status === '監控中'
        );

        if (hasAlert) {
          card.classList.add('alert');
        } else if (hasWarning) {
          card.classList.add('warning');
        } else {
          card.classList.add('occupied');
        }

        peopleEl.textContent = `${personsInRoom.length} 人`;
        actEl.textContent = personsInRoom.map(p => `${ACTIVITY_ICONS[p.activity]} ${p.activity}`).join(' · ');
      } else {
        peopleEl.textContent = '無人';
        actEl.textContent = '—';
      }
    });
  }

  function renderAlertTable() {
    const tbody = document.getElementById('alert-tbody');
    const countEl = document.getElementById('alert-count');
    countEl.textContent = `${state.alertHistory.length} 筆`;

    if (state.alertHistory.length === 0) {
      tbody.innerHTML = '<tr class="table-empty"><td colspan="6">尚無警報記錄</td></tr>';
      return;
    }

    tbody.innerHTML = state.alertHistory.map(a => {
      const rowCls = a.type === 'fall' ? 'row-fall' : 'row-lying';
      const eventCls = a.type === 'fall' ? 'fall' : 'lying';
      const eventText = a.event;
      const conf = parseFloat(a.confidence);
      const confColor = conf >= 95 ? 'var(--color-error)' : conf >= 90 ? 'var(--color-warning)' : 'var(--color-primary)';

      let statusCls = 'active';
      let statusText = a.status;
      if (a.status === '已處理') statusCls = 'resolved';
      else if (a.status === '監控中') statusCls = 'monitoring';

      return `
        <tr class="${rowCls}">
          <td>${a.time}</td>
          <td>${a.person}</td>
          <td>${a.location}</td>
          <td><span class="event-badge ${eventCls}">${eventText}</span></td>
          <td>
            <div class="confidence-bar">
              <div class="confidence-fill">
                <div class="confidence-fill-inner" style="width:${conf}%;background:${confColor}"></div>
              </div>
              <span>${a.confidence}%</span>
            </div>
          </td>
          <td><span class="status-badge ${statusCls}">${statusText}</span></td>
        </tr>
      `;
    }).join('');
  }

  function renderAll() {
    renderKPIs();
    renderRooms();
    renderFeed();
    renderAlertTable();
    updateCharts();
    document.getElementById('footer-time').textContent = dateTimeStr(now());
  }

  // ============================================
  // CHARTS
  // ============================================
  function getChartColors() {
    const style = getComputedStyle(document.documentElement);
    return {
      text: style.getPropertyValue('--color-text').trim(),
      muted: style.getPropertyValue('--color-text-muted').trim(),
      faint: style.getPropertyValue('--color-text-faint').trim(),
      primary: style.getPropertyValue('--color-primary').trim(),
      success: style.getPropertyValue('--color-success').trim(),
      warning: style.getPropertyValue('--color-warning').trim(),
      error: style.getPropertyValue('--color-error').trim(),
      blue: style.getPropertyValue('--color-blue').trim(),
      surface: style.getPropertyValue('--color-surface').trim(),
      divider: style.getPropertyValue('--color-divider').trim(),
      grid: style.getPropertyValue('--color-border').trim(),
    };
  }

  function initCharts() {
    if (typeof Chart === 'undefined') {
      setTimeout(initCharts, 200);
      return;
    }

    const c = getChartColors();

    // Activity Donut
    const ctx1 = document.getElementById('activity-chart').getContext('2d');
    activityChart = new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: ['站立', '坐下', '行走', '躺臥'],
        datasets: [{
          data: [
            state.activityCounts['站立'] || 1,
            state.activityCounts['坐下'] || 1,
            state.activityCounts['行走'] || 1,
            state.activityCounts['躺臥'] || 0
          ],
          backgroundColor: [c.primary, c.blue, c.success, c.warning],
          borderWidth: 0,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '65%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              color: c.muted,
              font: { family: 'Inter', size: 12 },
              padding: 16,
              usePointStyle: true,
              pointStyleWidth: 10
            }
          }
        }
      }
    });

    // Timeline
    const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`);
    const ctx2 = document.getElementById('timeline-chart').getContext('2d');
    timelineChart = new Chart(ctx2, {
      type: 'line',
      data: {
        labels: hours,
        datasets: [{
          label: '偵測活動次數',
          data: state.hourlyActivity,
          borderColor: c.primary,
          backgroundColor: c.primary + '20',
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: c.primary
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        scales: {
          x: {
            ticks: {
              color: c.faint,
              font: { family: 'Inter', size: 11 },
              maxTicksLimit: 12
            },
            grid: { color: c.divider + '40' }
          },
          y: {
            beginAtZero: true,
            ticks: {
              color: c.faint,
              font: { family: 'Inter', size: 11 },
              stepSize: 5
            },
            grid: { color: c.divider + '40' }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

  function updateCharts() {
    if (!activityChart || !timelineChart) return;

    activityChart.data.datasets[0].data = [
      state.activityCounts['站立'] || 0,
      state.activityCounts['坐下'] || 0,
      state.activityCounts['行走'] || 0,
      state.activityCounts['躺臥'] || 0
    ];
    activityChart.update('none');

    timelineChart.data.datasets[0].data = state.hourlyActivity;
    timelineChart.update('none');
  }

  function updateChartColors() {
    if (!activityChart || !timelineChart) return;
    const c = getChartColors();

    activityChart.data.datasets[0].backgroundColor = [c.primary, c.blue, c.success, c.warning];
    activityChart.options.plugins.legend.labels.color = c.muted;
    activityChart.update('none');

    timelineChart.data.datasets[0].borderColor = c.primary;
    timelineChart.data.datasets[0].backgroundColor = c.primary + '20';
    timelineChart.data.datasets[0].pointHoverBackgroundColor = c.primary;
    timelineChart.options.scales.x.ticks.color = c.faint;
    timelineChart.options.scales.x.grid.color = c.divider + '40';
    timelineChart.options.scales.y.ticks.color = c.faint;
    timelineChart.options.scales.y.grid.color = c.divider + '40';
    timelineChart.update('none');
  }

  // ============================================
  // DEMO MODE
  // ============================================
  function startDemo() {
    stopDemo();

    // Initial data
    updateDemoState();

    // Periodic updates every 3 seconds
    demoInterval = setInterval(updateDemoState, 3000);

    // Alert simulation every 15-30 seconds
    scheduleNextAlert();
  }

  function scheduleNextAlert() {
    const delay = rand(15000, 30000);
    alertInterval = setTimeout(() => {
      if (mode === 'demo') {
        simulateAlert();
        scheduleNextAlert();
      }
    }, delay);
  }

  function stopDemo() {
    if (demoInterval) { clearInterval(demoInterval); demoInterval = null; }
    if (alertInterval) { clearTimeout(alertInterval); alertInterval = null; }
  }

  // ============================================
  // LIVE MODE (attempts localhost:8000)
  // ============================================
  let liveInterval = null;

  function startLive() {
    if (liveInterval) clearInterval(liveInterval);

    async function fetchData() {
      try {
        const res = await fetch('http://localhost:8000/api/status', {
          signal: AbortSignal.timeout(3000)
        });
        if (!res.ok) throw new Error('Bad response');
        const data = await res.json();
        connStatus.innerHTML = '<span class="status-dot-sm green"></span><span>已連接</span>';
        // Process live data...
        if (data.persons) state.persons = data.persons;
        if (data.alerts !== undefined) state.todayAlerts = data.alerts;
        renderAll();
      } catch (e) {
        connStatus.innerHTML = '<span class="status-dot-sm red"></span><span>無法連接</span>';
      }
    }

    fetchData();
    liveInterval = setInterval(fetchData, 3000);
  }

  function stopLive() {
    if (liveInterval) { clearInterval(liveInterval); liveInterval = null; }
  }

  // ============================================
  // TABLE SORTING
  // ============================================
  document.querySelectorAll('#alert-table th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const key = th.dataset.sort;
      const map = {
        time: 'time', person: 'person', location: 'location',
        event: 'event', confidence: 'confidence', status: 'status'
      };

      const dir = th.classList.contains('sort-asc') ? 'desc' : 'asc';
      document.querySelectorAll('#alert-table th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
      th.classList.add(`sort-${dir}`);

      state.alertHistory.sort((a, b) => {
        let va = a[map[key]];
        let vb = b[map[key]];
        if (key === 'confidence') { va = parseFloat(va); vb = parseFloat(vb); }
        if (key === 'time') { va = a.sortTime; vb = b.sortTime; }
        if (typeof va === 'number') return dir === 'asc' ? va - vb : vb - va;
        return dir === 'asc' ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
      });

      renderAlertTable();
    });
  });

  // ============================================
  // INIT
  // ============================================
  function init() {
    // Pre-seed some hourly data
    const currentHour = now().getHours();
    for (let i = 0; i < currentHour; i++) {
      state.hourlyActivity[i] = rand(2, 15);
    }

    // Pre-seed activity counts
    state.activityCounts = {
      '站立': rand(20, 80),
      '坐下': rand(30, 90),
      '行走': rand(15, 60),
      '躺臥': rand(5, 25)
    };

    initCharts();
    startDemo();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
