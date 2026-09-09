import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# 페이지 설정
st.set_page_config(page_title="Streamlit 천 시뮬레이션", layout="wide")
st.title("🧵 Streamlit 베를레 적분 천 시뮬레이션")

# 사이드바 설정 (물리 파라미터 제어)
st.sidebar.header("⚙️ 시뮬레이션 설정")
cols = st.sidebar.slider("가로 입자 수", 5, 20, 10)
rows = st.sidebar.slider("세로 입자 수", 5, 20, 10)
gravity = st.sidebar.slider("중력 (Gravity)", 0.0, 2.0, 0.5, step=0.1)
iterations = st.sidebar.slider("제약 조건 반복 (Stiffness)", 1, 10, 5)
steps = st.sidebar.slider("총 프레임 수", 50, 300, 150)

# 클래스 정의
class Particle:
    def __init__(self, x, y, pinned=False):
        self.x = x
        self.y = y
        self.oldx = x
        self.oldy = y
        self.pinned = pinned

    def update(self, g, dt=1.0):
        if self.pinned:
            return
        vx = self.x - self.oldx
        vy = self.y - self.oldy
        self.oldx = self.x
        self.oldy = self.y
        self.x += vx
        self.y += vy - g * dt * dt  # y축이 위쪽을 향하도록 -g 적용

class Constraint:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.length = np.hypot(p1.x - p2.x, p1.y - p2.y)

    def resolve(self):
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        dist = np.hypot(dx, dy)
        if dist == 0:
            return
        diff = (self.length - dist) / dist * 0.5
        off_x = dx * diff
        off_y = dy * diff

        if not self.p1.pinned:
            self.p1.x -= off_x
            self.p1.y -= off_y
        if not self.p2.pinned:
            self.p2.x += off_x
            self.p2.y += off_y

# 시뮬레이션 시작 버튼
if st.button("🚀 시뮬레이션 시작"):
    # 입자 및 제약 조건 초기화
    particles = []
    constraints = []
    
    spacing = 1.0
    for r in range(rows):
        row_particles = []
        for c in range(cols):
            # 맨 위쪽 양 끝 모서리 입자 고정
            pinned = (r == 0 and (c == 0 or c == cols - 1))
            p = Particle(c * spacing, -r * spacing, pinned=pinned)
            row_particles.append(p)
        particles.append(row_particles)

    # 제약 조건(스프링) 연결
    for r in range(rows):
        for c in range(cols):
            if c < cols - 1:
                constraints.append(Constraint(particles[r][c], particles[r][c+1]))
            if r < rows - 1:
                constraints.append(Constraint(particles[r][c], particles[r+1][c]))

    # 애니메이션 출력을 위한 Streamlit 빈 요소 생성
    plot_spot = st.empty()

    # 시뮬레이션 루프
    for frame in range(steps):
        # 1. 위치 업데이트 (Verlet Integration)
        for row in particles:
            for p in row:
                p.update(gravity)

        # 2. 제약 조건 해결 (Relaxation)
        for _ in range(iterations):
            for c in constraints:
                c.resolve()

        # 3. Matplotlib을 이용한 그려주기
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_xlim(-2, cols * spacing + 2)
        ax.set_ylim(-rows * spacing - 3, 2)
        ax.set_aspect('equal')
        ax.axis('off')

        # 제약 조건(선) 그리기
        for c in constraints:
            ax.plot([c.p1.x, c.p2.x], [c.p1.y, c.p2.y], color='gray', lw=1.5)

        # 고정된 점 강조 표시
        for row in particles:
            for p in row:
                if p.pinned:
                    ax.plot(p.x, p.y, 'ro', markersize=6)

        # Streamlit 화면 갱신
        plot_spot.pyplot(fig)
        plt.close(fig)
        time.sleep(0.01)

    st.success("시뮬레이션 완료!")
