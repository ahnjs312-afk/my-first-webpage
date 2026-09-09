class Cloth {
    constructor(x, y, cols = 7, rows = 7, spacing = 14) {
        this.particles = [];
        this.constraints = [];

        // 천 입자 생성
        for (let r = 0; r < rows; r++) {
            for (let c = 0; c < cols; c++) {
                this.particles.push(new Particle(x + c * spacing, y + r * spacing));
            }
        }

        // 솟구쳐 오르는 회전 및 초기 속도 (Verlet 방식: oldx, oldy 조절)
        let vx = (Math.random() - 0.5) * 6;
        let vy = -(12 + Math.random() * 4);
        
        // 중앙부에 약간의 불균일한 힘을 주어 튀어오를 때 펄럭이게 만듦
        this.particles.forEach((p, i) => {
            let noiseX = (Math.random() - 0.5) * 2;
            let noiseY = (Math.random() - 0.5) * 2;
            p.oldx = p.x - (vx + noiseX);
            p.oldy = p.y - (vy + noiseY);
        });

        // 가로, 세로 및 대각선(Shear) 제약 조건 추가로 천 형태 유지 강화
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
        
        // 반복 횟수를 6회로 늘려 팽팽하고 유연한 베를레 적분 반응 생성
        for (let i = 0; i < 6; i++) {
            this.constraints.forEach(c => c.resolve());
        }
    }
}
