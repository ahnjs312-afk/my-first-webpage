import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🛡️ 천 그물망 디펜스 (Cloth Net Defense)")
st.caption("💡 **좌클릭 드래그**: 천을 당겨 물체 튕기기 | ✂️ **우클릭 드래그**: 천 잘라 폭탄 통과시키기 | 📥 **목표**: 물체를 양쪽 수거함에 넣으세요!")

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
            gap: 20px;
            align-items: center;
            margin-bottom: 10px;
        }
        .score-board {
            font-size: 18px;
            font-weight: bold;
            color: #1a202c;
        }
        .btn {
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s;
        }
        .btn-reset { background-color: #ff3b30; color: white; }
        .btn-reset:hover { background-color: #e02d22; }
        .btn-repair { background-color: #34c759; color: white; }
        .btn-repair:hover { background-color: #28a745; }
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
        <button class="btn btn-repair" onclick="repairCloth()">🔧 천 복구 (50점 소모)</button>
        <button class="btn btn-reset" onclick="resetGame()">🔄 게임 리셋</button>
    </div>
    <canvas id="canvas" width="850" height="580"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const gravity = 0.22;
        const friction = 0.985;

        // 천 구성 상수 (양끝 상단 고정)
        const cols = 26;
        const rows = 10;
        const spacing = 19;
        const startX = 180;
        const startY = 160;

        let particles = [];
        let constraints = [];
        let fallingObjects = [];
        let explosions = [];
        let draggedParticle = null;
        let isRightClicking = false;
        let score = 0;
        let spawnTimer = 0;

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
                this.active = true;
            }

            resolve() {
                if (!this.active) return;
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
            constructor(x, y, type) {
                this.x = x;
                this.y = y;
                this.oldx = x - (Math.random() - 0.5) * 2;
                this.oldy = y - Math.random() * 2;
                this.type = type; // 'ball', 'gem', 'bomb'
                this.radius = type === 'gem' ? 14 : (type === 'bomb' ? 18 : 16);
                this.exploded = false;
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
                if (this.type === 'ball') {
                    ctx.fillStyle = '#3182ce';
                } else if (this.type === 'gem') {
                    ctx.fillStyle = '#805ad5';
                } else if (this.type === 'bomb') {
                    ctx.fillStyle = '#e53e3e';
                }
                ctx.fill();
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
                ctx.stroke();

                // 아이콘 표시
                ctx.font = "12px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                let symbol = this.type === 'ball' ? '⚪' : (this.type === 'gem' ? '💎' : '💣');
                ctx.fillText(symbol, this.x, this.y);
            }
        }

        function resetGame() {
            particles = [];
            constraints = [];
            fallingObjects = [];
            explosions = [];
            draggedParticle = null;
            score = 0;
            spawnTimer = 0;
            document.getElementById('score').innerText = "SCORE: 0";

            // 양쪽 끝 위쪽 입자 고정
            for (let r = 0; r < rows; r++) {
                for (let c = 0; c < cols; c++) {
                    let pinned = (r === 0 && (c < 3 || c >= cols - 3));
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

        function repairCloth() {
            if (score >= 50) {
                let repaired = 0;
                for (let c of constraints) {
                    if (!c.active) {
                        c.active = true;
                        repaired++;
                        if (repaired >= 12) break; // 한 번에 최대 12개 실 복구
                    }
                }
                if (repaired > 0) {
                    score -= 50;
                    document.getElementById('score').innerText = `SCORE: ${score}`;
                }
            }
        }

        function explodeBomb(bomb) {
            bomb.exploded = true;
            const blastRadius = 65;

            // 주변 천 끊어내기
            constraints.forEach(c => {
                if (c.active) {
                    let d1 = Math.hypot(c.p1.x - bomb.x, c.p1.y - bomb.y);
                    let d2 = Math.hypot(c.p2.x - bomb.x, c.p2.y - bomb.y);
                    if (d1 < blastRadius || d2 < blastRadius) {
                        c.active = false;
                    }
                }
            });

            explosions.push({ x: bomb.x, y: bomb.y, radius: 5, maxRadius: 50, alpha: 1 });
        }

        function distToSegment(p, v, w) {
            let l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
            if (l2 === 0) return Math.hypot(p.x - v.x, p.y - v.y);
            let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
            t = Math.max(0, Math.min(1, t));
            return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
        }

        canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        let mouse = { x: -100, y: -100, isHover: false };

        canvas.addEventListener('mouseenter', () => { mouse.isHover = true; });
        canvas.addEventListener('mouseleave', () => { mouse.isHover = false; draggedParticle = null; isRightClicking = false; });

        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

            if (e.button === 0) {
                let minDist = 35;
                particles.forEach(p => {
                    let d = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                    if (d < minDist) {
                        minDist = d;
                        draggedParticle = p;
                    }
                });
            } else if (e.button === 2) {
                isRightClicking = true;
                cutCloth();
            }
        });

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

            if (draggedParticle) {
                draggedParticle.x = mouse.x;
                draggedParticle.y = mouse.y;
            }

            if (isRightClicking) {
                cutCloth();
            }
        });

        window.addEventListener('mouseup', (e) => {
            if (e.button === 0) draggedParticle = null;
            if (e.button === 2) isRightClicking = false;
        });

        function cutCloth() {
            const cutRadius = 12;
            constraints.forEach(c => {
                if (c.active && distToSegment(mouse, c.p1, c.p2) < cutRadius) {
                    c.active = false;
                }
            });
        }

        resetGame();

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 1. 물체 생성 (시간이 지나면 간격 단축)
            spawnTimer++;
            let spawnInterval = Math.max(40, 110 - Math.floor(score / 50) * 8);
            if (spawnTimer % spawnInterval === 0) {
                let spawnX = startX + 40 + Math.random() * (cols * spacing - 80);
                let rand = Math.random();
                let type = rand < 0.65 ? 'ball' : (rand < 0.85 ? 'gem' : 'bomb');
                fallingObjects.push(new FallingObject(spawnX, -20, type));
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

            // 3. 천-낙하 물체 충돌 처리
            fallingObjects.forEach(obj => {
                if (obj.exploded) return;

                particles.forEach(p => {
                    let dx = p.x - obj.x;
                    let dy = p.y - obj.y;
                    let dist = Math.hypot(dx, dy);
                    let minDist = obj.radius + 6;

                    if (dist < minDist && dist > 0) {
                        if (obj.type === 'bomb') {
                            explodeBomb(obj);
                            return;
                        }

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

            // 4. 수거함(Score Zone) 검사 & 처리
            fallingObjects = fallingObjects.filter(obj => {
                if (obj.exploded) return false;

                // 좌측 수거함 (x: 0~140, y: 460~580) | 우측 수거함 (x: 710~850, y: 460~580)
                let inLeftZone = (obj.x < 140 && obj.y > 460);
                let inRightZone = (obj.x > 710 && obj.y > 460);

                if (inLeftZone || inRightZone) {
                    if (obj.type === 'ball') score += 10;
                    else if (obj.type === 'gem') score += 30;
                    else if (obj.type === 'bomb') score = Math.max(0, score - 20);

                    document.getElementById('score').innerText = `SCORE: ${score}`;
                    return false;
                }

                // 바닥으로 완전히 떨어진 경우 삭제
                return obj.y < canvas.height + 30;
            });

            // 5. 그리기 - 수거함 구역
            ctx.fillStyle = 'rgba(66, 153, 225, 0.15)';
            ctx.fillRect(0, 460, 140, 120);
            ctx.fillRect(710, 460, 140, 120);
            
            ctx.lineWidth = 2;
            ctx.strokeStyle = '#3182ce';
            ctx.strokeRect(0, 460, 140, 120);
            ctx.strokeRect(710, 460, 140, 120);

            ctx.font = "bold 15px sans-serif";
            ctx.fillStyle = "#2b6cb0";
            ctx.textAlign = "center";
            ctx.fillText("📥 수거함", 70, 520);
            ctx.fillText("📥 수거함", 780, 520);

            // 6. 그리기 - 천
            ctx.beginPath();
            ctx.strokeStyle = '#1a1a1a';
            ctx.lineWidth = 1.8;
            constraints.forEach(c => {
                if (c.active) {
                    ctx.moveTo(c.p1.x, c.p1.y);
                    ctx.lineTo(c.p2.x, c.p2.y);
                }
            });
            ctx.stroke();

            // 고정점
            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
                    ctx.fillStyle = '#4a5568';
                    ctx.fill();
                }
            });

            // 7. 그리기 - 낙하 물체
            fallingObjects.forEach(obj => obj.draw());

            // 8. 그리기 - 폭발 이펙트
            explosions.forEach(exp => {
                ctx.beginPath();
                ctx.arc(exp.x, exp.y, exp.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(229, 62, 62, ${exp.alpha})`;
                ctx.fill();
                exp.radius += 3;
                exp.alpha -= 0.05;
            });
            explosions = explosions.filter(exp => exp.alpha > 0);

            // 9. 커서 표시
            if (mouse.isHover) {
                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, isRightClicking ? 12 : (draggedParticle ? 8 : 6), 0, Math.PI * 2);
                ctx.fillStyle = isRightClicking ? 'rgba(255, 59, 48, 0.2)' : (draggedParticle ? '#ff2d55' : 'rgba(255, 45, 85, 0.7)');
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
