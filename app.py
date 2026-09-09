import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🪢 Rope Balance Catcher (2초 안착 물리 캐치 게임)")
st.caption("💡 **조작법**: [좌측 축] `A` / `D` | [우측 축] `⬅️` / `➡️` | 사과가 로프 좌우 범위 안에서 2초 동안 머무르게 하면 점수를 얻어요! (먼저 게임 화면을 한 번 클릭해주세요)")

html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            margin: 0; 
            overflow: hidden; 
            background-color: #f7f9fc; 
            display: flex; 
            flex-direction: column;
            align-items: center; 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .ui-panel {
            display: flex;
            gap: 30px;
            align-items: center;
            margin-bottom: 10px;
        }
        .score-board {
            font-size: 18px;
            font-weight: bold;
            color: #1a202c;
        }
        .life-board {
            font-size: 18px;
            font-weight: bold;
            color: #e53e3e;
        }
        button {
            background-color: #3182ce;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        button:hover { background-color: #2b6cb0; }
        canvas { 
            background: #ffffff; 
            border: 2px solid #e2e8f0;
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
            outline: none;
        }
        .hint {
            font-size: 12px;
            color: #a0aec0;
            margin-top: 6px;
        }
    </style>
</head>
<body>
    <div class="ui-panel">
        <div class="score-board" id="score">SCORE: 0</div>
        <div class="life-board" id="lives">❤️❤️❤️</div>
        <button onclick="resetGame()">🔄 게임 리셋</button>
    </div>
    <canvas id="canvas" width="850" height="580" tabindex="0"></canvas>
    <div class="hint">화면을 클릭하면 키보드 입력이 활성화됩니다</div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        // 캔버스에 포커스를 줘야 iframe 안에서 키 입력이 확실히 잡힘
        canvas.addEventListener('click', () => canvas.focus());
        canvas.focus();

        // ---- 물리/난이도 상수 ----
        // 아래 값들은 "초당" 기준으로 튜닝되어 있고, 고정 타임스텝(STEP_MS)으로 매 프레임 동일하게 적용됩니다.
        // 그래서 60Hz든 144Hz든, 혹은 컴퓨터가 느려서 프레임이 드문드문 나와도 게임 속도는 항상 같습니다.
        const STEP_MS = 1000 / 60;      // 물리 연산은 항상 1/60초 단위로 진행 (모니터 주사율과 무관)
        const MAX_STEPS_PER_FRAME = 5;  // 브라우저 탭이 잠깐 멈췄다가 돌아와도 한번에 폭주하지 않도록 상한

        const ropeGravity = 0.16;      // 기존 0.25 -> 로프가 더 완만하게 출렁임
        const ropeFriction = 0.985;
        const BASE_ITEM_GRAVITY = 0.045;   // 게임 시작 시 낙하 중력
        const MAX_ITEM_GRAVITY = 0.09;     // 시간이 지나며 도달하는 최대 낙하 중력
        let currentItemGravity = BASE_ITEM_GRAVITY; // 난이도에 따라 매 스텝 갱신됨

        const SUCCESS_STEPS = 120;         // 성공 판정까지 필요한 스텝 수 (60스텝=1초 -> 120스텝=2초)
        const XRANGE_MARGIN = 10;          // 로프 x축 판정 범위에 좌우로 살짝 여유를 줌 (아이템 반지름 대비)

        const ropePoints = 22;
        const restLen = 17;
        // 최대 간격 제한(maxSpan)은 제거 -> 축을 끝까지 벌리면 로프가 팽팽하게 일직선으로 늘어남

        let leftPinX = 250;
        let rightPinX = 600;
        let leftPinVX = 0;   // 좌측 축 관성 속도
        let rightPinVX = 0;  // 우측 축 관성 속도
        const pinsY = 320;
        const pinAccel = 0.55;    // 기존 0.45 -> 가속도 소폭 상향
        const pinMaxSpeed = 8;    // 기존 6.5 -> 최대 이동 속도 소폭 상향
        const pinFriction = 0.90; // 키를 뗐을 때 속도가 줄어드는 비율(관성 감쇠)

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

        const keys = {};
        const trackedKeys = new Set(['a', 'A', 'd', 'D', 'ArrowLeft', 'ArrowRight']);

        window.addEventListener('keydown', e => {
            if (trackedKeys.has(e.key)) e.preventDefault(); // 부모 페이지 스크롤 방지
            keys[e.key] = true;
        });
        window.addEventListener('keyup', e => {
            if (trackedKeys.has(e.key)) e.preventDefault();
            keys[e.key] = false;
        });

        class Particle {
            constructor(x, y, isLeftPin = false, isRightPin = false) {
                this.x = x;
                this.y = y;
                this.oldx = x;
                this.oldy = y;
                this.isLeftPin = isLeftPin;
                this.isRightPin = isRightPin;
            }

            update() {
                if (this.isLeftPin || this.isRightPin) return;
                let vx = (this.x - this.oldx) * ropeFriction;
                let vy = (this.y - this.oldy) * ropeFriction;
                this.oldx = this.x;
                this.oldy = this.y;
                this.x += vx;
                this.y += vy + ropeGravity;
            }
        }

        class Constraint {
            constructor(p1, p2, restLength) {
                this.p1 = p1;
                this.p2 = p2;
                this.length = restLength;
            }

            resolve() {
                let dx = this.p2.x - this.p1.x;
                let dy = this.p2.y - this.p1.y;
                let dist = Math.hypot(dx, dy);
                if (dist === 0) return;
                let diff = (this.length - dist) / dist * 0.5;

                if (!this.p1.isLeftPin && !this.p1.isRightPin) {
                    this.p1.x -= dx * diff;
                    this.p1.y -= dy * diff;
                }
                if (!this.p2.isLeftPin && !this.p2.isRightPin) {
                    this.p2.x += dx * diff;
                    this.p2.y += dy * diff;
                }
            }
        }

        class Sparkle {
            constructor(x, y, color) {
                this.x = x;
                this.y = y;
                this.vx = (Math.random() - 0.5) * 7;
                this.vy = (Math.random() - 0.5) * 7;
                this.radius = 3 + Math.random() * 4;
                this.color = color;
                this.alpha = 1.0;
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;
                this.alpha -= 0.03;
            }

            draw() {
                ctx.save();
                ctx.globalAlpha = Math.max(0, this.alpha);
                ctx.fillStyle = this.color;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
            }
        }

        class FallingItem {
            constructor(x, y, type) {
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
                this.hasTouchedRope = false; // 한 번이라도 로프에 닿았는지 여부. 한 번 닿은 뒤로는
                                              // 수직으로 튕기거나 잠깐 떠도 상관없이, x좌표가 로프의
                                              // 좌우 범위(leftPinX ~ rightPinX) 안에 있는 한 계속
                                              // 카운트가 유지된다 (아래 판정 로직 참고)
            }

            update() {
                this.prevX = this.x;
                this.prevY = this.y;
                this.vy += currentItemGravity;
                this.x += this.vx;
                this.y += this.vy;
                this.vx *= 0.98;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                if (this.type === 'apple') ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
                else if (this.type === 'star') ctx.fillStyle = 'rgba(234, 179, 8, 0.2)';
                else ctx.fillStyle = 'rgba(31, 41, 55, 0.2)';
                ctx.fill();

                ctx.strokeStyle = this.type === 'apple' ? '#ef4444' : (this.type === 'star' ? '#eab308' : '#1f2937');
                ctx.lineWidth = 2;
                ctx.stroke();

                ctx.font = "18px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                let symbol = this.type === 'apple' ? '🍎' : (this.type === 'star' ? '⭐' : '💣');
                ctx.fillText(symbol, this.x, this.y);

                // 안착 타이머 게이지 (로프에 닿아있는 동안의 "연속" 유지 시간을 표시. 이탈하면 0으로 리셋됨)
                if (this.hasTouchedRope && (this.type === 'apple' || this.type === 'star')) {
                    let progress = Math.min(1.0, this.touchTimer / SUCCESS_STEPS);
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.radius + 5, -Math.PI / 2, (-Math.PI / 2) + (Math.PI * 2 * progress));
                    ctx.strokeStyle = this.type === 'apple' ? '#22c55e' : '#3b82f6';
                    ctx.lineWidth = 3.5;
                    ctx.stroke();
                }
            }
        }

        function initRope() {
            particles = [];
            constraints = [];
            let widthStep = (rightPinX - leftPinX) / (ropePoints - 1);

            for (let i = 0; i < ropePoints; i++) {
                let isLeftPin = (i === 0);
                let isRightPin = (i === ropePoints - 1);
                let x = leftPinX + i * widthStep;
                let y = pinsY;
                particles.push(new Particle(x, y, isLeftPin, isRightPin));
            }

            for (let i = 0; i < ropePoints - 1; i++) {
                constraints.push(new Constraint(particles[i], particles[i + 1], restLen));
            }
        }

        function createParticles(x, y, color, count = 15) {
            for (let i = 0; i < count; i++) {
                effects.push(new Sparkle(x, y, color));
            }
        }

        function resetGame() {
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
        }

        function updateUI() {
            document.getElementById('score').innerText = `SCORE: ${score}`;
            let hearts = "❤️".repeat(lives);
            document.getElementById('lives').innerText = hearts || "💀 GAME OVER";
        }

        // 두 선분(A: 아이템의 이전->현재 이동 경로, B: 로프 세그먼트) 사이의 최단 거리를 구하는
        // 표준 "closest points between two segments" 알고리즘 (Ericson, Real-Time Collision Detection).
        // 이걸로 "이번 프레임에 이동한 경로 전체"가 로프에 얼마나 가까워졌는지 검사하므로,
        // 한 스텝에 로프 두께보다 더 멀리 이동해서 그냥 통과해버리는 터널링을 방지할 수 있습니다.
        function closestDistBetweenSegments(p1, q1, p2, q2) {
            const EPS = 1e-9;
            let d1x = q1.x - p1.x, d1y = q1.y - p1.y; // 경로 세그먼트 방향
            let d2x = q2.x - p2.x, d2y = q2.y - p2.y; // 로프 세그먼트 방향
            let rx = p1.x - p2.x, ry = p1.y - p2.y;

            let a = d1x * d1x + d1y * d1y;
            let e = d2x * d2x + d2y * d2y;
            let f = d2x * rx + d2y * ry;

            let s, t;
            if (a <= EPS && e <= EPS) {
                s = 0; t = 0;
            } else if (a <= EPS) {
                s = 0;
                t = Math.max(0, Math.min(1, f / e));
            } else {
                let c = d1x * rx + d1y * ry;
                if (e <= EPS) {
                    t = 0;
                    s = Math.max(0, Math.min(1, -c / a));
                } else {
                    let b = d1x * d2x + d1y * d2y;
                    let denom = a * e - b * b;
                    s = denom !== 0 ? Math.max(0, Math.min(1, (b * f - c * e) / denom)) : 0;
                    t = (b * s + f) / e;
                    if (t < 0) {
                        t = 0;
                        s = Math.max(0, Math.min(1, -c / a));
                    } else if (t > 1) {
                        t = 1;
                        s = Math.max(0, Math.min(1, (b - c) / a));
                    }
                }
            }

            let c1x = p1.x + d1x * s, c1y = p1.y + d1y * s; // 경로 위 최근접점
            let c2x = p2.x + d2x * t, c2y = p2.y + d2y * t; // 로프 세그먼트 위 최근접점
            let dx = c1x - c2x, dy = c1y - c2y;
            return { dist: Math.hypot(dx, dy), t, dx, dy, c2x, c2y };
        }

        resetGame();

        function handleInput() {
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

            // 화면 경계 및 두 축이 겹치지 않도록 위치 제한 (경계에 부딪히면 관성 속도 제거)
            if (leftPinX < 30) { leftPinX = 30; leftPinVX = 0; }
            if (leftPinX > rightPinX - 60) { leftPinX = rightPinX - 60; leftPinVX = 0; }

            if (rightPinX > canvas.width - 30) { rightPinX = canvas.width - 30; rightPinVX = 0; }
            if (rightPinX < leftPinX + 60) { rightPinX = leftPinX + 60; rightPinVX = 0; }

            particles[0].x = leftPinX;
            particles[0].y = pinsY;
            particles[ropePoints - 1].x = rightPinX;
            particles[ropePoints - 1].y = pinsY;
        }

        // 물리/게임 로직 한 스텝 (항상 동일한 "가상 시간" 단위로 실행됨 -> 기기 성능과 무관)
        function step() {
            if (isGameOver) return;

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
            if (spawnCountdown <= 0) {
                spawnCountdown += currentSpawnInterval;
                let spawnX = 60 + Math.random() * (canvas.width - 120);
                let rand = Math.random();
                let appleChance = (1 - currentBombChance) * 0.75; // 사과:별 비율은 기존처럼 3:1 유지
                let type = rand < appleChance ? 'apple' : (rand < 1 - currentBombChance ? 'star' : 'bomb');
                fallingItems.push(new FallingItem(spawnX, -20, type));
            }

            // 2. 물리 연산
            particles.forEach(p => p.update());
            for (let i = 0; i < 8; i++) {
                constraints.forEach(c => c.resolve());
            }

            fallingItems.forEach(item => item.update());

            // 3. 로프와 원형 물체 충돌 처리 — 스윕(swept) + 다중 반복 보정
            // "이전 위치 -> 현재 위치" 경로와 로프 세그먼트의 최단 거리로 통과(터널링)를 잡아내는 것에 더해,
            // 사과가 로프 양쪽 세그먼트에 동시에 '끼는' 상황을 처리하기 위해 한 스텝에 여러 번 반복 보정한다.
            // 반복 없이 가장 가까운 세그먼트 한 쪽만 보정하면, 반대쪽 세그먼트가 계속 조여올 때
            // 아이템이 한쪽으로만 밀려나다가 다음 스텝에 이미 반대편 세그먼트를 지나쳐버릴 수 있다(터널링).
            const SQUEEZE_ITERATIONS = 4;

            fallingItems.forEach(item => {
                let pathStart = { x: item.prevX, y: item.prevY };
                let anyCollision = false;
                let lastBest = null;

                for (let iter = 0; iter < SQUEEZE_ITERATIONS; iter++) {
                    let best = null;
                    let pathEnd = { x: item.x, y: item.y };

                    for (let i = 0; i < particles.length - 1; i++) {
                        let ropeP1 = particles[i], ropeP2 = particles[i + 1];
                        let res = closestDistBetweenSegments(pathStart, pathEnd, ropeP1, ropeP2);

                        if (res.dist < item.radius + 3 && (!best || res.dist < best.dist)) {
                            let segDx = ropeP2.x - ropeP1.x, segDy = ropeP2.y - ropeP1.y;
                            let segLen = Math.hypot(segDx, segDy) || 1;
                            let tx = segDx / segLen; // 세그먼트 접선 방향(정규화)
                            let ty = segDy / segLen;
                            let nx = res.dist > 1e-6 ? res.dx / res.dist : 0; // 로프 접점 -> 경로 쪽 법선 방향
                            let ny = res.dist > 1e-6 ? res.dy / res.dist : -1;
                            best = { dist: res.dist, t: res.t, nx, ny, tx, ty, p1: ropeP1, p2: ropeP2, contactX: res.c2x, contactY: res.c2y };
                        }
                    }

                    if (!best) break; // 더 이상 겹치는 세그먼트가 없으면 수렴 완료

                    anyCollision = true;
                    lastBest = best;

                    // 통과해버린 위치가 아니라, 로프 접점에서 정확히 (radius+3)만큼 떨어진 지점으로 배치
                    item.x = best.contactX + best.nx * (item.radius + 3);
                    item.y = best.contactY + best.ny * (item.radius + 3);

                    // 접촉한 세그먼트도 살짝 눌리도록 반응 (각 반복마다 누적 적용)
                    if (!best.p1.isLeftPin && !best.p1.isRightPin) best.p1.y += 1.8 * (1 - best.t);
                    if (!best.p2.isLeftPin && !best.p2.isRightPin) best.p2.y += 1.8 * best.t;
                }

                if (anyCollision) {
                    item.vy = -item.vy * 0.2;
                    // 경사 방향(접선)을 따라 미끄러지는 힘: 로프가 기운 쪽으로만 슬라이드됨 (마지막으로 닿은 세그먼트 기준)
                    item.vx += lastBest.tx * lastBest.ty * 0.6;
                }

                item.isOnRope = anyCollision;
                if (item.isOnRope) item.hasTouchedRope = true;
            });

            // 4. 아이템 2초 안착 / 폭발 / 낙하 판정
            fallingItems = fallingItems.filter(item => {
                if (item.type === 'apple' || item.type === 'star') {
                    // 한 번이라도 로프에 닿았다면, 이후로는 위아래로 미세하게 튕기거나 로프 표면에서
                    // 살짝 떠 있어도 상관없이 계속 카운트가 진행된다. x좌표가 로프의 좌우 범위를
                    // (여유값 XRANGE_MARGIN만큼) 완전히 벗어났을 때만 카운트를 리셋한다.
                    if (item.hasTouchedRope) {
                        if (item.x < leftPinX - XRANGE_MARGIN || item.x > rightPinX + XRANGE_MARGIN) {
                            item.touchTimer = 0;
                        } else {
                            item.touchTimer++;
                            // SUCCESS_STEPS(2초) 유지 성공 시 점수 획득
                            if (item.touchTimer >= SUCCESS_STEPS) {
                                let color = item.type === 'apple' ? '#22c55e' : '#eab308';
                                createParticles(item.x, item.y, color, 20);
                                score += (item.type === 'apple' ? 15 : 35);
                                updateUI();
                                return false;
                            }
                        }
                    }
                } else if (item.type === 'bomb') {
                    if (item.isOnRope) {
                        createParticles(item.x, item.y, '#ef4444', 25);
                        lives--;
                        updateUI();
                        return false;
                    }
                }

                if (item.y > canvas.height + 30) {
                    if (item.type === 'apple' || item.type === 'star') {
                        lives--;
                        updateUI();
                    }
                    return false;
                }

                return true;
            });

            if (lives <= 0) isGameOver = true;
        }

        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 이펙트 파티클
            effects = effects.filter(e => {
                e.update();
                e.draw();
                return e.alpha > 0;
            });

            // 로프 그리기
            ctx.beginPath();
            ctx.strokeStyle = '#8b5cf6';
            ctx.lineWidth = 5;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.moveTo(particles[0].x, particles[0].y);
            for (let i = 1; i < particles.length; i++) {
                ctx.lineTo(particles[i].x, particles[i].y);
            }
            ctx.stroke();

            // 좌/우 축 (A/D & 화살표)
            ctx.fillStyle = '#3182ce';
            ctx.beginPath();
            ctx.arc(leftPinX, pinsY, 12, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.font = "bold 10px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("A/D", leftPinX, pinsY + 3);

            ctx.fillStyle = '#e53e3e';
            ctx.beginPath();
            ctx.arc(rightPinX, pinsY, 12, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.fillText("⬅️➡️", rightPinX, pinsY + 3);

            // 낙하 물체 그리기
            fallingItems.forEach(item => item.draw());

            // Game Over
            if (isGameOver) {
                ctx.font = "bold 36px sans-serif";
                ctx.fillStyle = "#e53e3e";
                ctx.textAlign = "center";
                ctx.fillText("GAME OVER", canvas.width / 2, 230);
                ctx.font = "18px sans-serif";
                ctx.fillStyle = "#4a5568";
                ctx.fillText("상단의 [게임 리셋] 버튼을 눌러 다시 시작하세요!", canvas.width / 2, 270);
            }
        }

        // ---- 고정 타임스텝 메인 루프 ----
        // requestAnimationFrame은 화면 주사율에 따라 초당 호출 횟수가 다르지만(60Hz/120Hz/144Hz 등),
        // 여기서는 실제 경과 시간을 누적(accumulator)해서 항상 STEP_MS(1/60초) 단위로만 물리 연산을 수행합니다.
        // 그래서 모니터 주사율이나 기기 성능과 무관하게 게임 속도가 항상 동일하게 유지됩니다.
        let lastTime = performance.now();
        let accumulator = 0;

        function loop(now) {
            let delta = now - lastTime;
            lastTime = now;

            // 탭 전환 등으로 delta가 비정상적으로 커지는 경우 대비 (스파이럴 오브 데스 방지)
            if (delta > STEP_MS * MAX_STEPS_PER_FRAME) {
                delta = STEP_MS * MAX_STEPS_PER_FRAME;
            }

            accumulator += delta;

            let steps = 0;
            while (accumulator >= STEP_MS && steps < MAX_STEPS_PER_FRAME) {
                step();
                accumulator -= STEP_MS;
                steps++;
            }

            draw();
            requestAnimationFrame(loop);
        }

        requestAnimationFrame(loop);
    </script>
</body>
</html>
"""

components.html(html_code, height=680)
