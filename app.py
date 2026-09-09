import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🪢 Rope Balance Catcher (2초 안착 물리 캐치 게임)")
st.caption("💡 **조작법**: [좌측 축] `A` / `D` | [우측 축] `⬅️` / `➡️` | 사과를 로프 위에 2초 동안 안전하게 얹어 점수를 얻으세요!")

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
        }
    </style>
</head>
<body>
    <div class="ui-panel">
        <div class="score-board" id="score">SCORE: 0</div>
        <div class="life-board" id="lives">❤️❤️❤️</div>
        <button onclick="resetGame()">🔄 게임 리셋</button>
    </div>
    <canvas id="canvas" width="850" height="580"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const ropeGravity = 0.25;
        const ropeFriction = 0.985;
        const itemGravity = 0.09; // 물체에 적용할 약한 중력

        const ropePoints = 22;
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

        window.addEventListener('keydown', e => { keys[e.key] = true; });
        window.addEventListener('keyup', e => { keys[e.key] = false; });

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

        // 파티클 이펙트
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
                this.vx = (Math.random() - 0.5) * 1.2;
                this.vy = 0; // 초기 약한 속도
                this.type = type; // 'apple', 'star', 'bomb'
                this.radius = type === 'star' ? 15 : 18;
                this.touchTimer = 0; // 로프 위 안착 프레임 타이머 (120프레임 = 2초)
                this.isOnRope = false;
            }

            update() {
                // 약한 중력 적용
                this.vy += itemGravity;
                this.x += this.vx;
                this.y += this.vy;
                this.vx *= 0.98; // 공기 저항
            }

            draw() {
                // 원형 물리 바디 그리기
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                if (this.type === 'apple') ctx.fillStyle = 'rgba(239, 68, 68, 0.2)';
                else if (this.type === 'star') ctx.fillStyle = 'rgba(234, 179, 8, 0.2)';
                else ctx.fillStyle = 'rgba(31, 41, 55, 0.2)';
                ctx.fill();

                ctx.strokeStyle = this.type === 'apple' ? '#ef4444' : (this.type === 'star' ? '#eab308' : '#1f2937');
                ctx.lineWidth = 2;
                ctx.stroke();

                // 이모지 심볼
                ctx.font = "18px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                let symbol = this.type === 'apple' ? '🍎' : (this.type === 'star' ? '⭐' : '💣');
                ctx.fillText(symbol, this.x, this.y);

                // 2초 안착 타이머 게이지 (프로그레스 링)
                if (this.isOnRope && (this.type === 'apple' || this.type === 'star')) {
                    let progress = Math.min(1.0, this.touchTimer / 120);
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

            let restLen = 17;
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
        }

        function updateUI() {
            document.getElementById('score').innerText = `SCORE: ${score}`;
            let hearts = "❤️".repeat(lives);
            document.getElementById('lives').innerText = hearts || "💀 GAME OVER";
        }

        // 선분과 원 충돌 판정 계산 함수
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
                return { dist, nx, ny, projX, projY, t };
            }
            return null;
        }

        resetGame();

        function handleInput() {
            if (keys['a'] || keys['A']) leftPinX = Math.max(30, leftPinX - moveSpeed);
            if (keys['d'] || keys['D']) leftPinX = Math.min(rightPinX - 60, leftPinX + moveSpeed);

            if (keys['ArrowLeft']) rightPinX = Math.max(leftPinX + 60, rightPinX - moveSpeed);
            if (keys['ArrowRight']) rightPinX = Math.min(canvas.width - 30, rightPinX + moveSpeed);

            particles[0].x = leftPinX;
            particles[0].y = pinsY;
            particles[ropePoints - 1].x = rightPinX;
            particles[ropePoints - 1].y = pinsY;
        }

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (!isGameOver) {
                handleInput();

                // 1. 물체 생성
                spawnTimer++;
                if (spawnTimer % 80 === 0) {
                    let spawnX = 100 + Math.random() * (canvas.width - 200);
                    let rand = Math.random();
                    let type = rand < 0.6 ? 'apple' : (rand < 0.8 ? 'star' : 'bomb');
                    fallingItems.push(new FallingItem(spawnX, -20, type));
                }

                // 2. 물리 연산 (로프 & 물체)
                particles.forEach(p => p.update());
                for (let i = 0; i < 8; i++) {
                    constraints.forEach(c => c.resolve());
                }

                fallingItems.forEach(item => item.update());

                // 3. 로프와 원형 물체 충돌 및 안착 처리
                fallingItems.forEach(item => {
                    let touching = false;

                    for (let i = 0; i < particles.length - 1; i++) {
                        let p1 = particles[i];
                        let p2 = particles[i + 1];

                        let col = checkSegmentCircleCollision(p1, p2, item);
                        if (col) {
                            touching = true;
                            let overlap = (item.radius + 3) - col.dist;

                            // 물체 밀어내기 및 반발력 적용
                            item.x += col.nx * overlap;
                            item.y += col.ny * overlap;
                            item.vy = -item.vy * 0.2; // 충격 완화
                            item.vx += (p2.x - p1.x) * 0.02;

                            // 로프를 눌러 처지게 만듦
                            if (!p1.isLeftPin && !p1.isRightPin) p1.y += 1.8 * (1 - col.t);
                            if (!p2.isLeftPin && !p2.isRightPin) p2.y += 1.8 * col.t;
                        }
                    }

                    item.isOnRope = touching;
                });

                // 4. 아이템 2초안착 / 폭발 / 낙하 판정
                fallingItems = fallingItems.filter(item => {
                    if (item.type === 'apple' || item.type === 'star') {
                        if (item.isOnRope) {
                            item.touchTimer++;
                            // 2초 (120프레임) 유지 성공 시 점수 획득
                            if (item.touchTimer >= 120) {
                                let color = item.type === 'apple' ? '#22c55e' : '#eab308';
                                createParticles(item.x, item.y, color, 20);
                                score += (item.type === 'apple' ? 15 : 35);
                                updateUI();
                                return false; // 성공하여 삭제
                            }
                        } else {
                            // 로프에서 이탈하면 게이지 감소
                            item.touchTimer = Math.max(0, item.touchTimer - 2);
                        }
                    } else if (item.type === 'bomb') {
                        if (item.isOnRope) {
                            // 폭탄이 로프에 닿으면 즉시 폭발!
                            createParticles(item.x, item.y, '#ef4444', 25);
                            lives--;
                            updateUI();
                            return false; // 삭제
                        }
                    }

                    // 화면 바닥 낙하 판정
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

            // 5. 파티클 이펙트 업데이트 & 그리기
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

            // 7. 좌/우 조작 핸들
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

            // 8. 떨어지는 물체 그리기
            fallingItems.forEach(item => item.draw());

            // Game Over 문구
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

components.html(html_code, height=640)
