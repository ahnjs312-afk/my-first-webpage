import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧵 천 베기 (Cloth Ninja)")
st.caption("💡 마우스 드래그로 튀어 오르는 천을 베어내세요! 천을 자를 때마다 점수가 올라갑니다.")

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
            font-size: 20px;
            font-weight: bold;
            color: #1a202c;
        }
        button {
            background-color: #ff3b30;
            color: white;
            border: none;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 6px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        button:hover { background-color: #e02d22; }
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
        <button onclick="resetGame()">🔄 다시 하기 (Reset)</button>
    </div>
    <canvas id="canvas" width="850" height="580"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const gravity = 0.18;
        const friction = 0.99;

        let score = 0;
        let cloths = [];
        let mouseTrail = []; // 검기 궤적 저장
        let isMouseDown = false;

        class Particle {
            constructor(x, y) {
                this.x = x;
                this.y = y;
                this.oldx = x;
                this.oldy = y;
            }

            update() {
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
                
                this.p1.x -= dx * diff;
                this.p1.y -= dy * diff;
                this.p2.x += dx * diff;
                this.p2.y += dy * diff;
            }
        }

        class Cloth {
            constructor(x, y, cols = 6, rows = 6, spacing = 15) {
                this.particles = [];
                this.constraints = [];
                this.cols = cols;
                this.rows = rows;

                // 천 입자 생성
                for (let r = 0; r < rows; r++) {
                    for (let c = 0; c < cols; c++) {
                        this.particles.push(new Particle(x + c * spacing, y + r * spacing));
                    }
                }

                // 솟구쳐 오르는 속도 부여 (임의 분사)
                let vx = (Math.random() - 0.5) * 8;
                let vy = -(11 + Math.random() * 5);

                this.particles.forEach(p => {
                    p.oldx = p.x - vx;
                    p.oldy = p.y - vy;
                });

                // 제약 조건 연결
                for (let r = 0; r < rows; r++) {
                    for (let c = 0; c < cols; c++) {
                        let idx = r * cols + c;
                        if (c < cols - 1) this.constraints.push(new Constraint(this.particles[idx], this.particles[idx + 1]));
                        if (r < rows - 1) this.constraints.push(new Constraint(this.particles[idx], this.particles[idx + cols]));
                    }
                }
            }

            update() {
                this.particles.forEach(p => p.update());
                for (let i = 0; i < 3; i++) {
                    this.constraints.forEach(c => c.resolve());
                }
            }

            draw() {
                ctx.beginPath();
                ctx.strokeStyle = '#1a1a1a';
                ctx.lineWidth = 1.8;
                this.constraints.forEach(c => {
                    if (c.active) {
                        ctx.moveTo(c.p1.x, c.p1.y);
                        ctx.lineTo(c.p2.x, c.p2.y);
                    }
                });
                ctx.stroke();
            }

            // 화면 밖으로 완전히 사라졌는지 확인
            isOutOfBounds() {
                return this.particles.every(p => p.y > canvas.height + 50);
            }
        }

        // 선분 교차 검사 (자르기 판정)
        function distToSegment(p, v, w) {
            let l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
            if (l2 === 0) return Math.hypot(p.x - v.x, p.y - v.y);
            let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
            t = Math.max(0, Math.min(1, t));
            return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
        }

        // 천 스폰 타이머
        let spawnTimer = 0;

        function resetGame() {
            score = 0;
            cloths = [];
            mouseTrail = [];
            document.getElementById('score').innerText = "SCORE: 0";
        }

        let mouse = { x: -100, y: -100 };

        canvas.addEventListener('mousedown', (e) => { isMouseDown = true; });
        canvas.addEventListener('mouseup', () => { isMouseDown = false; });
        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

            mouseTrail.push({ x: mouse.x, y: mouse.y, life: 10 });
            if (isMouseDown || mouseTrail.length > 1) {
                cutCloths();
            }
        });

        // 천 자르기 처리
        function cutCloths() {
            cloths.forEach(cloth => {
                cloth.constraints.forEach(c => {
                    if (c.active) {
                        let d = distToSegment(mouse, c.p1, c.p2);
                        if (d < 12) {
                            c.active = false;
                            score += 10;
                            document.getElementById('score').innerText = `SCORE: ${score}`;
                        }
                    }
                });
            });
        }

        resetGame();

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 주기적으로 천 스폰
            spawnTimer++;
            if (spawnTimer % 70 === 0) {
                let spawnX = 150 + Math.random() * (canvas.width - 300);
                cloths.push(new Cloth(spawnX, canvas.height + 20, 6, 6, 16));
            }

            // 천 업데이트 & 그리기
            cloths.forEach(cloth => {
                cloth.update();
                cloth.draw();
            });

            // 화면 밖으로 떨어진 천 제거
            cloths = cloths.filter(cloth => !cloth.isOutOfBounds());

            // 마우스 궤적(검기) 그리기
            ctx.beginPath();
            if (mouseTrail.length > 0) {
                ctx.moveTo(mouseTrail[0].x, mouseTrail[0].y);
                for (let i = 1; i < mouseTrail.length; i++) {
                    ctx.lineTo(mouseTrail[i].x, mouseTrail[i].y);
                }
            }
            ctx.strokeStyle = '#ff2d55';
            ctx.lineWidth = 3;
            ctx.stroke();

            // 궤적 수명 감소
            mouseTrail.forEach(t => t.life--);
            mouseTrail = mouseTrail.filter(t => t.life > 0);

            requestAnimationFrame(loop);
        }

        loop();
    </script>
</body>
</html>
"""

components.html(html_code, height=640)
