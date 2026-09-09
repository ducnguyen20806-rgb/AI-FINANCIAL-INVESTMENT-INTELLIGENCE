"""
ui/login.py
CỔNG ĐĂNG NHẬP LAMP LOGIN ANIMATION — AI Financial Platform

Tái hiện chuyển động kéo dây đèn (Lamp Login Animation):
- Kéo dây đèn xuống (hoặc click / phím cách) -> đèn bật sáng.
- Phòng đổi màu mượt từ ROOM_OFF (#121417) sang ROOM_ON (#1c1f24).
- Chùm sáng rọi xuống bàn làm việc và thẻ đăng nhập viền vàng kim (#d8b45f) hiện ra.
- Hỗ trợ nhập tài khoản hoặc Đăng nhập nhanh 1-click (Demo / Khách).
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


def build_lamp_html(initial_on: bool = False, default_user: str = "admin") -> str:
    """Tạo mã HTML/SVG/CSS/JS hoạt hình tương tác kéo dây đèn hoàn chỉnh."""
    is_on_str = "true" if initial_on else "false"
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lamp Login</title>
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
    overflow: hidden;
    transition: background-color 0.6s cubic-bezier(0.25, 1, 0.5, 1);
  }}

  body.lamp-on {{
    background-color: {ROOM_ON};
  }}

  .scene-container {{
    position: relative;
    width: 920px;
    height: 560px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 40px;
  }}

  /* --- CỘT ĐÈN (SVG LAMP) --- */
  .lamp-area {{
    position: relative;
    width: 440px;
    height: 500px;
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
    bottom: 28px;
    left: 48%;
    transform: translateX(-50%);
    background: rgba(18, 20, 23, 0.85);
    border: 1px solid rgba(216, 180, 95, 0.3);
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
    0%, 100% {{ opacity: 0.7; transform: translateX(-50%) translateY(0); }}
    50% {{ opacity: 1; transform: translateX(-50%) translateY(-3px); }}
  }}

  /* --- THẺ ĐĂNG NHẬP (LOGIN CARD) --- */
  .card-area {{
    width: 380px;
    position: relative;
    z-index: 10;
  }}

  .login-card {{
    background: {CARD_OFF};
    border: 1px solid #232629;
    border-radius: 14px;
    padding: 34px 30px;
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

  .brand-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(216, 180, 95, 0.12);
    border: 1px solid rgba(216, 180, 95, 0.35);
    color: {GOLD};
    font-size: 10.5px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 6px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 14px;
  }}

  .card-title {{
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: {INK};
    margin-bottom: 4px;
  }}

  .card-subtitle {{
    font-size: 12px;
    color: {MUTED};
    margin-bottom: 22px;
    line-height: 1.4;
  }}

  .form-group {{
    margin-bottom: 16px;
    text-align: left;
  }}

  .form-label {{
    display: block;
    font-size: 11.5px;
    font-weight: 600;
    color: {MUTED};
    margin-bottom: 6px;
    letter-spacing: 0.02em;
  }}

  .form-input {{
    width: 100%;
    height: 40px;
    background: #1e2126;
    border: 1px solid #2b2f35;
    border-radius: 8px;
    padding: 0 14px;
    color: {INK};
    font-family: inherit;
    font-size: 13.5px;
    outline: none;
    transition: border-color 0.2s, box-shadow 0.2s;
  }}
  .form-input:focus {{
    border-color: {GOLD};
    box-shadow: 0 0 0 3px rgba(216, 180, 95, 0.2);
  }}

  .btn-submit {{
    width: 100%;
    height: 44px;
    background: {GOLD};
    color: #2a2110;
    border: none;
    border-radius: 8px;
    font-family: inherit;
    font-size: 13.5px;
    font-weight: 700;
    cursor: pointer;
    margin-top: 8px;
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
    height: 38px;
    background: transparent;
    color: {MUTED};
    border: 1px solid #33373e;
    border-radius: 8px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 10px;
    transition: all 0.2s;
  }}
  .btn-demo:hover {{
    border-color: {GOLD};
    color: {INK};
    background: rgba(216, 180, 95, 0.08);
  }}

  .status-msg {{
    margin-top: 14px;
    font-size: 12px;
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
      <span>💡</span> Kéo dây hoặc bấm phím Cách để bật đèn
    </div>
  </div>

  <!-- Thẻ Đăng Nhập -->
  <div class="card-area">
    <div class="dark-hint">
      <div style="font-size: 28px; margin-bottom: 8px;">🛋️</div>
      Phòng đang tối.<br>Hãy kéo dây đèn để bật sáng hệ thống.
    </div>

    <div class="login-card" id="loginCard">
      <div class="brand-badge">⚡ AI Quant Gateway</div>
      <h2 class="card-title">Welcome</h2>
      <p class="card-subtitle">Hệ thống phân tích tài chính & đầu tư định lượng</p>

      <form id="loginForm" onsubmit="event.preventDefault(); handleLogin();">
        <div class="form-group">
          <label class="form-label" for="username">Username</label>
          <input class="form-input" id="username" type="text" value="{default_user}" placeholder="admin" required autocomplete="username" />
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input class="form-input" id="password" type="password" value="admin" placeholder="••••••••" required autocomplete="current-password" />
        </div>

        <button type="submit" class="btn-submit" id="btnSubmit">
          <span>Sign In</span>
          <span>→</span>
        </button>

        <button type="button" class="btn-demo" onclick="handleDemoLogin()">
          ⚡ Đăng nhập nhanh (Khách / Demo)
        </button>

        <div class="status-msg" id="statusMsg"></div>
      </form>
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
    const duration = 240; // ms

    function animate(now) {{
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      // Overshoot bounce equation tương tự Tkinter
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
      pullTooltip.innerHTML = '<span>💡</span> Đèn đã bật! Nhập tài khoản hoặc kéo dây để tắt';
    }} else {{
      document.body.classList.remove('lamp-on');
      pullTooltip.innerHTML = '<span>💡</span> Kéo dây hoặc bấm phím Cách để bật đèn';
    }}
  }}

  // Xử lý kéo thả (Pointer Events: chuột + cảm ứng)
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

  // Click vào núm giật nếu không kéo
  cordHitArea.addEventListener('click', (e) => {{
    if (currentPull < 5) {{
      updateCord(45);
      setTimeout(() => {{
        snapBack(() => toggleLamp());
      }}, 80);
    }}
  }});

  // Phím Space để kéo dây
  window.addEventListener('keydown', (e) => {{
    if (e.code === 'Space' && e.target.tagName !== 'INPUT') {{
      e.preventDefault();
      updateCord(50);
      setTimeout(() => {{
        snapBack(() => toggleLamp());
      }}, 100);
    }}
  }});

  // --- XỬ LÝ ĐĂNG NHẬP ---
  function sendAuthToStreamlit(user) {{
    statusMsg.innerText = `Xin chào, ${{user}}! Đang mở hệ thống...`;
    
    // Gửi thông điệp qua parent URL query params
    try {{
      const target = window.parent || window.top;
      if (target && target.location) {{
        const url = new URL(target.location.href);
        url.searchParams.set('auth', 'true');
        url.searchParams.set('user', user);
        target.location.href = url.toString();
      }}
    }} catch(e) {{
      console.warn('Parent window redirect restricted:', e);
    }}
    
    // Đăng tin qua postMessage để hỗ trợ Streamlit Component
    try {{
      window.parent.postMessage({{ type: 'STREAMLIT_AUTH', user: user }}, '*');
    }} catch(e) {{}}
  }}

  function handleLogin() {{
    const user = document.getElementById('username').value.trim() || 'Admin';
    sendAuthToStreamlit(user);
  }}

  function handleDemoLogin() {{
    document.getElementById('username').value = 'Guest_Trader';
    sendAuthToStreamlit('Guest_Trader');
  }}
</script>
</body>
</html>
"""


