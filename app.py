import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🧵 천 시뮬레이션 (상호작용 & 자르기)")
st.caption("💡 **왼쪽 클릭 드래그**: 천 잡고 당기기 | ✂️ **오른쪽 클릭 드래그**: 천 자르기")

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
        .controls {
            margin-bottom: 10px;
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
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #e02d22;
        }
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
    <div class="controls">
        <button onclick="resetCloth()">🔄 천 초기화 (Reset)</button>
    </div>
    <canvas id="canvas" width="850" height="560"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const cols = 25;
        const rows = 18;
        const spacing = 22;
        const startX = 150;
        const startY = 40;
        const gravity = 0.2;
        const friction = 0.99;

        let particles = [];
        let constraints = [];
        let draggedParticle = null;
        let isRightClicking = false;

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

        // 초기화 함수
        function resetCloth() {
            particles = [];
            constraints = [];
            draggedParticle = null;

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
        }

        // 선분과 점(마우스) 사이의 거리 계산 (자르기 로직)
        function distToSegment(p, v, w) {
            let l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
            if (l2 === 0) return Math.hypot(p.x - v.x, p.y - v.y);
            let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
            t = Math.max(0, Math.min(1, t));
            return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
        }

        // 우클릭 기본 메뉴 방지
        canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        let mouse = { x: -100, y: -100, isHover: false };

        canvas.addEventListener('mouseenter', () => { mouse.isHover = true; });
        canvas.addEventListener('mouseleave', () => { mouse.isHover = false; draggedParticle = null; isRightClicking = false; });

        canvas.addEventListener('mousedown', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;

            if (e.button === 0) { // 좌클릭: 잡아당기기
                let minDist = 35;
                particles.forEach(p => {
                    let d = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                    if (d < minDist) {
                        minDist = d;
                        draggedParticle = p;
                    }
                });
            } else if (e.button === 2) { // 우클릭: 자르기 시작
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

        // 자르기 로직
        function cutCloth() {
            const cutRadius = 12; // 자르는 범위 반지름
            constraints = constraints.filter(c => {
                let d = distToSegment(mouse, c.p1, c.p2);
                return d > cutRadius;
            });
        }

        // 첫 시작 시 초기화
        resetCloth();

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

            // 천 (실) - 검은색
            ctx.beginPath();
            ctx.strokeStyle = '#1a1a1a';
            ctx.lineWidth = 1.8;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            // 고정점 - 어두운 회색
            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
                    ctx.fillStyle = '#4a5568';
                    ctx.fill();
                }
            });

            // 마우스 커서 - 빨간색 (자르는 중일 땐 가위 아이콘 모드)
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
