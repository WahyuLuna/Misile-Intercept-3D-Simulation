import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random

# --- 1. Konfigurasi ---
dt = 0.1
total_time = 60  # Simulasi berjalan 60 detik
frames = int(total_time / dt)
g = 9.8

# Target awal
target_pos = np.array([3000.0, 0.0, 500.0])
target_vel = np.array([-20.0, 150.0, 0.0]) # Kecepatan dasar

# Properti Misil
spawn_interval = 5.0 # detik
life_span = 20.0     # detik
missile_speed = 250.0

class Missile:
    def __init__(self, start_time, color):
        self.start_time = start_time
        self.color = color
        self.pos = np.array([0.0, 0.0, 0.0])
        self.path = []
        self.active = True
        self.exploded = False

    def update(self, current_time, target_p, target_v):
        age = current_time - self.start_time
        
        if not self.active or age > life_span:
            self.active = False
            return

        # LOGIKA PREDIKSI: Misil menebak posisi target 1 detik ke depan
        prediction_time = 1.0 
        predicted_target = target_p + (target_v * prediction_time)
        
        # Arah ke posisi prediksi
        direction = predicted_target - self.pos
        dist = np.linalg.norm(direction)
        
        if dist < 20: # Collision
            self.exploded = True
            self.active = False
            return

        unit_dir = direction / dist
        self.pos += (unit_dir * missile_speed * dt)
        self.pos[2] -= 0.5 * g * (dt**2) # Gravitasi
        self.path.append(self.pos.copy())

# --- 2. Perhitungan Jalur Simulasi ---
all_missiles = []
target_history = []
curr_t_pos = target_pos.copy()
curr_t_vel = target_vel.copy()

for f in range(frames):
    curr_time = f * dt
    
    # 1. Update Target (Gerak Acak)
    # Menambahkan noise acak pada kecepatan
    curr_t_vel += np.random.uniform(-2, 2, 3) 
    curr_t_vel = np.clip(curr_t_vel, -60, 60) # Batasi kecepatan agar tidak liar
    curr_t_pos += curr_t_vel * dt
    target_history.append(curr_t_pos.copy())
    
    # 2. Spawn Misil Baru setiap 5 detik
    if abs(curr_time % spawn_interval) < 0.01:
        color = "#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
        all_missiles.append(Missile(curr_time, color))
    
    # 3. Update Semua Misil
    for m in all_missiles:
        m.update(curr_time, curr_t_pos, curr_t_vel)

target_history = np.array(target_history)

# --- 3. Visualisasi ---
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(0, 4000); ax.set_ylim(-2000, 2000); ax.set_zlim(0, 1000)

target_dot = ax.scatter([], [], [], color='black', s=100, label='Target (Random)')
missile_plots = [ax.plot([], [], [], color=m.color, lw=2)[0] for m in all_missiles]
missile_dots = [ax.scatter([], [], [], color=m.color, s=40) for m in all_missiles]

def animate(i):
    curr_time = i * dt
    # Update Target
    target_dot._offsets3d = (target_history[i:i+1, 0], target_history[i:i+1, 1], target_history[i:i+1, 2])
    
    for idx, m in enumerate(all_missiles):
        # Hitung index relatif misil berdasarkan waktu spawn-nya
        m_idx = int((curr_time - m.start_time) / dt)
        
        if m_idx > 0 and len(m.path) > 0:
            actual_idx = min(m_idx, len(m.path)-1)
            path_data = np.array(m.path[:actual_idx])
            
            missile_plots[idx].set_data(path_data[:, 0], path_data[:, 1])
            missile_plots[idx].set_3d_properties(path_data[:, 2])
            
            curr_p = m.path[actual_idx]
            missile_dots[idx]._offsets3d = ([curr_p[0]], [curr_p[1]], [curr_p[2]])
            
            if m.exploded:
                ax.set_title(f"Target Hit by Missile {idx+1}!", color=m.color)
                
    return [target_dot] + missile_plots + missile_dots

ani = FuncAnimation(fig, animate, frames=frames, interval=20, blit=False)
plt.legend()
plt.show()