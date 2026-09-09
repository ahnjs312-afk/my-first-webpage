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
            background-color: #f7f9fc; /* 연한 회색 배경 */
            display: flex; 
            justify-content: center; 
            align-items: center; 
        }
        canvas { 
            background: #ffffff; /* 흰색 배경 */
            border: 2px solid #e2e8f0;
            border-radius: 12px; 
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
            cursor: none; /* 기본 커서 숨기기 */
        }
    </style>
</head>
<body>
    <canvas id="canvas" width="850" height="600"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        // 천 크기 및 입자 수 확장 (가로 25개, 세로 18개)
        const cols = 25;
        const rows = 18;
        const spacing = 22; // 입자 간격
        const startX = 150;
        const startY = 40;
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

        // 초기화 (맨 위 줄 5개 위치를 고정)
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                let pinned = (r === 0 && (
                    c === 0 || 
                    c === Math.floor((cols - 1) * 0.25) || 
                    c === Math.floor((cols - 1) * 0.5) || 
                    c === Math.floor((cols - 1) * 0.75) || 
                    c === cols - 1
                ));
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

            // 천 (실) 그리기 - 검은색 (#1a1a1a)
            ctx.beginPath();
            ctx.strokeStyle = '#1a1a1a';
            ctx.lineWidth = 1.8;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            // 고정점 그리기 - 어두운 회색
            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
                    ctx.fillStyle = '#4a5568';
                    ctx.fill();
                }
            });

            // 마우스 커서 - 빨간색 (#ff2d55)
            if (mouse.isHover) {
                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, draggedParticle ? 8 : 6, 0, Math.PI * 2);
                ctx.fillStyle = draggedParticle ? '#ff2d55' : 'rgba(255, 45, 85, 0.7)';
                ctx.strokeStyle = '#ffffff';
                ctx.lineWidth = 2;
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

components.html(html_code, height=630)
