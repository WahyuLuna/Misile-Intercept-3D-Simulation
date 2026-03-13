from stable_baselines3 import PPO
from ursina import *
import math
import random
import numpy as np
import os

# ─────────────────────────── APP INIT ────────────────────────────
app = Ursina(title='PPO Missile Intercept Simulation', borderless=False)

# ───────────────────── ENVIRONMENT ─────────────
ground = Entity(model='plane', scale=9000, texture='grass', color=color.gray)
Sky()

# ──────────────────────────── SETTINGS ───────────────────────────
class Settings:
    red_fire_interval       = 1.0
    attacker_missile_speed  = 100.0
    attacker_missile_wobble = 10
    blue_missile_speed      = 80.0
    defender_detect_radius  = 3000.0
    gravity                 = 9.8
    arc_height              = 600.0
    attacker_pos            = Vec3(-4000, 0, 0) # RED
    blue_pos                = Vec3( 800, 0, 0)  # BLUE (Defender)
    time_scale              = 2.0 # Percepat simulasi

cfg = Settings()

class GameState:
    paused = False
    attack_missiles = []
    intercept_missiles = []
    targets = []
    explosions = []
    attack_timer = 0.0

state = GameState()

# ────────────────────── BASES & TARGETS ──────────────────────
atk_base = Entity(model='cube', color=color.red, scale=(8, 2, 8), position=cfg.attacker_pos + Vec3(0, 1, 0))
blue_base = Entity(model='cube', color=color.blue, scale=(8, 2, 8), position=cfg.blue_pos + Vec3(0, 1, 0))
blue_base.is_base = True
state.targets.append(blue_base)

# Gedung Target Biru
for _ in range(30):
    tx = cfg.blue_pos.x + random.uniform(-600, 600)
    tz = cfg.blue_pos.z + random.uniform(-600, 600)
    th = random.uniform(5, 20)
    t_obj = Entity(model='cube', color=color.gray, scale=(8, th, 8), position=(tx, th/2, tz))
    t_obj.is_base = False
    t_obj.center_pos = cfg.blue_pos
    state.targets.append(t_obj)

dome_blue = Entity(model='sphere', position=cfg.blue_pos, scale=cfg.defender_detect_radius * 2, color=color.rgba(0, 0, 255, 60), wireframe=True)

# ──────────────────────── CAMERA SETUP ───────────────────────────
camera.position = (cfg.blue_pos.x - 300, 150, cfg.blue_pos.z - 400)
camera.look_at(cfg.blue_pos)

# ──────────────────────── HUD ──────────────────────────────
Text(parent=camera.ui, text='[ PPO INTERCEPTOR SIMULATION ]', position=(0, 0.45), scale=1.25, color=color.yellow, origin=(0,0))
hud_action = Text(parent=camera.ui, text='Action: [0.0, 0.0]', position=(-0.85, 0.4), scale=1, color=color.green)
hud_reward = Text(parent=camera.ui, text='Reward: 0.0', position=(-0.85, 0.35), scale=1, color=color.cyan)

# ──────────────────────── EXPLOSION ──────────────────────────────
def spawn_explosion(pos, clr=color.orange, size=4.0):
    e1 = Entity(model='sphere', position=pos, color=color.rgba(*clr.rgb, 200), scale=0.3)
    e2 = Entity(model='sphere', position=pos, color=color.rgba(255, 240, 80, 150), scale=0.2)
    state.explosions.append({'e': e1, 'e2': e2, 'timer': 0.0, 'dur': 0.6, 'size': size})

# ──────────────────────── RED ATTACK MISSILE (Target) ─────────────
class AttackMissile:
    def __init__(self):
        self.origin = Vec3(cfg.attacker_pos.x, 10, cfg.attacker_pos.z)
        self.target_ent = random.choice(state.targets)
        self.target = self.target_ent.position
        self.t = 0.0
        self.dist = (self.target - self.origin).length()
        self.speed = cfg.attacker_missile_speed
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.alive = True
        self.body = Entity(model='sphere', color=color.red, scale=1.5)
        self.velocity = Vec3(0,0,0)
        self.last_pos = Vec3(self.origin)
        self._set_pos(self.origin)

    def _get_arc_pos(self, t):
        p = lerp(self.origin, self.target, t)
        p.y += cfg.arc_height * math.sin(math.pi * t)
        if t > 0.5:
            ramp = (t - 0.5) * 2.0
            side = cfg.attacker_missile_wobble * math.sin(self.wobble_phase + 3.0 * t * math.pi * 4)
            p.z += side * ramp
        return p

    def _set_pos(self, pos):
        self.body.position = pos

    def advance(self, dt):
        if not self.alive: return None
        self.t += (self.speed / max(self.dist, 1.0)) * dt
        pos = self._get_arc_pos(min(self.t, 1.0))
        
        # Kalkulasi velocity untuk dibaca oleh agen PPO
        if dt > 0:
            self.velocity = (pos - self.last_pos) / dt
        self.last_pos = Vec3(pos)
        
        self._set_pos(pos)

        if self.t >= 1.0:
            self.destroy()
            spawn_explosion(pos, color.red, 6.0)
            return 'hit'
        return Vec3(pos)

    def destroy(self):
        self.alive = False
        if self.body: destroy(self.body)

