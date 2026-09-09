import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧺 Dual-Axis Cloth Catcher (두 손으로 잡는 천 게임)")
st.caption("💡 **조작법**: [좌측 축] `A` / `D` 키 | [우측 축] `⬅️` / `➡️` 화살표 키 | 천을 조율해 폭탄을 피하고 물건을 받아내세요!")

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

        const gravity = 0.25;
        const friction = 0.98;

        const cols = 20;
        const rows = 5;
        
        let leftPinX = 250;
        let rightPinX = 600;
        const pinsY = 320;
        const moveSpeed = 7;

        let particles = [];
        let constraints = [];
        let fallingItems = [];
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
                let vx = (this.x - this.oldx) * friction;
                let vy = (this.y - this.oldy) * friction;
                this.oldx = this.x;
                this.oldy = this.y;
                this.x += vx;
                this.y += vy + gravity;
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

        class FallingItem {
            constructor(x, y, type) {
                this.x = x;
                this.y = y;
                this.vy = 1.5 + Math.random() * 1.5;
                this.type = type; // 'apple', 'star', 'bomb'
                this.radius = 16;
                this.caught = false;
            }

            update() {
                this.y += this.vy;
            }

            draw() {
                ctx.font = "20px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                let symbol = this.type === 'apple' ? '🍎' : (this.type === 'star' ? '⭐' : '💣');
                ctx.fillText(symbol, this.x, this.y);
            }
        }

        function initCloth() {
            particles = [];
            constraints = [];
            let widthStep = (rightPinX - leftPinX) / (cols - 1);

            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    let isLeftPin = (r === 0 && c === 0);
                    let isRightPin = (r === 0 && c === cols - 1);
                    let x = leftPinX + c * widthStep;
                    let y = pinsY + r * 15;
                    particles.push(new Particle(x, y, isLeftPin, isRightPin));
                }
            }

            let restLen = 18;
            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    let idx = r * cols + c;
                    if (c < cols - 1) constraints.push(new Constraint(particles[idx], particles[idx + 1], restLen));
                    if (r < rows - 1) constraints.push(new Constraint(particles[idx], particles[idx + cols], restLen));
                }
            }
        }

        function resetGame() {
            leftPinX = 250;
            rightPinX = 600;
            fallingItems = [];
            score = 0;
            lives = 3;
            spawnTimer = 0;
            isGameOver = false;
            initCloth();
            updateUI();
        }

        function updateUI() {
            document.getElementById('score').innerText = `SCORE: ${score}`;
            let hearts = "❤️".repeat(lives);
            document.getElementById('lives').innerText = hearts || "💀 GAME OVER";
        }

        resetGame();

        function handleInput() {
            // 좌측 축 조작 (A / D)
            if (keys['a'] || keys['A']) leftPinX = Math.max(30, leftPinX - moveSpeed);
            if (keys['d'] || keys['D']) leftPinX = Math.min(rightPinX - 60, leftPinX + moveSpeed);

            // 우측 축 조작 (화살표 ⬅️ / ➡️)
            if (keys['ArrowLeft']) rightPinX = Math.max(leftPinX + 60, rightPinX - moveSpeed);
            if (keys['ArrowRight']) rightPinX = Math.min(canvas.width - 30, rightPinX + moveSpeed);

            // 핀 위치 연동
            particles[0].x = leftPinX;
            particles[0].y = pinsY;
            particles[cols - 1].x = rightPinX;
            particles[cols - 1].y = pinsY;
        }

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (!isGameOver) {
                handleInput();

                // 1. 아이템 생성
                spawnTimer++;
                if (spawnTimer % 65 === 0) {
                    let spawnX = 80 + Math.random() * (canvas.width - 160);
                    let rand = Math.random();
                    let type = rand < 0.6 ? 'apple' : (rand < 0.8 ? 'star' : 'bomb');
                    fallingItems.push(new FallingItem(spawnX, -20, type));
                }

                // 2. 물리 업데이트
                particles.forEach(p => p.update());
                for (let i = 0; i < 5; i++) {
                    constraints.forEach(c => c.resolve());
                }

                fallingItems.forEach(item => item.update());

                // 3. 천-아이템 충돌 및 수거 처리
                fallingItems = fallingItems.filter(item => {
                    let caughtByCloth = false;

                    particles.forEach(p => {
                        let dx = p.x - item.x;
                        let dy = p.y - item.y;
                        let dist = Math.hypot(dx, dy);

                        if (dist < item.radius + 10) {
                            caughtByCloth = true;
                            if (!p.isLeftPin && !p.isRightPin) {
                                p.y += 12; // 천이 우묵하게 눌리는 효과
                            }
                        }
                    });

                    if (caughtByCloth) {
                        if (item.type === 'apple') score += 10;
                        else if (item.type === 'star') score += 25;
                        else if (item.type === 'bomb') lives--;

                        updateUI();
                        return false; // 수거 완료되어 화면에서 삭제
                    }

                    // 바닥 낙하 처리
                    if (item.y > canvas.height + 20) {
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

            // 4. 시각 가이드 및 천 그리기
            ctx.beginPath();
            ctx.strokeStyle = '#2d3748';
            ctx.lineWidth = 2;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            // 축 표시 (핸들)
            ctx.fillStyle = '#3182ce';
            ctx.beginPath();
            ctx.arc(leftPinX, pinsY, 10, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.font = "bold 10px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("A/D", leftPinX, pinsY + 3);

            ctx.fillStyle = '#e53e3e';
            ctx.beginPath();
            ctx.arc(rightPinX, pinsY, 10, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.fillText("⬅️➡️", rightPinX, pinsY + 3);

            // 5. 떨어지는 아이템 그리기
            fallingItems.forEach(item => item.draw());

            // Game Over 연출
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
