import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random

# --- 1. Konfigurasi ---
dt = 0.1
total_time = 40  # Durasi simulasi
frames = int(total_time / dt)
g = 9.8

spawn_interval = 5.0  # Misil muncul tiap 5 detik
life_span = 15.0       # Nyawa misil 15 detik
missile_speed = 350.0  # Misil harus lebih cepat karena target makin ngebut

# --- 2. Class Target & Missile ---
class Target:
    def __init__(self, id, start_pos, color):
        self.id = id
        self.pos = np.array(start_pos, dtype=float)
        # Kecepatan objek ditingkatkan (range 60-100 m/s)
        self.vel = np.array([random.uniform(-80, -60), random.uniform(-40, 40), random.uniform(-5, 5)])
        self.color = color
        self.history = []
        self.is_destroyed = False

    def update(self):
        if self.is_destroyed: return
        # Gerak acak yang lebih agresif
        self.vel += np.random.uniform(-5, 5, 3)
        self.vel = np.clip(self.vel, -120, 120) 
        self.pos += self.vel * dt
        self.history.append(self.pos.copy())

class Missile:
    def __init__(self, start_time, color, targets):
        self.start_time = start_time
        self.color = color
        self.pos = np.array([0.0, 0.0, 0.0])
        self.path = []
        self.active = True
        self.target_ref = self.assign_target(targets)

    def assign_target(self, targets):
        # Pilih target yang belum hancur dan paling dekat
        active_targets = [t for t in targets if not t.is_destroyed]
        if not active_targets: return None
        return min(active_targets, key=lambda t: np.linalg.norm(t.pos - self.pos))

    def update(self, current_time):
        age = current_time - self.start_time
        if not self.active or age > life_span or self.target_ref is None:
            self.active = False
            return

        # Prediksi posisi masa depan target (Lead Pursuit)
        dist_to_target = np.linalg.norm(self.target_ref.pos - self.pos)
        look_ahead = dist_to_target / missile_speed 
        predicted_pos = self.target_ref.pos + (self.target_ref.vel * look_ahead)
        
        direction = predicted_pos - self.pos
        dist = np.linalg.norm(direction)
        
        if dist < 25: # Deteksi Tabrakan
            self.target_ref.is_destroyed = True
            self.active = False
            print(f"Target {self.target_ref.id} Hancur!")
            return

        unit_dir = direction / dist
        self.pos += (unit_dir * missile_speed * dt)
        self.pos[2] -= 0.5 * g * (dt**2)
        self.path.append(self.pos.copy())

# --- 3. Inisialisasi Data ---
targets = [
    Target(1, [3800, 1000, 700], 'blue'),
    Target(2, [3500, -1000, 500], 'cyan'),
    Target(3, [3000, 500, 900], 'green')
]

missiles = []
target_positions_over_time = {t.id: [] for t in targets}

for f in range(frames):
    curr_time = f * dt
    # Update Targets
    for t in targets:
        t.update()
        target_positions_over_time[t.id].append(t.pos.copy())
    
    # Spawn Missile
    if abs(curr_time % spawn_interval) < 0.01:
        new_color = "#"+''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
        missiles.append(Missile(curr_time, new_color, targets))
    
    # Update Missiles
    for m in missiles:
        m.update(curr_time)

# --- 4. Visualisasi ---
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.set_xlim(0, 4000); ax.set_ylim(-2000, 2000); ax.set_zlim(0, 1200)

target_dots = [ax.scatter([], [], [], color=t.color, s=80, label=f'Target {t.id}') for t in targets]
missile_plots = [ax.plot([], [], [], color=m.color, lw=2)[0] for m in missiles]
missile_dots = [ax.scatter([], [], [], color=m.color, s=30) for m in missiles]

def animate(i):
    curr_time = i * dt
    # Update Targets
    for idx, t in enumerate(targets):
        pos = target_positions_over_time[t.id][i]
        target_dots[idx]._offsets3d = ([pos[0]], [pos[1]], [pos[2]])
    
    # Update Missiles
    for idx, m in enumerate(missiles):
        m_idx = int((curr_time - m.start_time) / dt)
        if 0 < m_idx < len(m.path):
            path_data = np.array(m.path[:m_idx])
            missile_plots[idx].set_data(path_data[:, 0], path_data[:, 1])
            missile_plots[idx].set_3d_properties(path_data[:, 2])
            curr_p = m.path[m_idx-1]
            missile_dots[idx]._offsets3d = ([curr_p[0]], [curr_p[1]], [curr_p[2]])
            
    ax.set_title(f"Multi-Target Defense Simulation - Time: {curr_time:.1f}s")
    return target_dots + missile_plots + missile_dots

ani = FuncAnimation(fig, animate, frames=frames, interval=20, blit=False)
plt.legend(loc='upper left')
plt.show()