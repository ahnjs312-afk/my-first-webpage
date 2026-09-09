import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧵 마우스 상호작용 천 시뮬레이션")
st.caption("마우스로 천을 클릭하고 드래그해 보세요!")

html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { 
            margin: 0; 
            overflow: hidden; 
            background-color: #1a1a2e; /* 어두운 남색 배경 */
            display: flex; 
            justify-content: center; 
            align-items: center; 
        }
        canvas { 
            background: #16213e; /* 캔버스 내부 배경 (짙은 네이비) */
            border: 2px solid #0f3460;
            border-radius: 12px; 
            box-shadow: 0 8px 16px rgba(0,0,0,0.4); 
            cursor: none; /* 기본 마우스 커서 숨기기 */
        }
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

        let particles = [];
        let constraints = [];
        let draggedParticle = null;

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

        // 마우스 이벤트
        let mouse = { x: -100, y: -100, isHover: false };

        canvas.addEventListener('mouseenter', () => { mouse.isHover = true; });
        canvas.addEventListener('mouseleave', () => { mouse.isHover = false; draggedParticle = null; });

        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

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
            draggedParticle = null;
        });

        // 애니메이션 루프
        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            particles.forEach(p => p.update());
            if (draggedParticle) {
                draggedParticle.x = mouse.x;
                draggedParticle.y = mouse.y;
            }

            for (let i = 0; i < 5; i++) {
                constraints.forEach(c => c.resolve());
            }

            // 천 (실) 그리기 - 형광 하늘색
            ctx.beginPath();
            ctx.strokeStyle = '#00f2fe';
            ctx.lineWidth = 2;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            // 고정점 그리기 - 주황색
            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
                    ctx.fillStyle = '#ff7675';
                    ctx.fill();
                }
            });

            // 마우스 커서 맞춤 그리기 - 형광 핑크 포인터
            if (mouse.isHover) {
                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, draggedParticle ? 8 : 6, 0, Math.PI * 2);
                ctx.fillStyle = draggedParticle ? '#ff007f' : 'rgba(255, 0, 127, 0.7)';
                ctx.strokeStyle = '#ffffff';
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

components.html(html_code, height=530)
