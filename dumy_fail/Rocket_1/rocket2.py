import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# --- 1. Pengaturan Simulasi ---
dt = 0.1  # Selang waktu (detik)
t_max = 300 # Jumlah frame
t = np.linspace(0, 30, t_max)

# Kondisi Awal Target (Bergerak lurus pelan)
# Target mulai dari X=4000, Y=-2000 dan bergerak ke arah Y positif
target_start = np.array([4000.0, -2000.0, 600.0])
target_velocity = np.array([-50.0, 80.0, 5.0]) # Kecepatan target (m/s)

# Kondisi Awal Misil (Lebih cepat dari target)
missile_pos = np.array([0.0, 0.0, 0.0])
missile_speed = 180.0 # Kecepatan konstan misil (m/s)

# Array untuk menyimpan history posisi untuk digambar
target_path = []
missile_path = []

# --- 2. Kalkulasi Pergerakan ---
curr_missile = missile_pos.copy()
curr_target = target_start.copy()

for i in range(t_max):
    # Simpan posisi saat ini
    target_path.append(curr_target.copy())
    missile_path.append(curr_missile.copy())
    
    # 1. Update posisi target (Gerak Lurus Beraturan)
    curr_target += target_velocity * dt
    
    # 2. Update posisi misil (Mengejar target)
    vector_to_target = curr_target - curr_missile
    distance = np.linalg.norm(vector_to_target)
    
    if distance > 5: # Jika belum kena
        unit_vector = vector_to_target / distance
        curr_missile += unit_vector * missile_speed * dt

target_path = np.array(target_path)
missile_path = np.array(missile_path)

# --- 3. Visualisasi 3D ---
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Batas koordinat agar grafik tidak "goyang" saat animasi
ax.set_xlim(0, 5000)
ax.set_ylim(-2500, 2500)
ax.set_zlim(0, 1000)

line_target, = ax.plot([], [], [], 'b--', alpha=0.5, label='Jalur Target')
line_missile, = ax.plot([], [], [], 'r-', alpha=0.8, label='Jalur Misil')
point_target = ax.scatter([], [], [], color='blue', s=50, label='Target')
point_missile = ax.scatter([], [], [], color='red', s=30, label='Misil')

ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_zlabel('Z (m)')
ax.legend()

def init():
    return line_target, line_missile, point_target, point_missile

def animate(i):
    # Update garis lintasan
    line_target.set_data(target_path[:i, 0], target_path[:i, 1])
    line_target.set_3d_properties(target_path[:i, 2])
    
    line_missile.set_data(missile_path[:i, 0], missile_path[:i, 1])
    line_missile.set_3d_properties(missile_path[:i, 2])
    
    # Update titik posisi sekarang
    point_target._offsets3d = (target_path[i:i+1, 0], target_path[i:i+1, 1], target_path[i:i+1, 2])
    point_missile._offsets3d = (missile_path[i:i+1, 0], missile_path[i:i+1, 1], missile_path[i:i+1, 2])
    
    return line_target, line_missile, point_target, point_missile

ani = FuncAnimation(fig, animate, init_func=init, frames=t_max, interval=30, blit=False)
plt.show()