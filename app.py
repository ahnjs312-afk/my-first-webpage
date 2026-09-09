import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🪢 Rope Balance Catcher (1초 안착 물리 캐치 게임)")
st.caption("💡 **조작법**: [좌측 축] `A` / `D` | [우측 축] `⬅️` / `➡️` | 사과를 로프 위에 1초 동안 안전하게 얹어 점수를 얻으세요! (먼저 게임 화면을 한 번 클릭해주세요)")

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

        const ropeGravity = 0.25;
        const ropeFriction = 0.985;
        const itemGravity = 0.09; // 물체에 적용할 약한 중력

        const ropePoints = 22;
        const restLen = 17;
        const maxSpan = restLen * (ropePoints - 1) * 0.92; // 로프가 팽팽하게 일직선이 되지 않도록 최대 간격 제한

        let leftPinX = 250;
        let rightPinX = 600;
        const pinsY = 320;
        const moveSpeed = 8;

        let particles = [];
        let constraints = [];
        let fallingItems = [];
        let effects = [];
        let score = 0;
        let lives = 3;
        let spawnTimer = 0;
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
                this.vx = 0; // 가로 쏠림 방지 (직하강)
                this.vy = 0; 
                this.type = type; // 'apple', 'star', 'bomb'
                this.radius = type === 'star' ? 15 : 18;
                this.touchTimer = 0; // 60프레임 = 1초
                this.isOnRope = false;
            }

            update() {
                this.vy += itemGravity;
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

                // 1초(60프레임) 안착 타이머 게이지
                if (this.isOnRope && (this.type === 'apple' || this.type === 'star')) {
                    let progress = Math.min(1.0, this.touchTimer / 60);
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
            fallingItems = [];
            effects = [];
            score = 0;
            lives = 3;
            spawnTimer = 0;
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

        function checkSegmentCircleCollision(p1, p2, circle) {
            let dx = p2.x - p1.x;
            let dy = p2.y - p1.y;
            let lenSq = dx * dx + dy * dy;
            if (lenSq === 0) return null;

            let t = Math.max(0, Math.min(1, ((circle.x - p1.x) * dx + (circle.y - p1.y) * dy) / lenSq));
            let projX = p1.x + t * dx;
            let projY = p1.y + t * dy;

            let distX = circle.x - projX;
            let distY = circle.y - projY;
            let dist = Math.hypot(distX, distY);

            if (dist < circle.radius + 3) {
                let nx = dist === 0 ? 0 : distX / dist;
                let ny = dist === 0 ? -1 : distY / dist;
                let segLen = Math.hypot(dx, dy) || 1;
                let tx = dx / segLen; // 세그먼트 접선 방향(정규화)
                let ty = dy / segLen;
                return { dist, nx, ny, tx, ty, projX, projY, t, p1, p2 };
            }
            return null;
        }

        resetGame();

        function handleInput() {
            if (keys['a'] || keys['A']) leftPinX = Math.max(30, leftPinX - moveSpeed);
            if (keys['d'] || keys['D']) leftPinX = Math.min(rightPinX - 60, leftPinX + moveSpeed);

            if (keys['ArrowLeft']) rightPinX = Math.max(leftPinX + 60, rightPinX - moveSpeed);
            if (keys['ArrowRight']) rightPinX = Math.min(canvas.width - 30, rightPinX + moveSpeed);

            // 로프가 완전히 팽팽해져 뻣뻣하게 일직선이 되지 않도록 최대 간격 제한
            if (rightPinX - leftPinX > maxSpan) {
                let mid = (rightPinX + leftPinX) / 2;
                leftPinX = mid - maxSpan / 2;
                rightPinX = mid + maxSpan / 2;
            }

            particles[0].x = leftPinX;
            particles[0].y = pinsY;
            particles[ropePoints - 1].x = rightPinX;
            particles[ropePoints - 1].y = pinsY;
        }

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (!isGameOver) {
                handleInput();

                // 1. 물체 생성 (화면 전역에서 좌우 쏠림 없이 대칭으로 스폰)
                spawnTimer++;
                if (spawnTimer % 75 === 0) {
                    let spawnX = 60 + Math.random() * (canvas.width - 120);
                    let rand = Math.random();
                    let type = rand < 0.6 ? 'apple' : (rand < 0.8 ? 'star' : 'bomb');
                    fallingItems.push(new FallingItem(spawnX, -20, type));
                }

                // 2. 물리 연산
                particles.forEach(p => p.update());
                for (let i = 0; i < 8; i++) {
                    constraints.forEach(c => c.resolve());
                }

                fallingItems.forEach(item => item.update());

                // 3. 로프와 원형 물체 충돌 처리 (프레임당 가장 가까운 세그먼트 하나만 적용 -> 중복 보정/떨림 방지)
                fallingItems.forEach(item => {
                    let best = null;

                    for (let i = 0; i < particles.length - 1; i++) {
                        let col = checkSegmentCircleCollision(particles[i], particles[i + 1], item);
                        if (col && (!best || col.dist < best.dist)) {
                            best = col;
                        }
                    }

                    if (best) {
                        let overlap = (item.radius + 3) - best.dist;
                        item.x += best.nx * overlap;
                        item.y += best.ny * overlap;
                        item.vy = -item.vy * 0.2;

                        // 경사 방향(접선)을 따라 미끄러지는 힘: 로프가 기운 쪽으로만 슬라이드됨
                        item.vx += best.tx * best.ty * 0.6;

                        if (!best.p1.isLeftPin && !best.p1.isRightPin) best.p1.y += 1.8 * (1 - best.t);
                        if (!best.p2.isLeftPin && !best.p2.isRightPin) best.p2.y += 1.8 * best.t;
                    }

                    item.isOnRope = !!best;
                });

                // 4. 아이템 1초 안착 / 폭발 / 낙하 판정
                fallingItems = fallingItems.filter(item => {
                    if (item.type === 'apple' || item.type === 'star') {
                        if (item.isOnRope) {
                            item.touchTimer++;
                            // 1초 (60프레임) 유지 성공 시 점수 획득
                            if (item.touchTimer >= 60) {
                                let color = item.type === 'apple' ? '#22c55e' : '#eab308';
                                createParticles(item.x, item.y, color, 20);
                                score += (item.type === 'apple' ? 15 : 35);
                                updateUI();
                                return false;
                            }
                        } else {
                            item.touchTimer = Math.max(0, item.touchTimer - 2);
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

            // 5. 이펙트 파티클
            effects = effects.filter(e => {
                e.update();
                e.draw();
                return e.alpha > 0;
            });

            // 6. 로프 그리기
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

            // 7. 좌/우 축 (A/D & 화살표)
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

            // 8. 낙하 물체 그리기
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

            requestAnimationFrame(loop);
        }

        loop();
    </script>
</body>
</html>
"""

components.html(html_code, height=680)
