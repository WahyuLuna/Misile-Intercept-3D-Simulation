import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- 1. Parameter Fisika & Simulasi ---
dt = 0.1
t_max = 500  # Frame lebih banyak untuk durasi lebih lama
g = 9.8      # Percepatan gravitasi (m/s^2)

# Kondisi Target (Bergerak)
target_pos = np.array([3500.0, 1500.0, 800.0])
target_vel = np.array([-40.0, -30.0, 0.0])

# Kondisi Misil
missile_pos = np.array([0.0, 0.0, 0.0])
missile_vel = np.array([0.0, 0.0, 0.0]) # Kecepatan awal
missile_speed = 220.0 # Kecepatan dorong misil (m/s)

# Storage
m_path = []
t_path = []
collision_frame = None

# --- 2. Loop Kalkulasi dengan Gravitasi & Collision ---
curr_m = missile_pos.copy()
curr_t = target_pos.copy()

for i in range(t_max):
    m_path.append(curr_m.copy())
    t_path.append(curr_t.copy())
    
    # Cek Jarak (Collision Detection)
    distance = np.linalg.norm(curr_t - curr_m)
    if distance < 15.0: # Jika jarak < 15 meter, dianggap kena
        collision_frame = i
        # Isi sisa path dengan posisi yang sama agar visualnya "freeze"
        for _ in range(i, t_max):
            m_path.append(curr_m.copy())
            t_path.append(curr_t.copy())
        break
    
    # Pergerakan Target
    curr_t += target_vel * dt
    
    # Pergerakan Misil (Mengejar + Gravitasi)
    direction = curr_t - curr_m
    unit_dir = direction / np.linalg.norm(direction)
    
    # Update Kecepatan: Arah dorong misil dikurangi tarikan gravitasi pada sumbu Z
    # Kita asumsikan misil punya mesin yang terus mendorong ke arah target
    curr_m += (unit_dir * missile_speed * dt)
    curr_m[2] -= 0.5 * g * (dt**2) # Efek penurunan ketinggian karena gravitasi

m_path = np.array(m_path)
t_path = np.array(t_path)

# --- 3. Visualisasi ---
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# Batas Grafik
ax.set_xlim(0, 4000)
ax.set_ylim(0, 2000)
ax.set_zlim(0, 1000)

line_m, = ax.plot([], [], [], 'r-', linewidth=2, label='Missile')
line_t, = ax.plot([], [], [], 'b--', alpha=0.4, label='Target Path')
dot_m = ax.scatter([], [], [], color='red', s=40)
dot_t = ax.scatter([], [], [], color='blue', s=60, marker='s') # Target kotak biru

def animate(i):
    # Jika sudah tabrakan, gunakan posisi terakhir di collision_frame
    idx = i if collision_frame is None or i < collision_frame else collision_frame
    
    line_m.set_data(m_path[:idx, 0], m_path[:idx, 1])
    line_m.set_3d_properties(m_path[:idx, 2])
    
    line_t.set_data(t_path[:idx, 0], t_path[:idx, 1])
    line_t.set_3d_properties(t_path[:idx, 2])
    
    dot_m._offsets3d = (m_path[idx:idx+1, 0], m_path[idx:idx+1, 1], m_path[idx:idx+1, 2])
    dot_t._offsets3d = (t_path[idx:idx+1, 0], t_path[idx:idx+1, 1], t_path[idx:idx+1, 2])
    
    if collision_frame is not None and i >= collision_frame:
        ax.set_title(f"BOOM! Target Neutralized at t={i*dt:.1f}s", color='red', fontsize=14)
    else:
        ax.set_title(f"Simulasi Intersepsi - Time: {i*dt:.1f}s")
        
    return line_m, line_t, dot_m, dot_t

ani = FuncAnimation(fig, animate, frames=len(m_path), interval=20, blit=False)
plt.legend()
plt.show()