# ──────────────────── PPO RL INTERCEPT MISSILE ─────────────────────
class RLInterceptMissile:
    def __init__(self, target_atk, start_pos):
        self.target = target_atk
        self.pos = Vec3(start_pos.x, 10, start_pos.z)
        self.speed = cfg.blue_missile_speed
        self.alive = True
        
        self.current_dir = Vec3(0, 1, 0).normalized() # Menghadap atas saat meluncur
        self.velocity = self.current_dir * self.speed
        self.max_turn_rate = 3.0 # Radian per detik
        
        self.body = Entity(model='cube', color=color.cyan, scale=(0.8, 0.8, 2.5))
        self.body.position = self.pos
        
        # Visualisasi "Lidar" ke target
        self.lidar_line = Entity(model=Mesh(vertices=[self.pos, self.pos], mode='line', thickness=2), color=color.rgba(0, 255, 255, 100))

        # RL Metrics
        self.cumulative_reward = 0.0
        self.prev_distance = (self.target.body.position - self.pos).length() if self.target else 0

    def get_state(self):
        """ Observasi environment (Input ke PPO) """
        if not self.target or not self.target.alive:
            return np.zeros(9)
            
        target_pos = self.target.body.position
        target_vel = self.target.velocity
        
        # Relatif Posisi (Normalisasi kasar)
        rel_pos = (target_pos - self.pos) / 1000.0
        
        # Relatif Velocity (Normalisasi kasar)
        rel_vel = (target_vel - self.velocity) / 200.0
        
        # Jarak tersisa
        dist = np.array([(target_pos - self.pos).length() / 1000.0])
        
        # Array State: [rx, ry, rz, rvx, rvy, rvz, mx, my, mz, dist]
        state_array = np.concatenate([
            [rel_pos.x, rel_pos.y, rel_pos.z],
            [rel_vel.x, rel_vel.y, rel_vel.z],
            [self.current_dir.x, self.current_dir.y, self.current_dir.z]
        ])
        return state_array

    def compute_reward(self):
        """ Pembentukan Reward (Reward Shaping) """
        if not self.target or not self.target.alive: return 0.0
        
        current_distance = (self.target.body.position - self.pos).length()
        
        # 1. Reward mendekati target (Dense Reward)
        dist_reward = (self.prev_distance - current_distance) * 0.1
        self.prev_distance = current_distance
        
        reward = dist_reward
        
        # 2. Sparse Rewards (Kondisi Terminal)
        if current_distance < 10.0:
            reward += 100.0 # Berhasil Intersep!
        elif self.pos.y <= 0:
            reward -= 50.0  # Menabrak tanah
            
        return reward

    def apply_action(self, action, dt):
        """ 
        Menerjemahkan aksi dari PPO ke pergerakan fisik.
        action adalah array/list 2 nilai kontinu [-1.0, 1.0]
        action[0] = Pitch (Angguk), action[1] = Yaw (Geleng)
        """
        pitch_cmd = float(action[0]) * self.max_turn_rate * dt
        yaw_cmd = float(action[1]) * self.max_turn_rate * dt

        # Terapkan rotasi vektor berdasarkan aksi PPO
        right = self.current_dir.cross(Vec3(0,1,0))
        if right.length() == 0: right = Vec3(1,0,0)
        up = right.cross(self.current_dir)
        
        new_dir = (self.current_dir + (up * pitch_cmd) + (right * yaw_cmd)).normalized()
        self.current_dir = new_dir
        self.velocity = self.current_dir * self.speed

    def advance(self, action, dt):
        if not self.alive: return None
        
        # Eksekusi aksi dari PPO
        self.apply_action(action, dt)
        
        # Update Fisika
        self.pos += self.velocity * dt
        self.body.position = self.pos
        self.body.look_at(self.pos + self.current_dir)
        
        # Update Visual Lidar
        if self.target and self.target.alive:
            self.lidar_line.model.vertices = [self.pos, self.target.body.position]
            self.lidar_line.model.generate()

        # Hitung Reward
        reward = self.compute_reward()
        self.cumulative_reward += reward
        hud_reward.text = f"Reward: {self.cumulative_reward:.2f}"

        # Cek Kondisi Terminal
        if not self.target or not self.target.alive:
            self.destroy()
            return 'miss'
            
        current_distance = (self.target.body.position - self.pos).length()
        if current_distance < 10.0:
            return 'intercept'
            
        if self.pos.y <= 0 or self.pos.length() > 5000:
            self.destroy()
            return 'crash'

        return Vec3(self.pos)

    def destroy(self):
        self.alive = False
        if self.body: destroy(self.body)
        if self.lidar_line: destroy(self.lidar_line)

