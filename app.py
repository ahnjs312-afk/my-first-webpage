import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🪢 Rope Balance Catcher (2초 안착 물리 캐치 게임)")
st.caption("💡 **조작법**: [좌측 축] `A` / `D` | [우측 축] `⬅️` / `➡️` | 사과가 로프 좌우 범위 안에서 2초 동안 머무르게 하면 점수를 얻어요! (먼저 게임 화면을 한 번 클릭해주세요)")

import base64 as _b64

def _img_b64(path, mime):
    data = open(path, "rb").read()
    return f"data:{mime};base64,{_b64.b64encode(data).decode()}"

_bg_layers = [
    _img_b64("assets/1.png", "image/png"),  # 하늘 배경 — 가장 뒤, 고정
    _img_b64("assets/2.png", "image/png"),  # 뒤 구름 — 느리게
    _img_b64("assets/3.png", "image/png"),  # 앞 구름 — 빠르게
    _img_b64("assets/4.png", "image/png"),  # 투명 레이어 — 가장 앞
]
_apple_src   = _img_b64("assets/Apple.png",   "image/png")
_crystal_src = _img_b64("assets/Crystal.png", "image/png")
_bomb_src    = _img_b64("assets/Bomb.png",    "image/png")

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        /* ── 디자인 토큰 ───────────────────────────────────── */
        :root {{
            --bg:        #f8f9fb;
            --surface:   #ffffff;
            --border:    #e4e7ed;
            --shadow:    0 2px 16px rgba(0,0,0,0.07);

            --text-primary:   #18181b;
            --text-secondary: #52525b;
            --text-muted:     #a1a1aa;

            --accent:    #6366f1;
            --accent-lt: #eef2ff;

            --green:     #22c55e;
            --yellow:    #eab308;
            --red:       #ef4444;

            --radius-sm: 8px;
            --radius-md: 14px;
            --radius-lg: 20px;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            overflow: hidden;
            background: var(--bg);
            display: flex;
            flex-direction: column;
            align-items: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}

        /* ── HUD ───────────────────────────────────────────── */
        .hud {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 6px 8px;
            box-shadow: var(--shadow);
        }}
        .hud-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 4px 14px;
            font-size: 15px;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .hud-divider {{ width: 1px; height: 22px; background: var(--border); }}
        .hud-label {{
            font-size: 11px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }}
        .btn-reset {{
            background: var(--accent-lt);
            color: var(--accent);
            border: 1px solid #c7d2fe;
            padding: 5px 14px;
            font-size: 13px;
            font-weight: 700;
            border-radius: var(--radius-sm);
            cursor: pointer;
            margin-left: 6px;
            transition: background 0.15s;
        }}
        .btn-reset:hover {{ background: #e0e7ff; }}

        /* ── 캔버스 ────────────────────────────────────────── */
        canvas {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            box-shadow: var(--shadow);
            outline: none;
            display: block;
            image-rendering: pixelated;
            image-rendering: crisp-edges;
        }}
        .hint {{
            font-size: 12px;
            color: var(--text-muted);
            margin-top: 8px;
        }}

        /* ── 씬 공통 (로비 / 설명 오버레이) ───────────────── */
        .scene {{
            position: absolute;
            top: 0; left: 0;
            width: 850px; height: 580px;
            background: var(--surface);
            border-radius: var(--radius-md);
            border: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10;
            user-select: none;
        }}

        /* ── 로비 씬 ───────────────────────────────────────── */
        .lobby-title {{
            font-size: 36px;
            font-weight: 900;
            color: var(--text-primary);
            letter-spacing: -1px;
            margin-bottom: 8px;
        }}
        .lobby-sub {{
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 48px;
            font-weight: 400;
        }}
        .lobby-btns {{
            display: flex;
            flex-direction: column;
            gap: 12px;
            align-items: center;
        }}

        /* ── 설명 씬 ───────────────────────────────────────── */
        .howto-title {{
            font-size: 13px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 32px;
        }}
        .howto-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px 48px;
            margin-bottom: 40px;
            width: 560px;
        }}
        .howto-section-label {{
            font-size: 11px;
            font-weight: 700;
            color: var(--accent);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 14px;
        }}
        .howto-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
            color: var(--text-secondary);
        }}
        .howto-row:last-child {{ border-bottom: none; }}
        .howto-key {{ display: flex; gap: 4px; }}
        kbd {{
            background: var(--bg);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-bottom-width: 2px;
            border-radius: 5px;
            padding: 2px 9px;
            font-size: 12px;
            font-weight: 700;
            font-family: inherit;
        }}
        .badge {{
            font-size: 12px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 99px;
        }}
        .badge-green  {{ background: #dcfce7; color: #16a34a; }}
        .badge-yellow {{ background: #fef9c3; color: #a16207; }}
        .badge-red    {{ background: #fee2e2; color: #dc2626; }}

        /* ── 버튼 공통 ─────────────────────────────────────── */
        .btn-primary {{
            background: var(--accent);
            color: #fff;
            border: none;
            padding: 12px 40px;
            font-size: 14px;
            font-weight: 700;
            border-radius: 99px;
            cursor: pointer;
            box-shadow: 0 4px 18px rgba(99,102,241,0.3);
            transition: transform 0.1s, box-shadow 0.1s, background 0.15s;
            letter-spacing: 0.3px;
        }}
        .btn-primary:hover {{
            background: #4f46e5;
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(99,102,241,0.4);
        }}
        .btn-primary:active {{ transform: translateY(0); }}
        .btn-ghost {{
            background: transparent;
            color: var(--text-muted);
            border: none;
            padding: 8px 20px;
            font-size: 13px;
            font-weight: 600;
            border-radius: 99px;
            cursor: pointer;
            transition: color 0.15s;
        }}
        .btn-ghost:hover {{ color: var(--text-secondary); }}
    </style>
</head>
<body>

    <!-- 인게임 HUD -->
    <div class="hud">
        <div class="hud-item">
            <span class="hud-label">SCORE</span>
            <span id="score">0</span>
        </div>
        <div class="hud-divider"></div>
        <div class="hud-item">
            <span class="hud-label">LIVES</span>
            <span id="lives">♥ ♥ ♥</span>
        </div>
        <button class="btn-reset" onclick="startGame()">Reset</button>
    </div>

    <!-- 씬 래퍼 -->
    <div style="position: relative; width: 850px; height: 580px;">

        <!-- 씬 1: 로비 -->
        <div id="scene-lobby" class="scene">
            <div class="lobby-title">Rope Balance Catcher</div>
            <div class="lobby-sub">Balance items on the rope to score</div>
            <div class="lobby-btns">
                <button class="btn-primary" id="startBtn" onclick="startGame()">Play</button>
                <button class="btn-ghost" onclick="showScene('scene-howto')">How to play</button>
            </div>
        </div>

        <!-- 씬 2: 설명 -->
        <div id="scene-howto" class="scene" style="display:none;">
            <div class="howto-title">How to play</div>
            <div class="howto-grid">

                <!-- 조작 -->
                <div>
                    <div class="howto-section-label">Controls</div>
                    <div class="howto-row">
                        <span>Left anchor</span>
                        <div class="howto-key"><kbd>A</kbd><kbd>D</kbd></div>
                    </div>
                    <div class="howto-row">
                        <span>Right anchor</span>
                        <div class="howto-key"><kbd>◀</kbd><kbd>▶</kbd></div>
                    </div>
                </div>

                <!-- 아이템 -->
                <div>
                    <div class="howto-section-label">Items</div>
                    <div class="howto-row">
                        <span>Apple — hold 2s</span>
                        <span class="badge badge-green">+15</span>
                    </div>
                    <div class="howto-row">
                        <span>Crystal — hold 2s</span>
                        <span class="badge badge-yellow">+35</span>
                    </div>
                    <div class="howto-row">
                        <span>Bomb — avoid</span>
                        <span class="badge badge-red">−1 life</span>
                    </div>
                </div>

                <!-- 규칙 -->
                <div>
                    <div class="howto-section-label">Rules</div>
                    <div class="howto-row">
                        <span>Starting lives</span>
                        <span style="font-weight:700;">3</span>
                    </div>
                    <div class="howto-row">
                        <span>Drop penalty</span>
                        <span class="badge badge-red">−1 life</span>
                    </div>
                    <div class="howto-row">
                        <span>Difficulty</span>
                        <span style="color:var(--text-muted);font-size:12px;">Increases over time</span>
                    </div>
                </div>

                <!-- 팁 -->
                <div>
                    <div class="howto-section-label">Tips</div>
                    <div class="howto-row">
                        <span>Keep rope taut</span>
                        <span style="color:var(--text-muted);font-size:12px;">Wider = more stable</span>
                    </div>
                    <div class="howto-row">
                        <span>Watch the arc</span>
                        <span style="color:var(--text-muted);font-size:12px;">Shows 2s progress</span>
                    </div>
                    <div class="howto-row">
                        <span>Crystal scores</span>
                        <span style="color:var(--text-muted);font-size:12px;">2× more than apple</span>
                    </div>
                </div>

            </div>
            <button class="btn-ghost" onclick="showScene('scene-lobby')">Back</button>
        </div>

        <canvas id="canvas" width="850" height="580" tabindex="0"></canvas>
    </div>

    <div class="hint" id="hint" style="visibility:hidden;">Click the canvas to enable keyboard input</div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        // 픽셀이 뭉개지지 않고 또렷하게 (nearest-neighbor 보간)
        ctx.imageSmoothingEnabled = false;

        // ---- 스프라이트 이미지 ----
        // 사과·크리스탈은 개별 PNG, 폭탄은 이모지 폴백 유지
        const imgApple   = new Image(); imgApple.src   = "{_apple_src}";
        const imgCrystal = new Image(); imgCrystal.src = "{_crystal_src}";
        const imgBomb    = new Image(); imgBomb.src    = "{_bomb_src}";

        // 캔버스에 포커스를 줘야 iframe 안에서 키 입력이 확실히 잡힘
        canvas.addEventListener('click', () => canvas.focus());

        let isLobby = true;

        function showScene(id) {{
            ['scene-lobby', 'scene-howto'].forEach(s => {{
                document.getElementById(s).style.display = s === id ? 'flex' : 'none';
            }});
        }}

        function startGame() {{
            showScene(null); // 모든 씬 숨김
            document.getElementById('hint').style.visibility = 'visible';
            isLobby = false;
            resetGame();
            canvas.focus();
        }}

        // ---- 물리/난이도 상수 ----
        // 아래 값들은 "초당" 기준으로 튜닝되어 있고, 고정 타임스텝(STEP_MS)으로 매 프레임 동일하게 적용됩니다.
        // 그래서 60Hz든 144Hz든, 혹은 컴퓨터가 느려서 프레임이 드문드문 나와도 게임 속도는 항상 같습니다.
        const STEP_MS = 1000 / 60;      // 물리 연산은 항상 1/60초 단위로 진행 (모니터 주사율과 무관)
        const MAX_STEPS_PER_FRAME = 5;  // 브라우저 탭이 잠깐 멈췄다가 돌아와도 한번에 폭주하지 않도록 상한

        const ropeGravity = 0.16;
        const ropeFriction = 0.985;
        const MAX_ROPE_SPEED = 12;         // 로프 입자 1스텝 최대 이동량 (수치 폭주 시 안전장치)

        const BASE_ITEM_GRAVITY = 0.045;   // 게임 시작 시 낙하 중력
        const MAX_ITEM_GRAVITY = 0.09;     // 시간이 지나며 도달하는 최대 낙하 중력
        const MAX_ITEM_SPEED = 14;         // 아이템 1스텝 최대 이동량 (이보다 빠르면 스윕 검사 부담이 커짐)
        let currentItemGravity = BASE_ITEM_GRAVITY; // 난이도에 따라 매 스텝 갱신됨

        const SUCCESS_STEPS = 120;         // 성공 판정까지 필요한 스텝 수 (60스텝=1초 -> 120스텝=2초)
        const XRANGE_MARGIN = 10;          // 로프 x축 판정 범위에 좌우로 살짝 여유를 줌

        // [수정] ropePoints를 22 -> 28로 늘려 로프의 물리적 총 길이를 확보한다.
        // 기존에는 총 길이가 21*17 = 357px 뿐인데 축은 최대 790px까지 벌어질 수 있었다.
        // 즉 357짜리 줄을 790까지 당기는 "불가능한 제약" 상태가 되어, 제약 해결기가 매 반복마다
        // 입자를 크게 끌어당기고 그 위치 변화가 Verlet 속도로 그대로 변환되면서
        // 로프가 채찍처럼 폭주 -> 아이템이 튕겨나가거나 로프를 뚫는 근본 원인이었다.
        const ropePoints = 28;
        const restLen = 17;
        const ROPE_TOTAL_LEN = (ropePoints - 1) * restLen;   // 27 * 17 = 459px
        const MAX_SPAN = ROPE_TOTAL_LEN * 0.97;              // 약 445px — 이 이상으로는 절대 벌어지지 않음
        // [수정] 최소 간격을 175px로 상향.
        // 정적 상태에서는 어떤 간격에서도 세그먼트 교차가 없지만, 축을 급격히 좁힐 때
        // 로프 관성으로 세그먼트가 일시적으로 교차하면서 관통이 발생한다.
        // 실측 결과 관통이 발생하는 시나리오의 간격이 모두 170~180px 이내였으므로,
        // 그 영역 자체를 게임에서 원천 차단한다. (기존 60px)
        // 소프트 리밋: 이 간격 이하로 좁혀지면 스프링 반발력이 생긴다.
        // 하드 클램프(벽처럼 딱 막힘)와 달리 자연스럽게 저항하며,
        // 아주 급격히 좁히는 극단적 상황에서만 가끔 관통이 생길 수 있다.
        const SOFT_MIN_SPAN  = 120;  // 이 간격부터 반발력 시작
        const SOFT_SPRING_K  = 0.4;  // 반발력 강도 (클수록 더 강하게 밀어냄)

        let leftPinX = 250;
        let rightPinX = 600;
        let leftPinVX = 0;   // 좌측 축 관성 속도
        let rightPinVX = 0;  // 우측 축 관성 속도
        const pinsY = 320;
        const pinAccel = 0.55;
        const pinMaxSpeed = 8;
        const pinFriction = 0.90; // 키를 뗐을 때 속도가 줄어드는 비율(관성 감쇠)

        // ---- 충돌 처리 관련 상수 ----
        const SQUEEZE_ITERATIONS = 6;   // 양쪽 세그먼트에 '끼는' 상황을 풀기 위한 반복 보정 횟수
        const PIN_RADIUS = 12;          // 축(핀)의 충돌 반지름 — 화면에 그려지는 원 크기와 동일
        const CONTACT_SKIN = 3;         // 접촉 유지용 여유 두께
        const RESTITUTION = 0.15;       // 반발 계수 (0에 가까울수록 덜 튐)
        const SLIDE_FACTOR = 0.5;       // 경사면을 따라 미끄러지는 정도
        const ROPE_PUSH = 1.2;          // 아이템이 로프를 눌러 들어가는 총량 (반복 횟수로 나눠서 적용)
        const ROPE_PUSH_VEL_RATIO = 0.3; // 눌린 양 중 실제 속도로 전환되는 비율 (나머지는 위치만 이동)

        const BASE_SPAWN_INTERVAL = 130;   // 게임 시작 시 아이템 생성 간격(스텝)
        const MIN_SPAWN_INTERVAL = 55;     // 시간이 지나며 도달하는 최소 생성 간격(더 자주 등장)
        const BASE_BOMB_CHANCE = 0.20;     // 게임 시작 시 폭탄 등장 확률
        const MAX_BOMB_CHANCE = 0.40;      // 시간이 지나며 도달하는 최대 폭탄 확률
        const DIFFICULTY_RAMP_STEPS = 60 * 90; // 90초에 걸쳐 최대 난이도에 도달

        let gameSteps = 0; // 게임 시작 후 누적 스텝 수 (난이도 스케일링 기준)

        let particles = [];
        let constraints = [];
        let fallingItems = [];
        let effects = [];
        let score = 0;
        let lives = 3;
        let spawnCountdown = BASE_SPAWN_INTERVAL; // 카운트다운 방식 스폰 타이머 (난이도 변화에 안전)
        let isGameOver = false;

        const keys = {{}};
        const trackedKeys = new Set(['a', 'A', 'd', 'D', 'ArrowLeft', 'ArrowRight']);

        window.addEventListener('keydown', e => {{
            if (trackedKeys.has(e.key)) e.preventDefault(); // 부모 페이지 스크롤 방지
            keys[e.key] = true;
        }});
        window.addEventListener('keyup', e => {{
            if (trackedKeys.has(e.key)) e.preventDefault();
            keys[e.key] = false;
        }});

        class Particle {{
            constructor(x, y, isLeftPin = false, isRightPin = false) {{
                this.x = x;
                this.y = y;
                this.oldx = x;
                this.oldy = y;
                this.isLeftPin = isLeftPin;
                this.isRightPin = isRightPin;
            }}

            update() {{
                if (this.isLeftPin || this.isRightPin) return;
                let vx = (this.x - this.oldx) * ropeFriction;
                let vy = (this.y - this.oldy) * ropeFriction;

                // [수정] 속도 상한. 수치적으로 한 번 폭주가 시작되면 로프 전체가 발산해버리므로
                // 마지막 안전장치로 스텝당 이동량을 제한한다.
                let speed = Math.hypot(vx, vy);
                if (speed > MAX_ROPE_SPEED) {{
                    vx = vx / speed * MAX_ROPE_SPEED;
                    vy = vy / speed * MAX_ROPE_SPEED;
                }}

                this.oldx = this.x;
                this.oldy = this.y;
                this.x += vx;
                this.y += vy + ropeGravity;
            }}
        }}

        class Constraint {{
            constructor(p1, p2, restLength) {{
                this.p1 = p1;
                this.p2 = p2;
                this.length = restLength;
            }}

            resolve() {{
                let dx = this.p2.x - this.p1.x;
                let dy = this.p2.y - this.p1.y;
                let dist = Math.hypot(dx, dy);
                if (dist === 0) return;
                let diff = (this.length - dist) / dist * 0.5;

                if (!this.p1.isLeftPin && !this.p1.isRightPin) {{
                    this.p1.x -= dx * diff;
                    this.p1.y -= dy * diff;
                }}
                if (!this.p2.isLeftPin && !this.p2.isRightPin) {{
                    this.p2.x += dx * diff;
                    this.p2.y += dy * diff;
                }}
            }}
        }}

        class Sparkle {{
            constructor(x, y, color) {{
                this.x = x;
                this.y = y;
                this.vx = (Math.random() - 0.5) * 7;
                this.vy = (Math.random() - 0.5) * 7;
                this.radius = 3 + Math.random() * 4;
                this.color = color;
                this.alpha = 1.0;
            }}

            update() {{
                this.x += this.vx;
                this.y += this.vy;
                this.alpha -= 0.03;
            }}

            draw() {{
                ctx.save();
                ctx.globalAlpha = Math.max(0, this.alpha);
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }}
        }}

        class FallingItem {{
            constructor(x, y, type) {{
                this.x = x;
                this.y = y;
                this.prevX = x; // 스윕(swept) 충돌 검사를 위한 이전 스텝 위치
                this.prevY = y;
                this.vx = 0; // 가로 쏠림 방지 (직하강)
                this.vy = 0; 
                this.type = type; // 'apple', 'star', 'bomb'
                this.radius = type === 'star' ? 15 : 18;
                this.touchTimer = 0; // 로프 위에서 유지한 스텝 수 (SUCCESS_STEPS = 2초)
                this.isOnRope = false;
                this.hasTouchedRope = false;
                // 회전: 낙하 중 천천히 회전하다가 로프에 닿으면 경사각으로 고정
                this.angle    = 0;
                this.angleVel = (Math.random() < 0.5 ? 1 : -1)
                              * (1 + Math.random()) * Math.PI / 180; // 1~2°/스텝
                this.angleLocked = false; // true가 되면 로프 경사각으로 고정
            }}

            update() {{
                this.prevX = this.x;
                this.prevY = this.y;
                this.vy += currentItemGravity;

                // [수정] 아이템 속도 상한. 스텝당 이동량이 너무 커지면 스윕 검사로도 잡기 어려운
                // 극단적인 관통이 생기고, 반사 시 에너지도 과하게 튄다.
                let speed = Math.hypot(this.vx, this.vy);
                if (speed > MAX_ITEM_SPEED) {{
                    this.vx = this.vx / speed * MAX_ITEM_SPEED;
                    this.vy = this.vy / speed * MAX_ITEM_SPEED;
                }}

                this.x += this.vx;
                this.y += this.vy;
                this.vx *= 0.98;

                // 낙하 중에는 회전, 로프에 닿으면 각도 고정
                if (!this.angleLocked) this.angle += this.angleVel;
            }}

            draw() {{
                const d = this.radius * 2;

                ctx.save();
                ctx.translate(this.x, this.y);
                ctx.rotate(this.angle);

                // 중심 기준으로 그리기 (translate 후 -radius 오프셋)
                const half = -this.radius;
                if (this.type === 'apple' && imgApple.complete && imgApple.naturalWidth > 0) {{
                    ctx.drawImage(imgApple, half, half, d, d);
                }} else if (this.type === 'star' && imgCrystal.complete && imgCrystal.naturalWidth > 0) {{
                    ctx.drawImage(imgCrystal, half, half, d, d);
                }} else if (this.type === 'bomb' && imgBomb.complete && imgBomb.naturalWidth > 0) {{
                    ctx.drawImage(imgBomb, half, half, d, d);
                }} else {{
                    // 이미지 로드 전 폴백
                    ctx.font = "18px sans-serif";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText(this.type === 'apple' ? '🍎'
                               : this.type === 'star'  ? '⭐' : '💣',
                                 0, 0);
                }}

                ctx.restore();

                // 안착 타이머 게이지 (회전 없이 항상 정방향)
                if (this.hasTouchedRope && (this.type === 'apple' || this.type === 'star')) {{
                    let progress = Math.min(1.0, this.touchTimer / SUCCESS_STEPS);
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.radius + 5, -Math.PI / 2,
                            -Math.PI / 2 + Math.PI * 2 * progress);
                    ctx.strokeStyle = this.type === 'apple' ? '#22c55e' : '#3b82f6';
                    ctx.lineWidth = 3.5;
                    ctx.stroke();
                }}
            }}
        }}

        function initRope() {{
            particles = [];
            constraints = [];
            let widthStep = (rightPinX - leftPinX) / (ropePoints - 1);

            for (let i = 0; i < ropePoints; i++) {{
                let isLeftPin = (i === 0);
                let isRightPin = (i === ropePoints - 1);
                let x = leftPinX + i * widthStep;
                let y = pinsY;
                particles.push(new Particle(x, y, isLeftPin, isRightPin));
            }}

            for (let i = 0; i < ropePoints - 1; i++) {{
                constraints.push(new Constraint(particles[i], particles[i + 1], restLen));
            }}
        }}

        function createParticles(x, y, color, count = 15) {{
            for (let i = 0; i < count; i++) {{
                effects.push(new Sparkle(x, y, color));
            }}
        }}

        function resetGame() {{
            leftPinX = 250;
            rightPinX = 600;
            leftPinVX = 0;
            rightPinVX = 0;
            gameSteps = 0;
            currentItemGravity = BASE_ITEM_GRAVITY;
            fallingItems = [];
            effects = [];
            score = 0;
            lives = 3;
            spawnCountdown = BASE_SPAWN_INTERVAL;
            isGameOver = false;
            initRope();
            updateUI();
            canvas.focus();
        }}

        function updateUI() {{
            document.getElementById('score').innerText = score;
            const hearts = '♥ '.repeat(Math.max(0, lives)).trim();
            document.getElementById('lives').innerText = hearts;
        }}

        // 두 선분(A: 아이템의 이동 경로, B: 로프 세그먼트) 사이의 최단 거리를 구하는
        // 표준 "closest points between two segments" 알고리즘 (Ericson, Real-Time Collision Detection).
        // 이동 경로 전체를 검사하므로, 한 스텝에 로프 두께보다 멀리 이동해서 그냥 지나쳐버리는
        // 터널링을 감지할 수 있습니다.
        function closestDistBetweenSegments(p1, q1, p2, q2) {{
            const EPS = 1e-9;
            let d1x = q1.x - p1.x, d1y = q1.y - p1.y; // 경로 세그먼트 방향
            let d2x = q2.x - p2.x, d2y = q2.y - p2.y; // 로프 세그먼트 방향
            let rx = p1.x - p2.x, ry = p1.y - p2.y;

            let a = d1x * d1x + d1y * d1y;
            let e = d2x * d2x + d2y * d2y;
            let f = d2x * rx + d2y * ry;

            let s, t;
            if (a <= EPS && e <= EPS) {{
                s = 0; t = 0;
            }} else if (a <= EPS) {{
                s = 0;
                t = Math.max(0, Math.min(1, f / e));
            }} else {{
                let c = d1x * rx + d1y * ry;
                if (e <= EPS) {{
                    t = 0;
                    s = Math.max(0, Math.min(1, -c / a));
                }} else {{
                    let b = d1x * d2x + d1y * d2y;
                    let denom = a * e - b * b;
                    s = denom !== 0 ? Math.max(0, Math.min(1, (b * f - c * e) / denom)) : 0;
                    t = (b * s + f) / e;
                    if (t < 0) {{
                        t = 0;
                        s = Math.max(0, Math.min(1, -c / a));
                    }} else if (t > 1) {{
                        t = 1;
                        s = Math.max(0, Math.min(1, (b - c) / a));
                    }}
                }}
            }}

            let c1x = p1.x + d1x * s, c1y = p1.y + d1y * s; // 경로 위 최근접점
            let c2x = p2.x + d2x * t, c2y = p2.y + d2y * t; // 로프 세그먼트 위 최근접점
            let dx = c1x - c2x, dy = c1y - c2y;
            return {{ dist: Math.hypot(dx, dy), t, dx, dy, c2x, c2y }};
        }}

        // [수정] 로프 입자를 밀 때 쓰는 헬퍼.
        // Verlet에서는 위치만 바꾸면 그 변화량이 그대로 다음 스텝의 속도가 되어버린다.
        // (기존 코드의 p.y += 1.8이 반복 4회 누적되면 스텝당 7.2px = 초당 430px의 속도 주입!)
        // 여기서는 oldx/oldy도 함께 옮겨서, 밀어낸 양 중 일부만 속도로 남게 한다.
        function pushRopeParticle(p, dx, dy) {{
            if (p.isLeftPin || p.isRightPin) return;
            p.x += dx;
            p.y += dy;
            p.oldx += dx * (1 - ROPE_PUSH_VEL_RATIO);
            p.oldy += dy * (1 - ROPE_PUSH_VEL_RATIO);
        }}

        resetGame();

        function handleInput() {{
            // 좌측 축 (A/D): 키 입력으로 가속하고, 손을 떼면 서서히 감속(관성)
            if (keys['a'] || keys['A']) leftPinVX -= pinAccel;
            if (keys['d'] || keys['D']) leftPinVX += pinAccel;
            leftPinVX *= pinFriction;
            leftPinVX = Math.max(-pinMaxSpeed, Math.min(pinMaxSpeed, leftPinVX));
            leftPinX += leftPinVX;

            // 우측 축 (화살표): 동일한 관성 방식
            if (keys['ArrowLeft']) rightPinVX -= pinAccel;
            if (keys['ArrowRight']) rightPinVX += pinAccel;
            rightPinVX *= pinFriction;
            rightPinVX = Math.max(-pinMaxSpeed, Math.min(pinMaxSpeed, rightPinVX));
            rightPinX += rightPinVX;

            // 화면 경계
            if (leftPinX < 30) {{ leftPinX = 30; leftPinVX = 0; }}
            if (rightPinX > canvas.width - 30) {{ rightPinX = canvas.width - 30; rightPinVX = 0; }}

            // 소프트 리밋: 간격이 SOFT_MIN_SPAN 이하로 좁혀질수록
            // 두 축을 서로 밀어내는 반발력이 점점 강해진다.
            // 하드 클램프처럼 벽에 부딪히는 느낌 없이 자연스럽게 저항한다.
            {{
                let span = rightPinX - leftPinX;
                if (span < SOFT_MIN_SPAN) {{
                    let overlap = SOFT_MIN_SPAN - span;
                    let force   = overlap * SOFT_SPRING_K;
                    leftPinVX  -= force;
                    rightPinVX += force;
                }}
            }}

            // [수정] 최대 간격 제한 — 이게 폭주의 근본 원인이었다.
            // 로프의 실제 길이(ROPE_TOTAL_LEN)보다 축을 더 벌리면 제약 조건이 물리적으로
            // 만족 불가능해지고, 해결기가 매 반복 입자를 크게 끌어당겨 속도가 발산한다.
            // 바깥으로 나가려던 축을 그 비율만큼 되돌려서 자연스럽게 "다 당겨진 느낌"으로 멈춘다.
            let span = rightPinX - leftPinX;
            if (span > MAX_SPAN) {{
                let over = span - MAX_SPAN;
                let leftOutward = Math.max(0, -leftPinVX);  // 왼쪽 축이 바깥(왼쪽)으로 가는 속도
                let rightOutward = Math.max(0, rightPinVX); // 오른쪽 축이 바깥(오른쪽)으로 가는 속도
                let total = leftOutward + rightOutward;

                if (total > 1e-6) {{
                    leftPinX += over * (leftOutward / total);
                    rightPinX -= over * (rightOutward / total);
                }} else {{
                    leftPinX += over / 2;
                    rightPinX -= over / 2;
                }}
                if (leftPinVX < 0) leftPinVX = 0;
                if (rightPinVX > 0) rightPinVX = 0;
            }}

            // [중요] 핀은 update()를 건너뛰므로 oldx/oldy가 갱신되지 않는다.
            // 그런데 아래 충돌 검사에서 로프의 이동량을 (x - oldx)로 추정하기 때문에,
            // 핀의 old 좌표를 갱신해두지 않으면 핀에 붙은 세그먼트의 이동량이 엉뚱한 값이 되어
            // 스윕 검사가 무너진다. 여기서 "이전 위치 -> 현재 위치"가 되도록 직접 갱신한다.
            let leftPin = particles[0];
            let rightPin = particles[ropePoints - 1];

            leftPin.oldx = leftPin.x;
            leftPin.oldy = leftPin.y;
            leftPin.x = leftPinX;
            leftPin.y = pinsY;

            rightPin.oldx = rightPin.x;
            rightPin.oldy = rightPin.y;
            rightPin.x = rightPinX;
            rightPin.y = pinsY;
        }}

        // 물리/게임 로직 한 스텝 (항상 동일한 "가상 시간" 단위로 실행됨 -> 기기 성능과 무관)
        function step() {{
            if (isLobby || isGameOver) return;

            gameSteps++;

            // 난이도 스케일링: 게임이 진행될수록(DIFFICULTY_RAMP_STEPS 동안) 서서히 어려워짐
            let difficulty = Math.min(1, gameSteps / DIFFICULTY_RAMP_STEPS);
            let currentSpawnInterval = Math.round(
                BASE_SPAWN_INTERVAL - (BASE_SPAWN_INTERVAL - MIN_SPAWN_INTERVAL) * difficulty
            );
            let currentBombChance = BASE_BOMB_CHANCE + (MAX_BOMB_CHANCE - BASE_BOMB_CHANCE) * difficulty;
            currentItemGravity = BASE_ITEM_GRAVITY + (MAX_ITEM_GRAVITY - BASE_ITEM_GRAVITY) * difficulty;

            handleInput();

            // 1. 물체 생성 (카운트다운 방식: currentSpawnInterval이 난이도에 따라 매 프레임 바뀌어도
            //    나머지 연산(%)처럼 정확히 0이 되는 시점을 놓쳐 스폰이 씹히는 문제가 없음)
            spawnCountdown--;
            if (spawnCountdown <= 0) {{
                spawnCountdown += currentSpawnInterval;
                let spawnX = 60 + Math.random() * (canvas.width - 120);
                let rand = Math.random();
                let appleChance = (1 - currentBombChance) * 0.75; // 사과:별 비율은 기존처럼 3:1 유지
                let type = rand < appleChance ? 'apple' : (rand < 1 - currentBombChance ? 'star' : 'bomb');
                fallingItems.push(new FallingItem(spawnX, -20, type));
            }}

            // 2. 물리 연산
            particles.forEach(p => p.update());
            for (let i = 0; i < 8; i++) {{
                constraints.forEach(c => c.resolve());
            }}

            fallingItems.forEach(item => item.update());

            // 3. 로프와 원형 물체 충돌 처리
            fallingItems.forEach(item => {{
                let anyCollision = false;
                let lastBest = null;

                for (let iter = 0; iter < SQUEEZE_ITERATIONS; iter++) {{
                    let best = null;
                    let pathEnd = {{ x: item.x, y: item.y }};

                    for (let i = 0; i < particles.length - 1; i++) {{
                        let ropeP1 = particles[i], ropeP2 = particles[i + 1];

                        // [수정] 로프 자체의 이번 스텝 이동량만큼 아이템의 출발점을 보정해서
                        // "상대 운동"으로 검사한다. 기존에는 로프를 정지 상태로 취급했기 때문에,
                        // 축을 빠르게 움직여 로프가 아이템 쪽으로 휘둘러 올라오는 경우
                        // 로프가 아이템을 그냥 스쳐 지나가버렸다(관통).
                        let segDispX = ((ropeP1.x - ropeP1.oldx) + (ropeP2.x - ropeP2.oldx)) * 0.5;
                        let segDispY = ((ropeP1.y - ropeP1.oldy) + (ropeP2.y - ropeP2.oldy)) * 0.5;

                        // [수정] 1회차만 스윕(이전 위치 -> 현재 위치) 검사를 하고,
                        // 2회차부터는 이미 보정된 현재 위치만 점으로 검사한다.
                        // 기존에는 매 반복마다 같은 "이전 위치"를 재사용해서 동일한 경로가 계속
                        // 재검출됐고, 그 결과 로프를 미는 힘이 반복 횟수만큼 누적되어 튀어올랐다.
                        let pathStart = (iter === 0)
                            ? {{ x: item.prevX + segDispX, y: item.prevY + segDispY }}
                            : {{ x: item.x, y: item.y }};

                        let res = closestDistBetweenSegments(pathStart, pathEnd, ropeP1, ropeP2);

                        if (res.dist < item.radius + CONTACT_SKIN && (!best || res.dist < best.dist)) {{
                            let segDx = ropeP2.x - ropeP1.x, segDy = ropeP2.y - ropeP1.y;
                            let segLen = Math.hypot(segDx, segDy) || 1;
                            let tx = segDx / segLen; // 세그먼트 접선 방향(정규화)
                            let ty = segDy / segLen;

                            // [수정] 밀어낼 방향은 "아이템이 원래 있던 쪽"으로 결정한다.
                            // 기존처럼 최근접점 방향(res.dx/res.dy)을 쓰면, 이미 로프를 지나쳐버린
                            // 경우 최근접점이 반대편에 생겨서 아이템을 관통한 쪽으로 확정시켜버렸다.
                            // 이것이 "로프를 뚫는" 현상의 직접적인 원인.
                            let nx0 = -ty, ny0 = tx; // 접선을 90도 회전한 법선
                            let refX = pathStart.x - ropeP1.x;
                            let refY = pathStart.y - ropeP1.y;
                            let side = (refX * nx0 + refY * ny0) >= 0 ? 1 : -1;

                            best = {{
                                dist: res.dist, t: res.t,
                                nx: nx0 * side, ny: ny0 * side, tx, ty,
                                p1: ropeP1, p2: ropeP2,
                                contactX: res.c2x, contactY: res.c2y
                            }};
                        }}
                    }}

                    if (!best) break; // 더 이상 겹치는 세그먼트가 없으면 수렴 완료

                    anyCollision = true;
                    lastBest = best;

                    // 로프 접점에서 정확히 (radius + skin)만큼, 원래 있던 쪽으로 떨어진 지점에 배치
                    item.x = best.contactX + best.nx * (item.radius + CONTACT_SKIN);
                    item.y = best.contactY + best.ny * (item.radius + CONTACT_SKIN);

                    // 접촉한 세그먼트도 눌리도록 반응 (반복 횟수로 나눠 총량을 일정하게 유지)
                    let push = ROPE_PUSH / SQUEEZE_ITERATIONS;
                    pushRopeParticle(best.p1, -best.nx * push * (1 - best.t), -best.ny * push * (1 - best.t));
                    pushRopeParticle(best.p2, -best.nx * push * best.t, -best.ny * push * best.t);
                }}

                if (anyCollision) {{
                    // [수정] 법선 방향으로 파고드는 속도 성분만 반사시킨다.
                    // 기존의 item.vy = -item.vy * 0.2는 로프가 기울어져 있어도 무조건 수직 성분만
                    // 뒤집어서, 경사면에서 엉뚱한 방향으로 에너지가 더해지며 튀어오르는 원인이 됐다.
                    let vn = item.vx * lastBest.nx + item.vy * lastBest.ny;
                    if (vn < 0) {{
                        item.vx -= (1 + RESTITUTION) * vn * lastBest.nx;
                        item.vy -= (1 + RESTITUTION) * vn * lastBest.ny;
                    }}
                    // 경사 방향(접선)을 따라 미끄러지는 힘: 로프가 기운 쪽으로만 슬라이드됨
                    item.vx += lastBest.tx * lastBest.ty * SLIDE_FACTOR;
                }}

                // [수정] 축(핀) 자체와의 충돌 처리.
                // 기존에는 축이 화면에 원으로 그려지기만 하고 충돌체가 없었다. 그래서 로프와 축이
                // 만나는 지점에 아이템이 끼면 빠져나갈 곳이 없어 로프를 뚫고 지나가버렸다.
                // (실제로 남아있던 관통은 전부 축에서 약 20px 이내 지점에 몰려 있었다)
                for (const pin of [{{ x: leftPinX, y: pinsY }}, {{ x: rightPinX, y: pinsY }}]) {{
                    let dx = item.x - pin.x, dy = item.y - pin.y;
                    let d = Math.hypot(dx, dy);
                    let minD = item.radius + PIN_RADIUS;
                    if (d < minD) {{
                        let nx = d > 1e-6 ? dx / d : 0;
                        let ny = d > 1e-6 ? dy / d : -1;
                        item.x = pin.x + nx * minD;
                        item.y = pin.y + ny * minD;
                        let vn = item.vx * nx + item.vy * ny;
                        if (vn < 0) {{
                            item.vx -= (1 + RESTITUTION) * vn * nx;
                            item.vy -= (1 + RESTITUTION) * vn * ny;
                        }}
                    }}
                }}

                item.isOnRope = anyCollision;
                if (item.isOnRope) {{
                    item.hasTouchedRope = true;
                    // 처음 닿는 순간 로프 경사각으로 각도를 고정한다.
                    // lastBest.tx/ty 는 접선 단위벡터이므로 atan2로 경사각을 구할 수 있다.
                    if (!item.angleLocked) {{
                        item.angle = Math.atan2(lastBest.ty, lastBest.tx);
                        item.angleLocked = true;
                    }}
                }}
            }});

            // 4. 아이템 2초 안착 / 폭발 / 낙하 판정
            fallingItems = fallingItems.filter(item => {{
                if (item.type === 'apple' || item.type === 'star') {{
                    // 한 번이라도 로프에 닿았다면, 이후로는 위아래로 미세하게 튕기거나 로프 표면에서
                    // 살짝 떠 있어도 상관없이 계속 카운트가 진행된다. x좌표가 로프의 좌우 범위를
                    // (여유값 XRANGE_MARGIN만큼) 완전히 벗어났을 때만 카운트를 리셋한다.
                    if (item.hasTouchedRope) {{
                        if (item.x < leftPinX - XRANGE_MARGIN || item.x > rightPinX + XRANGE_MARGIN) {{
                            item.touchTimer = 0;
                        }} else {{
                            item.touchTimer++;
                            // SUCCESS_STEPS(2초) 유지 성공 시 점수 획득
                            if (item.touchTimer >= SUCCESS_STEPS) {{
                                let color = item.type === 'apple' ? '#22c55e' : '#eab308';
                                createParticles(item.x, item.y, color, 20);
                                score += (item.type === 'apple' ? 15 : 35);
                                updateUI();
                                return false;
                            }}
                        }}
                    }}
                }} else if (item.type === 'bomb') {{
                    if (item.isOnRope) {{
                        createParticles(item.x, item.y, '#ef4444', 25);
                        lives--;
                        updateUI();
                        return false;
                    }}
                }}

                if (item.y > canvas.height + 30) {{
                    if (item.type === 'apple' || item.type === 'star') {{
                        lives--;
                        updateUI();
                    }}
                    return false;
                }}

                return true;
            }});

            if (lives <= 0) isGameOver = true;
        }}

        // ---- 배경 레이어 (패럴랙스) ----
        // 숫자 큰 파일이 앞(위)에, 작은 파일이 뒤(아래)에 그려진다.
        // speeds: 뒤 레이어일수록 느리게 스크롤해서 원근감(시차) 효과를 준다.
        const BG_LAYERS = [
            {{ src: "{_bg_layers[0]}", speed: 0.0 }},  // 1.png 하늘 배경 — 고정
            {{ src: "{_bg_layers[1]}", speed: 0.3 }},  // 2.png 뒤 구름 — 느리게
            {{ src: "{_bg_layers[2]}", speed: 0.15 }}, // 3.png 투명 레이어 — 천천히
            {{ src: "{_bg_layers[3]}", speed: 0.9 }},  // 4.png 앞 구름 — 빠르게
        ].map(l => {{
            const img = new Image();
            img.src = l.src;
            return {{ img, speed: l.speed, offset: 0 }};
        }});

        function drawBackground() {{
            // 가장 뒤 레이어(0번)를 먼저 그려 배경색을 채움
            // 투명 픽셀이 있을 수 있으니 흰 배경을 먼저 깔아둔다
            ctx.fillStyle = '#a8c8d8';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            for (const layer of BG_LAYERS) {{
                const {{ img, speed }} = layer;
                if (!img.complete || !img.naturalWidth) continue;

                const W = img.naturalWidth;
                const H = img.naturalHeight;

                // 게임 중일 때만 오프셋 전진 (로비에서는 정지)
                if (!isLobby) layer.offset = (layer.offset + speed) % W;

                // 캔버스 크기에 맞게 세로 스케일 (가로는 타일링)
                const scale = canvas.height / H;
                const dw = W * scale;
                const dh = canvas.height;

                // 왼쪽으로 스크롤 (오프셋만큼 왼쪽에서 시작)
                const startX = -(layer.offset * scale) % dw;
                for (let x = startX; x < canvas.width; x += dw) {{
                    ctx.drawImage(img, x, 0, dw, dh);
                }}
            }}
        }}

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 배경 (가장 먼저 그려서 모든 요소 뒤에 위치)
            drawBackground();

            // 이펙트 파티클
            effects = effects.filter(e => {{
                e.update();
                e.draw();
                return e.alpha > 0;
            }});

            // 로프 그리기 — 인디고 계열로 화이트 톤 통일
            ctx.beginPath();
            ctx.strokeStyle = '#6366f1';
            ctx.lineWidth = 5;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.moveTo(particles[0].x, particles[0].y);
            for (let i = 1; i < particles.length; i++) {{
                ctx.lineTo(particles[i].x, particles[i].y);
            }}
            ctx.stroke();

            // 좌 핀 (파랑)
            ctx.fillStyle = '#3b82f6';
            ctx.beginPath();
            ctx.arc(leftPinX, pinsY, 12, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.font = "bold 9px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText("A/D", leftPinX, pinsY);

            // 우 핀 (로즈)
            ctx.fillStyle = '#f43f5e';
            ctx.beginPath();
            ctx.arc(rightPinX, pinsY, 12, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.font = "bold 9px sans-serif";
            ctx.fillText("◀▶", rightPinX, pinsY);

            // 낙하 물체 그리기
            fallingItems.forEach(item => item.draw());

            // Game Over — 로비 씬으로 복귀
            if (isGameOver) {{
                document.getElementById('startBtn').textContent = 'Play again';
                showScene('scene-lobby');
                document.getElementById('hint').style.visibility = 'hidden';
                isLobby = true;
                isGameOver = false;
            }}
        }}

        // ---- 고정 타임스텝 메인 루프 ----
        // requestAnimationFrame은 화면 주사율에 따라 초당 호출 횟수가 다르지만(60Hz/120Hz/144Hz 등),
        // 여기서는 실제 경과 시간을 누적(accumulator)해서 항상 STEP_MS(1/60초) 단위로만 물리 연산을 수행합니다.
        let lastTime = performance.now();
        let accumulator = 0;

        function loop(now) {{
            let delta = now - lastTime;
            lastTime = now;

            // 탭 전환 등으로 delta가 비정상적으로 커지는 경우 대비 (스파이럴 오브 데스 방지)
            if (delta > STEP_MS * MAX_STEPS_PER_FRAME) {{
                delta = STEP_MS * MAX_STEPS_PER_FRAME;
            }}

            accumulator += delta;

            let steps = 0;
            while (accumulator >= STEP_MS && steps < MAX_STEPS_PER_FRAME) {{
                step();
                accumulator -= STEP_MS;
                steps++;
            }}

            draw();
            requestAnimationFrame(loop);
        }}

        requestAnimationFrame(loop);
    </script>
</body>
</html>
"""

components.html(html_code, height=680)
