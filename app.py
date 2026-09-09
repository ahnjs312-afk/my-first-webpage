import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧺 천 그물망 공 분류 게임 (Collision & Timing Fixed)")
st.caption("💡 **개선 사항**: 공끼리 부딪히는 물리 충돌 적용 / 다른 색상 공 간 최소 시차 간격 보장!")

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
            cursor: none; 
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

        const gravity = 0.22;
        const friction = 0.985;

        const cols = 26;
        const rows = 6; 
        const spacing = 19;
        const startX = 180;
        const startY = 180;

        let particles = [];
        let constraints = [];
        let fallingObjects = [];
        let draggedParticle = null;
        let score = 0;
        let lives = 3;
        let spawnTimer = 0;
        let lastColorType = null;
        let colorCooldowntimer = 0;
        let isGameOver = false;

        class Particle {
            constructor(x, y, pinned = false) {
                this.x = x;
                this.y = y;
                this.oldx = x;
                this.oldy = y;
                this.pinned = pinned;
            }

            update() {
                if (this.pinned) return;
                let vx = (this.x - this.oldx) * friction;
                let vy = (this.y - this.oldy) * friction;
                this.oldx = this.x;
                this.oldy = this.y;
                this.x += vx;
                this.y += vy + gravity;
            }
        }

        class Constraint {
            constructor(p1, p2) {
                this.p1 = p1;
                this.p2 = p2;
                this.length = Math.hypot(p1.x - p2.x, p1.y - p2.y);
            }

            resolve() {
                let dx = this.p2.x - this.p1.x;
                let dy = this.p2.y - this.p1.y;
                let dist = Math.hypot(dx, dy);
                if (dist === 0) return;
                let diff = (this.length - dist) / dist * 0.5;
                
                if (!this.p1.pinned) {
                    this.p1.x -= dx * diff;
                    this.p1.y -= dy * diff;
                }
                if (!this.p2.pinned) {
                    this.p2.x += dx * diff;
                    this.p2.y += dy * diff;
                }
            }
        }

        class FallingObject {
            constructor(x, y, colorType) {
                this.x = x;
                this.y = y;
                this.oldx = x - (Math.random() - 0.5) * 1.5;
                this.oldy = y - Math.random() * 2;
                this.colorType = colorType; // 'blue', 'red', 'gold'
                this.radius = colorType === 'gold' ? 14 : 16;
            }

            update() {
                let vx = (this.x - this.oldx) * 0.99;
                let vy = (this.y - this.oldy) * 0.99;
                this.oldx = this.x;
                this.oldy = this.y;
                this.x += vx;
                this.y += vy + gravity * 0.8;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                if (this.colorType === 'blue') ctx.fillStyle = '#3182ce';
                else if (this.colorType === 'red') ctx.fillStyle = '#e53e3e';
                else if (this.colorType === 'gold') ctx.fillStyle = '#ecc94b';
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                ctx.font = "12px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                let symbol = this.colorType === 'blue' ? '🔵' : (this.colorType === 'red' ? '🔴' : '⭐');
                ctx.fillText(symbol, this.x, this.y);
            }
        }

        function resetGame() {
            particles = [];
            constraints = [];
            fallingObjects = [];
            draggedParticle = null;
            score = 0;
            lives = 3;
            spawnTimer = 0;
            lastColorType = null;
            colorCooldowntimer = 0;
            isGameOver = false;
            updateUI();

            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    let pinned = (r === 0 && (c === 0 || c === cols - 1));
                    particles.push(new Particle(startX + c * spacing, startY + r * spacing, pinned));
                }
            }

            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    let idx = r * cols + c;
                    if (c < cols - 1) constraints.push(new Constraint(particles[idx], particles[idx + 1]));
                    if (r < rows - 1) constraints.push(new Constraint(particles[idx], particles[idx + cols]));
                }
            }
        }

        function updateUI() {
            document.getElementById('score').innerText = `SCORE: ${score}`;
            let hearts = "❤️".repeat(lives);
            document.getElementById('lives').innerText = hearts || "💀 GAME OVER";
        }

        let mouse = { x: -100, y: -100, isHover: false };

        canvas.addEventListener('mouseenter', () => { mouse.isHover = true; });
        canvas.addEventListener('mouseleave', () => { mouse.isHover = false; draggedParticle = null; });

        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

            let minDist = 35;
            particles.forEach(p => {
                let d = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                if (d < minDist) {
                    minDist = d;
                    draggedParticle = p;
                }
            });
        });

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

            if (draggedParticle) {
                draggedParticle.x = mouse.x;
                draggedParticle.y = mouse.y;
            }
        });

        window.addEventListener('mouseup', () => { draggedParticle = null; });

        resetGame();

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            if (!isGameOver) {
                // 1. [3번 구현] 물체 생성 및 반대 색상 시차 간격 제어
                spawnTimer++;
                colorCooldowntimer++;
                
                let baseSpawnInterval = Math.max(50, 110 - Math.floor(score / 40) * 8);
                if (spawnTimer % baseSpawnInterval === 0) {
                    let rand = Math.random();
                    let nextColor = rand < 0.45 ? 'blue' : (rand < 0.9 ? 'red' : 'gold');

                    // 이전 공과 다른 색상(파란색↔빨간색)이 연속 등장하면 딜레이(120프레임 약 2초) 보장
                    let isOpposite = (lastColorType === 'blue' && nextColor === 'red') || (lastColorType === 'red' && nextColor === 'blue');
                    
                    if (!isOpposite || colorCooldowntimer > 120) {
                        let spawnX = startX + 40 + Math.random() * (cols * spacing - 80);
                        fallingObjects.push(new FallingObject(spawnX, -20, nextColor));
                        lastColorType = nextColor;
                        colorCooldowntimer = 0;
                    }
                }

                // 2. 물리 업데이트
                particles.forEach(p => p.update());
                if (draggedParticle) {
                    draggedParticle.x = mouse.x;
                    draggedParticle.y = mouse.y;
                }

                for (let i = 0; i < 6; i++) {
                    constraints.forEach(c => c.resolve());
                }

                fallingObjects.forEach(obj => obj.update());

                // 3. 천-공 충돌 처리
                fallingObjects.forEach(obj => {
                    particles.forEach(p => {
                        let dx = p.x - obj.x;
                        let dy = p.y - obj.y;
                        let dist = Math.hypot(dx, dy);
                        let minDist = obj.radius + 6;

                        if (dist < minDist && dist > 0) {
                            let overlap = minDist - dist;
                            let nx = dx / dist;
                            let ny = dy / dist;

                            if (!p.pinned) {
                                p.x += nx * overlap * 0.65;
                                p.y += ny * overlap * 0.65;
                            }
                            obj.x -= nx * overlap * 0.35;
                            obj.y -= ny * overlap * 0.35;
                        }
                    });
                });

                // 4. [4번 구현] 공과 공 사이의 충돌 (Ball vs Ball Collision)
                for (let i = 0; i < fallingObjects.length; i++) {
                    for (let j = i + 1; j < fallingObjects.length; j++) {
                        let o1 = fallingObjects[i];
                        let o2 = fallingObjects[j];

                        let dx = o2.x - o1.x;
                        let dy = o2.y - o1.y;
                        let dist = Math.hypot(dx, dy);
                        let minDist = o1.radius + o2.radius;

                        if (dist < minDist && dist > 0) {
                            let overlap = (minDist - dist) / 2;
                            let nx = dx / dist;
                            let ny = dy / dist;

                            // 위치 겹침 해제
                            o1.x -= nx * overlap;
                            o1.y -= ny * overlap;
                            o2.x += nx * overlap;
                            o2.y += ny * overlap;

                            // 속도/반발력 교환 (밀쳐내기 효과)
                            let vx1 = o1.x - o1.oldx;
                            let vy1 = o1.y - o1.oldy;
                            let vx2 = o2.x - o2.oldx;
                            let vy2 = o2.y - o2.oldy;

                            let kx = vx1 - vx2;
                            let ky = vy1 - vy2;
                            let p = 2 * (nx * kx + ny * ky) / 2;

                            o1.oldx = o1.x - (vx1 - p * nx * 1.2);
                            o1.oldy = o1.y - (vy1 - p * ny * 1.2);
                            o2.oldx = o2.x - (vx2 + p * nx * 1.2);
                            o2.oldy = o2.y - (vy2 + p * ny * 1.2);
                        }
                    }
                }

                // 5. 화면 벽면 및 바닥 수거 판정
                fallingObjects = fallingObjects.filter(obj => {
                    let isBelowCloth = obj.y > 250;
                    let hitLeftWall = isBelowCloth && (obj.x - obj.radius <= 0);
                    let hitRightWall = isBelowCloth && (obj.x + obj.radius >= canvas.width);
                    let hitBottomFloor = obj.y + obj.radius >= canvas.height;

                    if (hitLeftWall || (hitBottomFloor && obj.x < canvas.width / 2)) {
                        if (obj.colorType === 'blue' || obj.colorType === 'gold') score += (obj.colorType === 'gold' ? 30 : 10);
                        else { lives--; }
                        updateUI();
                        return false;
                    }

                    if (hitRightWall || (hitBottomFloor && obj.x >= canvas.width / 2)) {
                        if (obj.colorType === 'red' || obj.colorType === 'gold') score += (obj.colorType === 'gold' ? 30 : 10);
                        else { lives--; }
                        updateUI();
                        return false;
                    }

                    return true;
                });

                if (lives <= 0) {
                    isGameOver = true;
                }
            }

            // 6. 시각적 영역 패널
            ctx.fillStyle = 'rgba(49, 130, 206, 0.06)';
            ctx.fillRect(0, 0, canvas.width / 2, canvas.height);
            ctx.fillStyle = 'rgba(229, 62, 62, 0.06)';
            ctx.fillRect(canvas.width / 2, 0, canvas.width / 2, canvas.height);

            ctx.beginPath();
            ctx.setLineDash([6, 6]);
            ctx.moveTo(canvas.width / 2, 350);
            ctx.lineTo(canvas.width / 2, canvas.height);
            ctx.strokeStyle = '#cbd5e0';
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.font = "bold 15px sans-serif";
            ctx.textAlign = "center";
            ctx.fillStyle = "#2b6cb0";
            ctx.fillText("🔵 좌측 영역 (벽 / 바닥)", canvas.width / 4, canvas.height - 15);
            ctx.fillStyle = "#c53030";
            ctx.fillText("🔴 우측 영역 (벽 / 바닥)", (canvas.width / 4) * 3, canvas.height - 15);

            // 7. 그리기 - 천 및 고정점
            ctx.beginPath();
            ctx.strokeStyle = '#1a1a1a';
            ctx.lineWidth = 1.8;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
                    ctx.fillStyle = '#2d3748';
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }
            });

            // 8. 공 그리기
            fallingObjects.forEach(obj => obj.draw());

            // Game Over 문구
            if (isGameOver) {
                ctx.font = "bold 36px sans-serif";
                ctx.fillStyle = "#e53e3e";
                ctx.textAlign = "center";
                ctx.fillText("GAME OVER", canvas.width / 2, 260);
                ctx.font = "18px sans-serif";
                ctx.fillStyle = "#4a5568";
                ctx.fillText("상단의 [게임 리셋] 버튼을 눌러 다시 도전하세요!", canvas.width / 2, 300);
            }

            // 9. 마우스 커서
            if (mouse.isHover) {
                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, draggedParticle ? 8 : 6, 0, Math.PI * 2);
                ctx.fillStyle = draggedParticle ? '#ff2d55' : 'rgba(255, 45, 85, 0.7)';
                ctx.strokeStyle = '#ff2d55';
                ctx.lineWidth = 1.5;
                ctx.fill();
                ctx.stroke();
            }

            requestAnimationFrame(loop);
        }

        loop();
    </script>
</body>
</html>
"""

components.html(html_code, height=640)
