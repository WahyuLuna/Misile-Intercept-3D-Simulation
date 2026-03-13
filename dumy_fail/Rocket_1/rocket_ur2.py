from ursina import *
import random

app = Ursina()

# --- 1. Lingkungan ---
Entity(model='plane', scale=1000, texture='grass', color=color.gray)
Sky()

score = 0
score_text = Text(text=f'Score Penyerang: {score}', position=(-0.8, 0.45), scale=2, color=color.red)

# Markas
penyerang_base = Entity(model='cube', color=color.red, scale=(5,1,5), position=(0,0,0))
bertahan_base = Entity(model='cube', color=color.blue, scale=(5,1,5), position=(150,0,0))

active_attackers = [] # List global untuk melacak misil penyerang

# --- 2. Misil Penyerang (Parabola Akurat) ---
class AttackerMissile(Entity):
    def __init__(self, target_pos):
        super().__init__(model='sphere', color=color.red, scale=1.2, position=penyerang_base.position)
        self.target_pos = target_pos
        self.g = 9.8
        self.speed_horiz = 20  # Kecepatan horisontal konstan
        self.time_alive = 0
        
        # Hitung arah horisontal (X dan Z saja)
        diff = target_pos - self.position
        self.direction_horiz = Vec3(diff.x, 0, diff.z).normalized()
        
        # Hitung kecepatan awal vertikal (V0y) agar jatuh tepat di target
        dist_horiz = distance_2d(self.position, target_pos)
        self.total_time_needed = dist_horiz / self.speed_horiz
        # Rumus: y = v0y*t - 0.5*g*t^2 -> karena y_awal & y_akhir = 0, maka v0y = 0.5 * g * t_total
        self.v0y = 0.5 * self.g * self.total_time_needed
        
        self.is_destroyed = False

    def update(self):
        if self.is_destroyed: return
        
        self.time_alive += time.dt
        t = self.time_alive
        
        # Update Posisi Horisontal
        new_pos = penyerang_base.position + (self.direction_horiz * self.speed_horiz * t)
        # Update Posisi Vertikal (Y)
        new_y = (self.v0y * t) - (0.5 * self.g * t**2)
        
        self.position = Vec3(new_pos.x, max(0, new_y), new_pos.z)

        # Efek Trail
        if t % 0.1 < 0.05:
            e = Entity(model='sphere', position=self.position, scale=0.3, color=color.red, alpha=0.6)
            e.animate_scale(0, duration=0.4)
            destroy(e, delay=0.5)

        # Cek jika sampai atau lewat waktu tempuh
        if t >= self.total_time_needed:
            if distance(self.position, self.target_pos) < 12:
                global score
                score += 1
                score_text.text = f'Score Penyerang: {score}'
            self.explode()

    def explode(self):
        self.is_destroyed = True
        exp = Entity(model='sphere', position=self.position, color=color.orange, scale=1)
        exp.animate_scale(15, duration=0.2)
        destroy(exp, delay=0.3)
        destroy(self)

# --- 3. Misil Bertahan (Interceptor Cepat) ---
class InterceptorMissile(Entity):
    def __init__(self, target_missile):
        super().__init__(model='cube', color=color.yellow, scale=(0.5, 1.5, 0.5), position=bertahan_base.position)
        self.target = target_missile
        self.speed = 50 # Lebih cepat dari penyerang
        self.active = True

    def update(self):
        if not self.active or not self.target or self.target.is_destroyed:
            destroy(self)
            return

        # Pengejaran langsung ke posisi misil merah
        self.look_at(self.target.position)
        self.rotation_x += 90 
        self.position += self.forward * self.speed * time.dt

        # Cek Tabrakan di udara
        if distance(self.position, self.target.position) < 4:
            self.target.explode()
            self.active = False
            print("Interception Successful!")
            destroy(self)

# --- 4. Sistem Manager ---
spawn_attack_timer = 0
spawn_defend_timer = 0
attack_count = 0

def update():
    global spawn_attack_timer, spawn_defend_timer, attack_count, active_attackers
    
    # Penyerang: Spawn lebih cepat (2 detik sekali)
    if attack_count < 10: # Tambah jumlah serangan
        spawn_attack_timer += time.dt
        if spawn_attack_timer >= 2:
            m = AttackerMissile(target_pos=bertahan_base.position)
            active_attackers.append(m)
            spawn_attack_timer = 0
            attack_count += 1

    # Bertahan: Cek lebih sering (0.5 detik sekali)
    spawn_defend_timer += time.dt
    if spawn_defend_timer >= 0.5:
        # Bersihkan list dari misil yang sudah hancur
        active_attackers = [m for m in active_attackers if not m.is_destroyed]
        
        if active_attackers:
            # Tembak misil yang paling dekat dengan markas bertahan
            target_to_intercept = min(active_attackers, key=lambda x: distance(x.position, bertahan_base.position))
            InterceptorMissile(target_to_intercept)
            spawn_defend_timer = 0

EditorCamera()
app.run()