"""
ui/login.py
CỔNG ĐĂNG NHẬP & ĐĂNG KÝ LAMP LOGIN ANIMATION — AI Financial Platform

Tái hiện chuyển động kéo dây đèn (Lamp Login Animation):
- Kéo dây đèn xuống (hoặc click / phím cách) -> đèn bật sáng.
- Phòng đổi màu mượt từ ROOM_OFF (#121417) sang ROOM_ON (#1c1f24).
- Chùm sáng rọi xuống bàn làm việc và thẻ đăng nhập/đăng ký viền vàng kim (#d8b45f) hiện ra.
- Hỗ trợ đầy đủ:
    1. Đăng nhập (Sign In)
    2. Đăng ký tài khoản mới (Sign Up)
    3. Đăng nhập nhanh 1-click (Guest / Demo)
- Khi user đăng nhập hoặc đăng ký xong, hệ thống tự động lưu phiên và chuyển hướng ngay vào Dashboard chính.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

# Bảng màu tương ứng với script Tkinter gốc
ROOM_OFF = "#121417"
ROOM_ON = "#1c1f24"
SHADE_OFF = "#26272a"
SHADE_ON = "#f3e6cd"
METAL_OFF = "#4a4b4e"
METAL_ON = "#9a9ca1"
CARD_OFF = "#16191d"
CARD_ON = "#2a2b28"
GOLD = "#d8b45f"
GOLD_HOVER = "#e6c877"
INK = "#f4f1ec"
MUTED = "#8d9099"


def build_lamp_html(initial_on: bool = True, default_user: str = "Admin") -> str:
    """Tạo mã HTML/SVG/CSS/JS hoạt hình tương tác kéo dây đèn và form Đăng nhập/Đăng ký."""
    is_on_str = "true" if initial_on else "false"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lamp Login & Register — AI Financial Platform</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    user-select: none;
    -webkit-user-select: none;
  }}

  body {{
    font-family: 'Be Vietnam Pro', system-ui, -apple-system, sans-serif;
    background-color: {ROOM_OFF};
    color: {INK};
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow-x: hidden;
    transition: background-color 0.6s cubic-bezier(0.25, 1, 0.5, 1);
  }}

  body.lamp-on {{
    background-color: {ROOM_ON};
  }}

  .scene-container {{
    position: relative;
    width: 940px;
    height: 590px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 30px;
  }}

  /* --- CỘT ĐÈN (SVG LAMP) --- */
  .lamp-area {{
    position: relative;
    width: 440px;
    height: 540px;
    display: flex;
    justify-content: center;
    align-items: center;
  }}

  svg.lamp-svg {{
    width: 100%;
    height: 100%;
    overflow: visible;
  }}

  /* Chùm sáng (Light Beam) */
  .light-beam {{
    opacity: 0;
    transition: opacity 0.6s cubic-bezier(0.25, 1, 0.5, 1);
    pointer-events: none;
  }}
  body.lamp-on .light-beam {{
    opacity: 0.92;
  }}

  /* Chao đèn (Shade) */
  .lamp-shade {{
    fill: {SHADE_OFF};
    transition: fill 0.6s cubic-bezier(0.25, 1, 0.5, 1), filter 0.6s ease;
  }}
  body.lamp-on .lamp-shade {{
    fill: {SHADE_ON};
    filter: drop-shadow(0 0 24px rgba(243, 230, 205, 0.85));
  }}

  /* Thân và đế kim loại */
  .lamp-metal {{
    fill: {METAL_OFF};
    transition: fill 0.6s cubic-bezier(0.25, 1, 0.5, 1);
  }}
  body.lamp-on .lamp-metal {{
    fill: {METAL_ON};
  }}

  /* Dây kéo và núm giật */
  .cord-line {{
    stroke: #7c7e83;
    stroke-width: 2.2;
    stroke-linecap: round;
  }}

  .cord-knob {{
    fill: #c98f4e;
    cursor: grab;
    transition: fill 0.4s ease, filter 0.4s ease;
  }}
  .cord-knob:hover {{
    filter: drop-shadow(0 0 6px rgba(216, 180, 95, 0.9));
  }}
  body.lamp-on .cord-knob {{
    fill: #f7e2a8;
  }}
  .cord-knob.grabbing {{
    cursor: grabbing;
  }}

  .cord-hit-area {{
    cursor: grab;
    fill: transparent;
  }}
  .cord-hit-area.grabbing {{
    cursor: grabbing;
  }}

  /* Chú thích kéo dây */
  .pull-tooltip {{
    position: absolute;
    bottom: 20px;
    left: 48%;
    transform: translateX(-50%);
    background: rgba(18, 20, 23, 0.88);
    border: 1px solid rgba(216, 180, 95, 0.35);
    color: {GOLD};
    font-size: 11.5px;
    padding: 6px 14px;
    border-radius: 20px;
    pointer-events: none;
    letter-spacing: 0.02em;
    display: flex;
    align-items: center;
    gap: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    animation: pulseHint 2.4s infinite ease-in-out;
  }}
  @keyframes pulseHint {{
    0%, 100% {{ opacity: 0.75; transform: translateX(-50%) translateY(0); }}
    50% {{ opacity: 1; transform: translateX(-50%) translateY(-3px); }}
  }}

  /* --- THẺ ĐĂNG NHẬP / ĐĂNG KÝ (AUTH CARD) --- */
  .card-area {{
    width: 410px;
    position: relative;
    z-index: 10;
  }}

  .login-card {{
    background: {CARD_OFF};
    border: 1px solid #232629;
    border-radius: 14px;
    padding: 26px 26px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
    opacity: 0.12;
    transform: scale(0.98);
    pointer-events: none;
    transition: background 0.6s cubic-bezier(0.25, 1, 0.5, 1),
                border-color 0.6s cubic-bezier(0.25, 1, 0.5, 1),
                opacity 0.6s cubic-bezier(0.25, 1, 0.5, 1),
                transform 0.6s cubic-bezier(0.25, 1, 0.5, 1),
                box-shadow 0.6s ease;
  }}

  body.lamp-on .login-card {{
    background: {CARD_ON};
    border-color: rgba(216, 180, 95, 0.45);
    opacity: 1;
    transform: scale(1);
    pointer-events: auto;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.7), 0 0 35px rgba(216, 180, 95, 0.18);
  }}

  .card-header-bar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }}

  .brand-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(216, 180, 95, 0.12);
    border: 1px solid rgba(216, 180, 95, 0.35);
    color: {GOLD};
    font-size: 10px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 6px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }}

  /* Chuyển đổi Tab Đăng nhập / Đăng ký */
  .auth-nav {{
    display: flex;
    background: #191c20;
    border: 1px solid #282c32;
    border-radius: 8px;
    padding: 3px;
    margin-bottom: 16px;
  }}

  .nav-btn {{
    flex: 1;
    text-align: center;
    padding: 6px 0;
    font-size: 12px;
    font-weight: 600;
    color: {MUTED};
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.25s ease;
  }}

  .nav-btn.active {{
    background: {GOLD};
    color: #2a2110;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(216, 180, 95, 0.3);
  }}

  .form-group {{
    margin-bottom: 12px;
    text-align: left;
  }}

  .form-label {{
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: {MUTED};
    margin-bottom: 4px;
    letter-spacing: 0.02em;
  }}

  .form-input {{
    width: 100%;
    height: 38px;
    background: #1e2126;
    border: 1px solid #2b2f35;
    border-radius: 8px;
    padding: 0 12px;
    color: {INK};
    font-family: inherit;
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }}
  .form-input:focus {{
    border-color: {GOLD};
    box-shadow: 0 0 0 3px rgba(216, 180, 95, 0.2);
  }}

  .btn-submit {{
    width: 100%;
    height: 40px;
    background: {GOLD};
    color: #2a2110;
    border: none;
    border-radius: 8px;
    font-family: inherit;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    margin-top: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    transition: background-color 0.2s, transform 0.1s, box-shadow 0.2s;
  }}
  .btn-submit:hover {{
    background: {GOLD_HOVER};
    box-shadow: 0 4px 16px rgba(216, 180, 95, 0.4);
  }}
  .btn-submit:active {{
    transform: scale(0.98);
  }}

  .btn-demo {{
    width: 100%;
    height: 34px;
    background: transparent;
    color: {MUTED};
    border: 1px solid #33373e;
    border-radius: 8px;
    font-family: inherit;
    font-size: 11.5px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 8px;
    transition: all 0.2s;
  }}
  .btn-demo:hover {{
    border-color: {GOLD};
    color: {INK};
    background: rgba(216, 180, 95, 0.08);
  }}

  .status-msg {{
    margin-top: 10px;
    font-size: 11.5px;
    text-align: center;
    color: {GOLD};
    min-height: 18px;
    font-weight: 500;
  }}

  .dark-hint {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    color: rgba(141, 144, 153, 0.65);
    font-size: 13px;
    pointer-events: none;
    transition: opacity 0.4s ease;
    width: 280px;
    line-height: 1.6;
  }}
  body.lamp-on .dark-hint {{
    opacity: 0;
  }}

  .form-section {{
    display: none;
  }}
  .form-section.active {{
    display: block;
    animation: fadeIn 0.3s ease;
  }}
  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(4px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}
</style>
</head>
<body class="{'lamp-on' if initial_on else ''}">

<div class="scene-container">
  <!-- Cột Đèn Chiếu Sáng -->
  <div class="lamp-area">
    <svg class="lamp-svg" viewBox="0 0 440 500">
      <defs>
        <!-- Chùm sáng hình nón đổ xuống -->
        <linearGradient id="beamGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="{SHADE_ON}" stop-opacity="0.45" />
          <stop offset="40%" stop-color="{SHADE_ON}" stop-opacity="0.2" />
          <stop offset="100%" stop-color="{SHADE_ON}" stop-opacity="0.0" />
        </linearGradient>

        <!-- Đổ bóng chao đèn -->
        <radialGradient id="shadeGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#fff6e0" stop-opacity="0.9" />
          <stop offset="100%" stop-color="{SHADE_ON}" stop-opacity="0.6" />
        </radialGradient>
      </defs>

      <!-- Chùm sáng (polygon toạ độ tương tự Tkinter beam) -->
      <polygon class="light-beam" points="165,190 275,190 410,480 30,480" fill="url(#beamGradient)" />

      <!-- Đế đèn kim loại -->
      <rect class="lamp-metal" x="175" y="380" width="90" height="12" rx="4" />

      <!-- Thân đèn kim loại -->
      <rect class="lamp-metal" x="215" y="195" width="10" height="185" rx="3" />

      <!-- Chao đèn (Hình chóp / bầu dục mượt mà) -->
      <path class="lamp-shade" d="M 140,195 Q 220,135 300,195 L 310,205 Q 220,225 130,205 Z" />
      <ellipse class="lamp-shade" cx="220" cy="200" rx="90" ry="14" />

      <!-- Dây kéo đèn (Interactive Cord) -->
      <g id="cordGroup">
        <line id="cordLine" class="cord-line" x1="285" y1="195" x2="285" y2="258" />
        <circle id="cordKnob" class="cord-knob" cx="285" cy="265" r="7.5" />
        <!-- Vùng bấm rộng hơn cho chuột / cảm ứng -->
        <rect id="cordHitArea" class="cord-hit-area" x="265" y="190" width="40" height="90" />
      </g>
    </svg>

    <div class="pull-tooltip" id="pullTooltip">
      <span>💡</span> Kéo dây hoặc bấm phím Cách để bật/tắt đèn
    </div>
  </div>

  <!-- Thẻ Đăng Nhập & Đăng Ký -->
  <div class="card-area">
    <div class="dark-hint">
      <div style="font-size: 28px; margin-bottom: 8px;">🛋️</div>
      Phòng đang tối.<br>Hãy kéo dây đèn để bật sáng hệ thống.
    </div>

    <div class="login-card" id="loginCard">
      <div class="card-header-bar">
        <div class="brand-badge">⚡ AI Quant Gateway</div>
        <span style="font-size: 11px; color: {MUTED};">Thị trường VN</span>
      </div>

      <!-- Điều hướng tab Đăng nhập / Đăng ký -->
      <div class="auth-nav">
        <button type="button" class="nav-btn active" id="tabLoginBtn" onclick="showTab('login')">🔑 Đăng nhập</button>
        <button type="button" class="nav-btn" id="tabRegisterBtn" onclick="showTab('register')">📝 Đăng ký</button>
      </div>

      <!-- Form ĐĂNG NHẬP -->
      <div class="form-section active" id="sectionLogin">
        <form id="formLogin" onsubmit="event.preventDefault(); handleLogin();">
          <div class="form-group">
            <label class="form-label" for="login_user">Tên tài khoản (Username)</label>
            <input class="form-input" id="login_user" type="text" value="{default_user}" placeholder="admin" required autocomplete="username" />
          </div>

          <div class="form-group">
            <label class="form-label" for="login_pass">Mật khẩu (Password)</label>
            <input class="form-input" id="login_pass" type="password" value="admin" placeholder="••••••••" required autocomplete="current-password" />
          </div>

          <button type="submit" class="btn-submit">
            <span>Đăng nhập & Vào Dashboard</span>
            <span>→</span>
          </button>
        </form>
      </div>

      <!-- Form ĐĂNG KÝ -->
      <div class="form-section" id="sectionRegister">
        <form id="formRegister" onsubmit="event.preventDefault(); handleRegister();">
          <div class="form-group">
            <label class="form-label" for="reg_user">Tên tài khoản mới</label>
            <input class="form-input" id="reg_user" type="text" placeholder="Nhập tên tài khoản..." required autocomplete="username" />
          </div>

          <div class="form-group">
            <label class="form-label" for="reg_pass">Mật khẩu bảo vệ</label>
            <input class="form-input" id="reg_pass" type="password" placeholder="Tối thiểu 4 ký tự..." required autocomplete="new-password" />
          </div>

          <div class="form-group">
            <label class="form-label" for="reg_pass2">Xác nhận mật khẩu</label>
            <input class="form-input" id="reg_pass2" type="password" placeholder="Nhập lại mật khẩu..." required autocomplete="new-password" />
          </div>

          <button type="submit" class="btn-submit">
            <span>Tạo tài khoản & Vào Dashboard</span>
            <span>✨</span>
          </button>
        </form>
      </div>

      <button type="button" class="btn-demo" onclick="handleDemoLogin()">
        ⚡ Vào nhanh (Khách / Demo)
      </button>

      <div class="status-msg" id="statusMsg"></div>
    </div>
  </div>
</div>

<script>
  let isOn = {is_on_str};
  let isDragging = false;
  let startY = 0;
  let currentPull = 0;
  const MAX_PULL = 85;
  const PULL_THRESHOLD = 34;
  const REST_Y = 258;

  const cordLine = document.getElementById('cordLine');
  const cordKnob = document.getElementById('cordKnob');
  const cordHitArea = document.getElementById('cordHitArea');
  const statusMsg = document.getElementById('statusMsg');
  const pullTooltip = document.getElementById('pullTooltip');

  // Chuyển tab Đăng nhập / Đăng ký
  function showTab(tab) {{
    const btnL = document.getElementById('tabLoginBtn');
    const btnR = document.getElementById('tabRegisterBtn');
    const secL = document.getElementById('sectionLogin');
    const secR = document.getElementById('sectionRegister');
    statusMsg.innerText = '';

    if (tab === 'login') {{
      btnL.classList.add('active');
      btnR.classList.remove('active');
      secL.classList.add('active');
      secR.classList.remove('active');
    }} else {{
      btnR.classList.add('active');
      btnL.classList.remove('active');
      secR.classList.add('active');
      secL.classList.remove('active');
    }}
  }}

  // Âm thanh cơ học khi giật dây (Web Audio API)
  function playClickSound() {{
    try {{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(isOn ? 520 : 380, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(120, ctx.currentTime + 0.08);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.08);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.09);
    }} catch(e) {{}}
  }}

  function updateCord(p) {{
    currentPull = Math.max(0, Math.min(MAX_PULL, p));
    const y = REST_Y + currentPull;
    cordLine.setAttribute('y2', y);
    cordKnob.setAttribute('cy', y + 7);
    cordHitArea.setAttribute('y', 190);
    cordHitArea.setAttribute('height', 85 + currentPull);
  }}

  function snapBack(callback) {{
    const start = currentPull;
    const startTime = performance.now();
    const duration = 240;

    function animate(now) {{
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      const eased = (1 - Math.pow(1 - progress, 3)) - 0.12 * (1 - progress) * (progress > 0.5 ? 1 : 0);
      const val = start * (1 - Math.max(0, Math.min(1, eased)));
      updateCord(val);

      if (progress < 1) {{
        requestAnimationFrame(animate);
      }} else {{
        updateCord(0);
        if (callback) callback();
      }}
    }}
    requestAnimationFrame(animate);
  }}

  function toggleLamp() {{
    isOn = !isOn;
    playClickSound();
    if (isOn) {{
      document.body.classList.add('lamp-on');
      pullTooltip.innerHTML = '<span>💡</span> Đèn đã bật! Nhập thông tin hoặc kéo dây để tắt';
    }} else {{
      document.body.classList.remove('lamp-on');
      pullTooltip.innerHTML = '<span>💡</span> Kéo dây hoặc bấm phím Cách để bật đèn';
    }}
  }}

  // Kéo thả chuột và cảm ứng
  function onPointerDown(e) {{
    isDragging = true;
    startY = e.clientY;
    cordKnob.classList.add('grabbing');
    cordHitArea.classList.add('grabbing');
    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
  }}

  function onPointerMove(e) {{
    if (!isDragging) return;
    const dy = e.clientY - startY;
    updateCord(dy);
  }}

  function onPointerUp(e) {{
    if (!isDragging) return;
    isDragging = false;
    cordKnob.classList.remove('grabbing');
    cordHitArea.classList.remove('grabbing');
    window.removeEventListener('pointermove', onPointerMove);
    window.removeEventListener('pointerup', onPointerUp);

    const shouldToggle = currentPull >= PULL_THRESHOLD;
    snapBack(() => {{
      if (shouldToggle) toggleLamp();
    }});
  }}

  cordHitArea.addEventListener('pointerdown', onPointerDown);
  cordKnob.addEventListener('pointerdown', onPointerDown);

  cordHitArea.addEventListener('click', (e) => {{
    if (currentPull < 5) {{
      updateCord(45);
      setTimeout(() => {{
        snapBack(() => toggleLamp());
      }}, 80);
    }}
  }});

  window.addEventListener('keydown', (e) => {{
    if (e.code === 'Space' && e.target.tagName !== 'INPUT') {{
      e.preventDefault();
      updateCord(50);
      setTimeout(() => {{
        snapBack(() => toggleLamp());
      }}, 100);
    }}
  }});

  // --- XỬ LÝ CHUYỂN HƯỚNG VÀO DASHBOARD CHÍNH ---
  function redirectToDashboard(user, action) {{
    statusMsg.innerText = '🎉 ' + (action === 'register' ? 'Đăng ký thành công' : 'Đăng nhập thành công') + '! Đang chuyển hướng...';
    
    // 1. Chuyển hướng qua URL query parameters của trang cha (Streamlit iframe)
    try {{
      const target = window.parent || window.top;
      if (target && target !== window && target.location) {{
        const url = new URL(target.location.href);
        url.searchParams.set('auth', 'true');
        url.searchParams.set('user', user);
        url.searchParams.set('action', action);
        target.location.href = url.toString();
        return;
      }}
    }} catch(e) {{
      console.warn('Parent window redirect restricted:', e);
    }}

    // 2. Chuyển hướng nếu mở trang /login độc lập sang cổng Streamlit
    try {{
      const host = window.location.hostname || 'localhost';
      window.location.href = 'http://' + host + ':8501/?auth=true&user=' + encodeURIComponent(user) + '&action=' + action;
      return;
    }} catch(e) {{}}

    // 3. Dự phòng qua postMessage
    try {{
      window.parent.postMessage({{ type: 'STREAMLIT_AUTH', user: user, action: action }}, '*');
    }} catch(e) {{}}
  }}

  function handleLogin() {{
    const user = document.getElementById('login_user').value.trim() || 'Admin';
    redirectToDashboard(user, 'login');
  }}

  function handleRegister() {{
    const user = document.getElementById('reg_user').value.trim();
    const p1 = document.getElementById('reg_pass').value;
    const p2 = document.getElementById('reg_pass2').value;

    if (!user) {{
      statusMsg.innerText = 'Vui lòng nhập tên tài khoản.';
      return;
    }}
    if (p1 && p2 && p1 !== p2) {{
      statusMsg.innerText = 'Mật khẩu xác nhận không khớp!';
      return;
    }}
    redirectToDashboard(user, 'register');
  }}

  function handleDemoLogin() {{
    redirectToDashboard('Guest_Trader', 'demo');
  }}
</script>
</body>
</html>
"""