def render_login_screen() -> None:
    """Hiển thị màn hình Lamp Login đầy đủ trước khi cho phép vào nền tảng."""
    # 1. Kiểm tra query parameters từ iframe redirect
    query_auth = st.query_params.get("auth")
    if query_auth == "true":
        user = st.query_params.get("user", "Admin")
        st.session_state["authenticated"] = True
        st.session_state["username"] = user
        st.query_params.clear()
        st.rerun()

    # 2. Render Interactive Lamp Animation Canvas
    # Streamlit component iframe
    components.html(build_lamp_html(initial_on=True, default_user="Admin"), height=580)

    # 3. Native Streamlit Quick Action Bar (Đảm bảo 100% người dùng đăng nhập mượt mà ở mọi trình duyệt)
    st.markdown(
        f'<div style="text-align:center;margin-top:10px;margin-bottom:20px;'
        f'padding:12px;background:{CARD_ON};border:1px solid rgba(216,180,95,0.3);'
        f'border-radius:10px;max-width:600px;margin-left:auto;margin-right:auto;">'
        f'<div style="font-size:13px;color:{GOLD};font-weight:700;margin-bottom:6px;">'
        f'⚡ XÁC THỰC TRUY CẬP HỆ THỐNG ĐỊNH LƯỢNG</div>'
        f'<div style="font-size:12px;color:{MUTED};margin-bottom:12px;">'
        f'Kéo dây đèn ở khung hoạt hình phía trên hoặc xác nhận nhanh trực tiếp bên dưới:</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    _, col_form, _ = st.columns([1, 2, 1])
    with col_form:
        with st.form("native_login_form"):
            user_input = st.text_input(
                "Tên đăng nhập (Username)",
                value="Admin",
                placeholder="Nhập tên đăng nhập...",
            )
            pass_input = st.text_input(
                "Mật khẩu (Password)",
                value="admin",
                type="password",
                placeholder="Nhập mật khẩu...",
            )
            c1, c2 = st.columns(2)
            btn_signin = c1.form_submit_button(
                "✨ Đăng nhập (Sign In)",
                use_container_width=True,
                type="primary",
            )
            btn_guest = c2.form_submit_button(
                "⚡ Vào nhanh (Guest)",
                use_container_width=True,
            )

            if btn_signin or btn_guest:
                chosen_user = (user_input.strip() or "Admin") if btn_signin else "Guest_Trader"
                st.session_state["authenticated"] = True
                st.session_state["username"] = chosen_user
                st.success(f"🎉 Xin chào, **{chosen_user}**! Đang kết nối vào hệ thống định lượng...")
                st.rerun()
