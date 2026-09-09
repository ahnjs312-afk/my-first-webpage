import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("🍬 Mini Cut the Rope 게임")
st.caption("💡 **마우스 왼쪽 드래그**: 밧줄 자르기 | 🎯 **목표**: 별을 획득하고 사탕을 Om Nom에게 전달하세요!")

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
            color: #2d3748;
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
        <div class="score-board" id="score">⭐ 획득한 별: 0 / 3</div>
        <button onclick="resetGame()">🔄 다시 하기 (Reset)</button>
    </div>
    <canvas id="canvas" width="800" height="550"></canvas>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        const gravity = 0.25;
        const friction = 0.99;

        // 게임 상태
        let particles = [];
        let constraints = [];
        let candy = null;
        let omNom = { x: 400, y: 470, radius: 35 };
        let stars = [];
        let collectedStars = 0;
        let isGameCleared = false;
        let isMouseDown = false;

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

        // 밧줄 생성 함수
        function createRope(pinX, pinY, length, numSegments, targetCandy) {
            let ropeParticles = [new Particle(pinX, pinY, true)];
            let segmentLen = length / numSegments;

            for (let i = 1; i < numSegments; i++) {
                ropeParticles.push(new Particle(pinX + (targetCandy.x - pinX) * (i / numSegments), pinY + (targetCandy.y - pinY) * (i / numSegments)));
            }
            ropeParticles.push(targetCandy); // 마지막 입자는 사탕과 연결

            particles.push(...ropeParticles.slice(0, -1));

            for (let i = 0; i < ropeParticles.length - 1; i++) {
                constraints.push(new Constraint(ropeParticles[i], ropeParticles[i + 1]));
            }
        }

        function resetGame() {
            particles = [];
            constraints = [];
            collectedStars = 0;
            isGameCleared = false;
            document.getElementById('score').innerText = "⭐ 획득한 별: 0 / 3";

            // 별 위치 초기화
            stars = [
                { x: 300, y: 250, collected: false },
                { x: 400, y: 320, collected: false },
                { x: 500, y: 250, collected: false }
            ];

            // 사탕 (중앙)
            candy = new Particle(400, 180);
            particles.push(candy);

            // 좌/우 고정점에서 사탕으로 연결되는 2개의 밧줄 생성
            createRope(220, 80, 200, 10, candy);
            createRope(580, 80, 200, 10, candy);
        }

        // 선분과 마우스 거리 함수 (자르기용)
        function distToSegment(p, v, w) {
            let l2 = Math.pow(v.x - w.x, 2) + Math.pow(v.y - w.y, 2);
            if (l2 === 0) return Math.hypot(p.x - v.x, p.y - v.y);
            let t = ((p.x - v.x) * (w.x - v.x) + (p.y - v.y) * (w.y - v.y)) / l2;
            t = Math.max(0, Math.min(1, t));
            return Math.hypot(p.x - (v.x + t * (w.x - v.x)), p.y - (v.y + t * (w.y - v.y)));
        }

        let mouse = { x: -100, y: -100, isHover: false };

        canvas.addEventListener('contextmenu', (e) => e.preventDefault());
        canvas.addEventListener('mouseenter', () => { mouse.isHover = true; });
        canvas.addEventListener('mouseleave', () => { mouse.isHover = false; isMouseDown = false; });

        canvas.addEventListener('mousedown', (e) => {
            isMouseDown = true;
            cutRope();
        });

        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
            if (isMouseDown) cutRope();
        });

        window.addEventListener('mouseup', () => { isMouseDown = false; });

        function cutRope() {
            const cutRadius = 10;
            constraints = constraints.filter(c => {
                let d = distToSegment(mouse, c.p1, c.p2);
                return d > cutRadius;
            });
        }

        resetGame();

        function loop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 물리 업데이트
            particles.forEach(p => p.update());
            for (let i = 0; i < 5; i++) {
                constraints.forEach(c => c.resolve());
            }

            // 별 획득 충돌 검사
            stars.forEach(s => {
                if (!s.collected && Math.hypot(candy.x - s.x, candy.y - s.y) < 25) {
                    s.collected = true;
                    collectedStars++;
                    document.getElementById('score').innerText = `⭐ 획득한 별: ${collectedStars} / 3`;
                }
            });

            // Om Nom 먹기 충돌 검사
            if (!isGameCleared && Math.hypot(candy.x - omNom.x, candy.y - omNom.y) < omNom.radius + 10) {
                isGameCleared = true;
            }

            // 1. 밧줄 그리기 (갈색)
            ctx.beginPath();
            ctx.strokeStyle = '#8B4513';
            ctx.lineWidth = 3;
            constraints.forEach(c => {
                ctx.moveTo(c.p1.x, c.p1.y);
                ctx.lineTo(c.p2.x, c.p2.y);
            });
            ctx.stroke();

            // 2. 고정핀 그리기
            particles.forEach(p => {
                if (p.pinned) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
                    ctx.fillStyle = '#4A5568';
                    ctx.fill();
                }
            });

            // 3. 별 그리기
            stars.forEach(s => {
                if (!s.collected) {
                    ctx.font = "24px sans-serif";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText("⭐", s.x, s.y);
                }
            });

            // 4. Om Nom (캐릭터) 그리기
            ctx.beginPath();
            ctx.arc(omNom.x, omNom.y, omNom.radius, 0, Math.PI * 2);
            ctx.fillStyle = '#48BB78'; // 초록색 몸체
            ctx.fill();

            // Om Nom 눈 & 입
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(omNom.x - 12, omNom.y - 12, 8, 0, Math.PI * 2);
            ctx.arc(omNom.x + 12, omNom.y - 12, 8, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = 'black';
            ctx.beginPath();
            ctx.arc(omNom.x - 10, omNom.y - 12, 3, 0, Math.PI * 2);
            ctx.arc(omNom.x + 10, omNom.y - 12, 3, 0, Math.PI * 2);
            ctx.fill();

            // 입 (성공 여부에 따라 바뀜)
            ctx.beginPath();
            if (isGameCleared) {
                ctx.arc(omNom.x, omNom.y + 5, 15, 0, Math.PI); // 벌린 입
                ctx.fillStyle = '#E53E3E';
                ctx.fill();
            } else {
                ctx.arc(omNom.x, omNom.y + 10, 10, Math.PI, 0); // 웃는 입
                ctx.strokeStyle = '#2F855A';
                ctx.lineWidth = 3;
                ctx.stroke();
            }

            // 5. 사탕 그리기 (빨간/하얀 회전 사탕)
            if (!isGameCleared) {
                ctx.beginPath();
                ctx.arc(candy.x, candy.y, 16, 0, Math.PI * 2);
                ctx.fillStyle = '#FF2D55';
                ctx.fill();
                ctx.strokeStyle = '#FFFFFF';
                ctx.lineWidth = 3;
                ctx.stroke();
            }

            // 성공 안내 텍스트
            if (isGameCleared) {
                ctx.font = "bold 32px sans-serif";
                ctx.fillStyle = "#2B6CB0";
                ctx.textAlign = "center";
                ctx.fillText("🎉 STAGE CLEAR! 🎉", canvas.width / 2, 220);
            }

            // 6. 마우스 커서 (가위 느낌의 빨간 가이드 원)
            if (mouse.isHover) {
                ctx.beginPath();
                ctx.arc(mouse.x, mouse.y, isMouseDown ? 10 : 5, 0, Math.PI * 2);
                ctx.fillStyle = isMouseDown ? 'rgba(255, 45, 85, 0.4)' : '#FF2D55';
                ctx.strokeStyle = '#FF2D55';
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

components.html(html_code, height=620)
