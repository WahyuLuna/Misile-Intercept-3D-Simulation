from ursina import *
import random

# --- 1. Inisialisasi App ---
app = Ursina()

# Lingkungan
Entity(model='plane', scale=1000, texture='grass', color=color.gray) # Tanah
Sky() # Langit biru

# --- 2. Class Target ---
class Target(Entity):
    def __init__(self, start_pos):
        super().__init__(
            model='sphere', 
            color=color.cyan, 
            scale=2, 
            position=start_pos
        )
        self.vel = Vec3(random.uniform(-15, -10), random.uniform(-2, 2), random.uniform(-5, 5))
        self.is_destroyed = False

    def update(self):
        if not self.is_destroyed:
            # Gerak acak tipis
            self.vel += Vec3(random.uniform(-1,1), random.uniform(-0.5,0.5), random.uniform(-1,1)) * time.dt
            self.position += self.vel * time.dt * 5 # Kecepatan ditingkatkan

# --- 3. Class Missile ---
class Missile(Entity):
    def __init__(self, target, color_trail):
        super().__init__(
            model='cube',  # Changed from 'cone' which is not a built-in model
            color=color.red, 
            scale=(0.5, 2, 0.5)
        )
        self.target = target
        self.speed = 100
        self.life_span = 15
        self.timer = 0
        self.color_trail = color_trail
        
        # Efek Asap (Trail)
        self.trail = Entity(model=None)
        self.last_pos = self.position

    def update(self):
        self.timer += time.dt
        if self.timer > self.life_span or not self.target or self.target.is_destroyed:
            destroy(self)
            return

        # Logika Prediksi Sederhana
        dist = distance(self.position, self.target.position)
        prediction = self.target.position + (self.target.vel * (dist / self.speed))
        
        # Rotasi menghadap target
        self.look_at(prediction)
        # self.rotation_x += 90 # This correction was likely for the cone model's orientation
        
        # Gerak maju
        self.position += self.forward * self.speed * time.dt
        
        # Visual Jejak (Trail)
        if distance(self.position, self.last_pos) > 0.5:
            e = Entity(model='sphere', position=self.position, scale=0.3, 
                       color=self.color_trail, alpha=0.5)
            e.animate_scale(0, duration=1, curve=curve.linear)
            destroy(e, delay=1)
            self.last_pos = self.position

        # Cek Tabrakan
        if distance(self.position, self.target.position) < 3:
            print("BOOM!")
            self.target.is_destroyed = True
            explode = Entity(model='sphere', position=self.position, color=color.orange, scale=1)
            explode.animate_scale(10, duration=0.2)
            explode.animate_color(color.clear, duration=0.3)
            destroy(explode, delay=0.5)
            destroy(self.target)
            destroy(self)

# --- 4. Sistem Spawning & Kontrol ---
targets = [Target((100, random.uniform(10, 50), random.uniform(-50, 50))) for _ in range(5)]
missiles = []
spawn_timer = 0

def update():
    global spawn_timer
    spawn_timer += time.dt
    
    # Spawn Misil setiap 5 detik
    if spawn_timer >= 5:
        active_targets = [t for t in targets if not t.is_destroyed]
        if active_targets:
            t = random.choice(active_targets)
            m = Missile(target=t, color_trail=color.random_color())
            missiles.append(m)
        spawn_timer = 0

# Kamera Orbit agar bisa diputar
EditorCamera() 

app.run()