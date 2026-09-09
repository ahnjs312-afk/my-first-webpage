import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧵 마우스 상호작용 가능한 천 시뮬레이션")
st.caption("마우스 왼쪽 클릭 및 드래그로 천을 잡아당겨 보세요!")

# HTML/JS 기반 베를레 적분 천 시뮬레이션 코드
html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; overflow: hidden; background-color: #f0f2f6; display: flex; justify-content: center; align-items: center; }
        canvas { background: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: grab; }
        canvas:active { cursor: grabbing; }
    </style>
</head>
<body>
    <canvas id="canvas" width="700" height="500"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const cols = 15;
        const rows = 12;
        const spacing = 20;
        const startX = 200;
        const startY = 50;
        const gravity = 0.2;
        const friction = 0.99;
        const bounce = 0.9;

        let particles = [];
        let constraints = [];
        let draggedParticle = null;

        class Particle {
            constructor(x, y, pinned = false) {
                self.x = x;
                self.y = y;
                self.oldx = x;
                self.oldy = y;
                self.pinned = pinned;
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

        // 초기화
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                let pinned = (r === 0 && (c === 0 || c === cols - 1 || c === Math.floor(cols/2)));
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

        // 마우스 이벤트 처리
        let mouse = { x: 0, y: 0, isDown: false };

        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
            mouse.isDown = true;

            // 클릭한 곳과 가장 가까운 입자 찾기
            let minDist = 30;
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

        window.addEventListener('mouseup', () => {
            mouse.isDown = false;
            draggedParticle = null;
        });

        // 루프 실행
        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 물리 업데이트
            particles.forEach(p => p.update());
            if (draggedParticle) {
                draggedParticle.x = mouse.x;
                draggedParticle.y = mouse.y;
            }

            for (let i = 0; i < 5; i++) {
                constraints.forEach(c => c.resolve());
            }

            // 그리기
            ctx.beginPath();
            ctx.strokeStyle = '#4A5568';
            ctx.lineWidth = 1.5;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
                    ctx.fillStyle = '#E53E3E';
                    ctx.fill();
                }
            });

            requestAnimationFrame(loop);
        }

        loop();
    </script>
</body>
</html>
"""

# HTML 컴포넌트로 화면에 출력
components.html(html_code, height=520)