def render_login_screen() -> None:
    """Hiển thị màn hình Lamp Login và Đăng ký trước khi vào Dashboard chính."""
    # 1. Kiểm tra query parameters từ redirect
    query_auth = st.query_params.get("auth")
    if query_auth == "true":
        user = st.query_params.get("user", "Admin")
        action = st.query_params.get("action", "login")
        st.session_state["authenticated"] = True
        st.session_state["username"] = user
        st.session_state["action"] = action
        st.query_params.clear()
        st.rerun()

    # 2. Render Interactive Lamp Animation Canvas
    components.html(build_lamp_html(initial_on=True, default_user="Admin"), height=610)

    # 3. Native Streamlit Action Box (Hỗ trợ 100% người dùng trên mọi trình duyệt)
    st.markdown(
        f'<div style="text-align:center;margin-top:5px;margin-bottom:15px;'
        f'padding:10px 14px;background:{CARD_ON};border:1px solid rgba(216,180,95,0.3);'
        f'border-radius:10px;max-width:620px;margin-left:auto;margin-right:auto;">'
        f'<div style="font-size:13px;color:{GOLD};font-weight:700;margin-bottom:4px;">'
        f'⚡ CỔNG ĐĂNG NHẬP & ĐĂNG KÝ HỆ THỐNG ĐỊNH LƯỢNG</div>'
        f'<div style="font-size:11.5px;color:{MUTED};">'
        f'Thao tác trên khung hoạt hình kéo dây ở trên hoặc xác nhận nhanh ngay dưới đây:</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _, col_form, _ = st.columns([1, 2.2, 1])
    with col_form:
        tab_login, tab_reg, tab_quick = st.tabs(["🔑 Đăng nhập", "📝 Đăng ký tài khoản", "⚡ Vào nhanh"])

        with tab_login:
            with st.form("form_native_login"):
                u_in = st.text_input("Tên đăng nhập", value="Admin", key="login_u")
                p_in = st.text_input("Mật khẩu", value="admin", type="password", key="login_p")
                btn_log = st.form_submit_button("✨ Đăng nhập & Vào Dashboard", use_container_width=True, type="primary")
                if btn_log:
                    user_final = u_in.strip() or "Admin"
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_final
                    st.success(f"🎉 Đăng nhập thành công! Chào mừng **{user_final}** đến với Dashboard.")
                    st.rerun()

        with tab_reg:
            with st.form("form_native_reg"):
                u_new = st.text_input("Tên tài khoản mới", placeholder="Nhập tên tài khoản của bạn...", key="reg_u")
                p_new1 = st.text_input("Mật khẩu mới", type="password", placeholder="Tối thiểu 4 ký tự...", key="reg_p1")
                p_new2 = st.text_input("Xác nhận mật khẩu", type="password", placeholder="Nhập lại mật khẩu...", key="reg_p2")
                btn_reg = st.form_submit_button("📝 Tạo tài khoản & Vào Dashboard", use_container_width=True, type="primary")
                if btn_reg:
                    if not u_new.strip():
                        st.error("Vui lòng nhập tên tài khoản.")
                    elif p_new1 and p_new2 and p_new1 != p_new2:
                        st.error("Mật khẩu xác nhận không khớp!")
                    else:
                        reg_user = u_new.strip()
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = reg_user
                        st.session_state["is_new_user"] = True
                        st.success(f"🎉 Đăng ký thành công! Đang đưa **{reg_user}** vào Dashboard chính...")
                        st.rerun()

        with tab_quick:
            st.markdown(
                f'<div style="font-size:12px;color:{MUTED};margin-bottom:10px;">'
                f'Khám phá toàn bộ tính năng phân tích định lượng ngay lập tức mà không cần mật khẩu.</div>',
                unsafe_allow_html=True,
            )
            if st.button("⚡ Vào ngay với quyền Khách (Guest)", use_container_width=True):
                st.session_state["authenticated"] = True
                st.session_state["username"] = "Guest_Trader"
                st.rerun()