# ──────────────────────── PPO AGENT (INFERENCE) ──────────────────

MODEL_PATH = "ppo_missile_model_4.zip"

try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError
    print(f"Memuat model dari: {MODEL_PATH}")
    ppo_model = PPO.load(MODEL_PATH)
    hud_action.color = color.green
    hud_action.text = "Model PPO berhasil dimuat!"
except FileNotFoundError:
    print(f"ERROR: File model '{MODEL_PATH}' tidak ditemukan.")
    print("Silakan jalankan 'train.py' terlebih dahulu untuk melatih dan membuat model.")
    ppo_model = None # Gunakan None untuk menandakan model tidak ada
    hud_action.color = color.red
    hud_action.text = "MODEL TIDAK DITEMUKAN. Jalankan train.py"

# ─────────────────────────── UPDATE ──────────────────────────────
def update():
    dt = time.dt * cfg.time_scale
    # ─────────────────────────── UPDATE ──────────────────────────────
    if held_keys['right mouse']:
        camera.rotation_y += mouse.velocity.x * 150
        camera.rotation_x -= mouse.velocity.y * 150
        camera.rotation_x = clamp(camera.rotation_x, -90, 90)

    speed = 100 * time.dt
    if held_keys['shift']: speed *= 4  # Sprint

    if held_keys['w']: camera.position += camera.forward * speed
    if held_keys['s']: camera.position -= camera.forward * speed
    if held_keys['a']: camera.position -= camera.right * speed
    if held_keys['d']: camera.position += camera.right * speed
    if held_keys['q']: camera.position -= camera.up * speed
    if held_keys['e']: camera.position += camera.up * speed


    dt = time.dt
    if state.paused: return

    # Spawn Red Attack Missile
    state.attack_timer += dt
    if state.attack_timer >= cfg.red_fire_interval:
        state.attack_timer = 0.0
        state.attack_missiles.append(AttackMissile())

    # Update Attack Missiles
    for m in list(state.attack_missiles):
        if m.advance(dt) in ('hit', None):
            state.attack_missiles.remove(m)

    # Trigger PPO Interceptors
    all_threats = [m for m in state.attack_missiles if m.alive]
    blue_threats = [m for m in all_threats if (m.body.position - cfg.blue_pos).length() <= cfg.defender_detect_radius]
    
    # List target yang sedang dikejar (agar tidak double intercept pada target yang sama)
    active_targets = [im.target for im in state.intercept_missiles if im.alive]

    # Spawn interseptor untuk SETIAP ancaman baru yang belum di-handle (Multi-Targeting)
    for threat in blue_threats:
        if threat not in active_targets:
            state.intercept_missiles.append(RLInterceptMissile(threat, cfg.blue_pos))
            active_targets.append(threat)

    # Update PPO Interceptors
    for im in list(state.intercept_missiles):
        # 1. Observasi (Get State)
        current_state = im.get_state()
        
        # 2. Pilih Aksi (Predict via Model PPO)
        if ppo_model:
            action, _ = ppo_model.predict(current_state, deterministic=True)
            hud_action.text = f"Action: [{action[0]:.2f}, {action[1]:.2f}]"
        else:
            # Jika model tidak ada, jangan lakukan apa-apa
            action = [0, 0]
        
        # 3. Lakukan Aksi di Environment (Step)
        res = im.advance(action, dt)
        
        # Proses learning sudah tidak ada di sini, hanya inference.

        # 4. Tangani hasil
        if res == 'intercept':
            pos = Vec3(im.target.body.position)
            im.target.destroy()
            if im.target in state.attack_missiles: state.attack_missiles.remove(im.target)
            im.destroy()
            state.intercept_missiles.remove(im)
            spawn_explosion(pos, color.cyan, 5.0)
        elif res in ('miss', 'crash', None):
            state.intercept_missiles.remove(im)

    # Animate explosions
    for exp in list(state.explosions):
        exp['timer'] += dt
        prog = exp['timer'] / exp['dur']
        s = exp['size'] * math.sin(math.pi * prog)
        try:
            exp['e'].scale = s; exp['e2'].scale = s * 0.55
            a = int(200 * (1 - prog))
            exp['e'].color = color.rgba(*exp['e'].color.rgb[:3], a)
        except: pass
        if prog >= 1.0:
            try: destroy(exp['e']); destroy(exp['e2'])
            except: pass
            state.explosions.remove(exp)

def input(key):
    if key == 'escape': application.quit()
    elif key == 'p': state.paused = not state.paused
    elif key == 'up arrow': cfg.time_scale += 0.5
    elif key == 'down arrow': cfg.time_scale = max(0.1, cfg.time_scale - 0.5)

app.run()