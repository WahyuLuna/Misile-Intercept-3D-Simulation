"""
╔══════════════════════════════════════════════════════════════╗
║      MISSILE INTERCEPT SIMULATION v2 - Visual Fixed          ║
║      Attacker (RED) vs Defenders (BLUE & GREEN)              ║
╚══════════════════════════════════════════════════════════════╝
Controls:
    P        = Pause / Resume
    R        = Reset
    ESC      = Quit
    RMB drag = Rotate Camera
    Scroll   = Zoom In/Out
"""

from ursina import *
import math
import random

# ─────────────────────────── APP INIT ────────────────────────────
app = Ursina(title='Missile Intercept Simulation', borderless=False)

# ───────────────────── ENVIRONMENT (dari rocket_ur2) ─────────────
# Ground — texture 'grass' seperti di rocket_ur2, skala besar
ground = Entity(
    model='plane',
    scale=9000,
    texture='grass',
    color=color.gray,   # Sesuai rocket_ur2.py
)

# Sky langsung dari ursina built-in (rocket_ur2 style)
Sky()

# ──────────────────────────── SETTINGS ───────────────────────────
class Settings:
    attacker_fire_interval  = 3.0
    red_team_active         = True
    yellow_team_active      = False
    yellow_fire_interval    = 5.0
    blue_fire_interval      = 2.0
    green_fire_interval     = 2.0
    attacker_missile_speed  = 100.0   # satuan/s (sama skala rocket_ur2)
    attacker_missile_wobble = 10    # Diperbesar untuk gerakan lebih agresif
    yellow_missile_speed    = 120.0
    yellow_split_threshold  = 0.5     # Titik pecah misil (0.0 - 1.0)
    blue_missile_speed      = 80.0
    green_missile_speed     = 80.0
    defender_detect_radius  = 500.0 #radius deteksi pertahanan
    intercept_prediction_dist = defender_detect_radius-0.
    angle_corner            = 10  # sudut belok intercept
    selfdestruction         = 3
    building                = 200  #jumlah bangunan
    defender_missile_lifetime = 10.0
    gravity                 = 9.8
    arc_height              = 150.0
    attacker_pos = Vec3(-4000, 0, 0)  # Jarak diperluas
    yellow_pos   = Vec3(-4100, 0, 0)
    blue_pos     = Vec3( 800, 0, -2200) # Tim Biru
    green_pos    = Vec3( 800, 0,  2200) # Tim Hijau (Baru)

cfg = Settings()

# ──────────────────────────── GAME STATE ─────────────────────────
class GameState:
    attacker_score    = 0
    blue_score        = 0
    green_score       = 0
    yellow_score      = 0
    blue_destroyed    = 0
    green_destroyed   = 0
    attacker_fired    = 0
    yellow_fired      = 0
    blue_fired        = 0
    green_fired       = 0
    paused            = False
    attack_timer      = 0.0
    yellow_attack_timer = 0.0
    blue_defend_timer = 0.0
    green_defend_timer= 0.0
    attack_missiles   = []
    yellow_missiles   = []
    sub_munitions     = []
    intercept_missiles= []
    explosions        = []
    targets           = []

state = GameState()

# ────────────────────── ATTACKER BASE (RED) ──────────────────────
# Gaya rocket_ur2: cube besar + warna solid tanpa texture
atk_base = Entity(
    model='cube',
    color=color.red,
    scale=(8, 2, 8),
    position=cfg.attacker_pos + Vec3(0, 1, 0),
)
atk_tower = Entity(
    model='cube',
    color=color.rgb(200, 30, 30),
    scale=(3, 6, 3),
    position=cfg.attacker_pos + Vec3(0, 5, 0),
)
atk_barrel = Entity(
    model='cube',
    color=color.rgb(220, 60, 60),
    scale=(1, 1, 5),
    position=cfg.attacker_pos + Vec3(0, 9, 3),
    rotation=(-35, 0, 0),
)
# Flag merah kecil
atk_flag = Entity(
    model='cube',
    color=color.red,
    scale=(0.3, 3, 0.3),
    position=cfg.attacker_pos + Vec3(-3, 10, -3),
)
atk_flag_cloth = Entity(
    model='cube',
    color=color.red,
    scale=(2, 1.2, 0.1),
    position=cfg.attacker_pos + Vec3(-2, 11.5, -3),
)

# ────────────────────── DEFENDER BASE (BLUE) ─────────────────────
blue_base = Entity(
    model='cube',
    color=color.blue,
    scale=(8, 2, 8),
    position=cfg.blue_pos + Vec3(0, 1, 0),
)
blue_tower = Entity(
    model='cube',
    color=color.rgb(30, 60, 200),
    scale=(3, 6, 3),
    position=cfg.blue_pos + Vec3(0, 5, 0),
)
blue_barrel = Entity(
    model='cube',
    color=color.rgb(60, 100, 220),
    scale=(1, 1, 5),
    position=cfg.blue_pos + Vec3(0, 9, -3),
    rotation=(35, 0, 0),
)
blue_flag = Entity(
    model='cube',
    color=color.blue,
    scale=(0.3, 3, 0.3),
    position=cfg.blue_pos + Vec3(3, 10, 3),
)
blue_flag_cloth = Entity(
    model='cube',
    color=color.rgb(50, 100, 255),
    scale=(2, 1.2, 0.1),
    position=cfg.blue_pos + Vec3(4, 11.5, 3),
)

# ────────────────────── DEFENDER BASE (GREEN) ────────────────────
green_base = Entity(
    model='cube',
    color=color.green,
    scale=(8, 2, 8),
    position=cfg.green_pos + Vec3(0, 1, 0),
)
green_tower = Entity(
    model='cube',
    color=color.rgb(30, 200, 60),
    scale=(3, 6, 3),
    position=cfg.green_pos + Vec3(0, 5, 0),
)
green_barrel = Entity(
    model='cube',
    color=color.rgb(60, 220, 100),
    scale=(1, 1, 5),
    position=cfg.green_pos + Vec3(0, 9, -3),
    rotation=(35, 0, 0),
)
green_flag = Entity(
    model='cube',
    color=color.green,
    scale=(0.3, 3, 0.3),
    position=cfg.green_pos + Vec3(3, 10, 3),
)
green_flag_cloth = Entity(
    model='cube',
    color=color.rgb(50, 255, 100),
    scale=(2, 1.2, 0.1),
    position=cfg.green_pos + Vec3(4, 11.5, 3),
)

# ─────────────────── ATTACKER BASE (YELLOW - NEW) ────────────────
yellow_base = Entity(
    model='cube',
    color=color.yellow,
    scale=(8, 2, 8),
    position=cfg.yellow_pos + Vec3(0, 1, 0),
)
yellow_tower = Entity(
    model='cube',
    color=color.rgb(255, 255, 0),
    scale=(3, 6, 3),
    position=cfg.yellow_pos + Vec3(0, 5, 0),
)
Text(parent=camera.ui, text='[Y] ATTACKER\nYELLOW FORCE',
     position=(-0.8,0.465), scale=0.82, color=color.white, origin=(0,0))

# ────────────────────── EXTRA TARGETS (BLUE & GREEN) ─────────────
blue_base.is_base = True
green_base.is_base = True
blue_base.team = 'blue'
green_base.team = 'green'
state.targets = [blue_base, green_base]

# Target Biru
for _ in range(cfg.building):
    # building_range = cfg.defender_detect_radius
    tx = cfg.blue_pos.x + random.uniform(-1000, 1000)
    tz = cfg.blue_pos.z + random.uniform(-1000, 1000)
    th = random.uniform(5, 20) # Tinggi bervariasi bangunan
    t_obj = Entity(
        model='cube', color=color.gray,
        scale=(8, th, 8), position=(tx, th/2, tz)
    )
    t_obj.is_base = False
    t_obj.center_pos = cfg.blue_pos
    t_obj.team = 'blue'
    state.targets.append(t_obj)

# Target Hijau
for _ in range(cfg.building):
    tx = cfg.green_pos.x + random.uniform(-1000, 1000)
    tz = cfg.green_pos.z + random.uniform(-1000, 1000)
    th = random.uniform(5, 20)
    t_obj = Entity(
        model='cube', color=color.gray,
        scale=(8, th, 8), position=(tx, th/2, tz)
    )
    t_obj.is_base = False
    t_obj.center_pos = cfg.green_pos
    t_obj.team = 'green'
    state.targets.append(t_obj)

# ──────────── DETECTION DOMES ────────────────────────────────────
dome_blue = Entity(
    model    = 'sphere',
    position = cfg.blue_pos,
    scale    = cfg.defender_detect_radius * 2,
    color    = color.rgba(0, 0, 255, 60),
    wireframe= True,                      # Kunci: hanya garis, tidak ada fill
)
dome_green = Entity(
    model    = 'sphere',
    position = cfg.green_pos,
    scale    = cfg.defender_detect_radius * 2,
    color    = color.rgba(0, 255, 0, 60),
    wireframe= True,
)
dome_red = Entity(
    model    = 'sphere',
    position = cfg.attacker_pos,
    scale    = 400,
    color    = color.red,
    wireframe= True,
)
# ──────────────────────── CAMERA SETUP ───────────────────────────
camera.position = (0, 100, -250)
camera.rotation = (25, 0, 0)

# ───────────────────────── HUD / UI ──────────────────────────────
# Latar judul (desain baru)

Text(parent=camera.ui, text='[ MISSILE INTERCEPT SIMULATION ]',
     position=(0, 2), scale=1.25, color=color.yellow, origin=(0,0))

stats_ui = Text(parent=camera.ui, text='', position=(-0.88, 0.45), scale=0.75,
                color=color.white, origin=(-0.5, 0.5), unlit=True, line_height=1)


Text(parent=camera.ui,
     text='[P] Pause  [R] Reset  [ESC] Quit  |  WASD=Fly  RMB=Look  Shift=Fast',
     position=(0,-0.485), scale=0.72,
     color=color.rgba(210,210,210,180), origin=(0,0))

# Label Tim

Text(parent=camera.ui, text='[A]  ATTACKER\nRED FORCE',
     position=(-0.58,0.465), scale=0.82, color=color.white, origin=(0,0))


Text(parent=camera.ui, text='[B]  DEFENDER\nBLUE FORCE',
     position=(0.40,0.465), scale=0.82, color=color.white, origin=(0,0))


Text(parent=camera.ui, text='[G]  DEFENDER\nGREEN FORCE',
     position=(0.65,0.465), scale=0.82, color=color.white, origin=(0,0))

# ──────────────────────── CONTROL PANEL (NEW) ──────────────────
def apply_settings():
    """ Ambil nilai dari slider dan terapkan ke config serta visual. """
    cfg.arc_height = arc_slider.value
    cfg.defender_detect_radius = defender_detect_radius.value
    cfg.attacker_missile_speed = atk_speed_slider.value
    cfg.attacker_missile_wobble = attacker_missile_wobble.value
    cfg.blue_missile_speed = blue_speed_slider.value
    cfg.green_missile_speed = green_speed_slider.value
    cfg.attacker_fire_interval = atk_fire_slider.value
    cfg.yellow_fire_interval = yellow_fire_slider.value
    cfg.blue_fire_interval = blue_fire_slider.value
    cfg.green_fire_interval = green_fire_slider.value
    cfg.red_team_active = bool(red_team_slider.value)
    cfg.yellow_team_active = bool(yellow_team_slider.value)
    cfg.yellow_missile_speed = yellow_speed_slider.value
    cfg.yellow_split_threshold = yellow_split_slider.value
    cfg.defender_missile_lifetime = defender_missile_lifetime.value
    cfg.intercept_prediction_dist = predict_dist_slider.value
    cfg.angle_corner = angle_corner.value
    cfg.selfdestruction = selfdestruction.value
    # cfg.building = building.value
    
    # --- PERBAIKAN: Update Skala Visual Dome ---
    # Skala dikali 2 karena radius adalah setengah dari diameter (scale)
    dome_blue.scale = cfg.defender_detect_radius * 2
    dome_green.scale = cfg.defender_detect_radius * 2
    
    control_panel.enabled = False 
    print(f"Settings Applied: Detect Radius={cfg.defender_detect_radius}")

# ──────────────────────── CUSTOM CONTROL PANEL UI ────────────────
control_panel = Entity(parent=camera.ui, enabled=False, z=-5)
# bg = Entity(parent=control_panel, model='quad', scale=(1.4, 0.9), color=color.rgba(0,0,0,220), position=(0,0.05))
Text(parent=control_panel, text='CONTROLS [E]', position=(0, 0.42), origin=(0,0), scale=1.5, color=color.yellow)

# Layout Constants
col1_x = -0.35
col2_x = 0.35
start_y = 0.30
gap_y = 0.08
sl_scale = 0.75

# --- LEFT COLUMN (RED & BLUE) ---
red_team_slider = Slider(min=0, max=1, default=int(cfg.red_team_active), step=1, text='Red Team Active', parent=control_panel, position=(col1_x, start_y), scale=sl_scale)
arc_slider = Slider(min=10, max=2500, default=cfg.arc_height, step=1, text='Arc Height', parent=control_panel, position=(col1_x, start_y - gap_y), scale=sl_scale)
atk_speed_slider = Slider(min=5, max=1500, default=cfg.attacker_missile_speed, step=1, text='Red Speed', parent=control_panel, position=(col1_x, start_y - 2*gap_y), scale=sl_scale)
attacker_missile_wobble = Slider(min=0, max=100, default=cfg.attacker_missile_wobble, step=1, text='missil wobble', parent=control_panel, position=(col1_x, start_y - 3*gap_y), scale=sl_scale)
atk_fire_slider = Slider(min=0.1, max=10, default=cfg.attacker_fire_interval, step=0.1, text='Red Interval', parent=control_panel, position=(col1_x, start_y - 4*gap_y), scale=sl_scale)
blue_speed_slider = Slider(min=50, max=1000, default=cfg.blue_missile_speed, step=1, text='Blue Speed', parent=control_panel, position=(col1_x, start_y - 5*gap_y), scale=sl_scale)
blue_fire_slider = Slider(min=0.1, max=10, default=cfg.blue_fire_interval, step=0.1, text='Blue Interval', parent=control_panel, position=(col1_x, start_y - 6*gap_y), scale=sl_scale)
defender_missile_lifetime = Slider(min=1, max=100, default=cfg.defender_missile_lifetime, step=1, text='Defender Missile Lifetime', parent=control_panel, position=(col1_x, start_y - 7*gap_y), scale=sl_scale)
selfdestruction = Slider(min=1, max=100, default=cfg.selfdestruction, step=1, text='Self Destruction', parent=control_panel, position=(col1_x, start_y - 8*gap_y), scale=sl_scale)

# --- RIGHT COLUMN (YELLOW & GREEN) ---
yellow_team_slider = Slider(min=0, max=1, default=int(cfg.yellow_team_active), step=1, text='Yellow Team Active', parent=control_panel, position=(col2_x, start_y), scale=sl_scale)
yellow_speed_slider = Slider(min=50, max=300, default=cfg.yellow_missile_speed, step=1, text='Yellow Speed', parent=control_panel, position=(col2_x, start_y - gap_y), scale=sl_scale)
yellow_fire_slider = Slider(min=0.5, max=10, default=cfg.yellow_fire_interval, step=0.1, text='Yellow Interval', parent=control_panel, position=(col2_x, start_y - 2*gap_y), scale=sl_scale)
yellow_split_slider = Slider(min=0.1, max=0.9, default=cfg.yellow_split_threshold, step=0.05, text='Yellow Split (0-1)', parent=control_panel, position=(col2_x, start_y - 3*gap_y), scale=sl_scale)
green_speed_slider = Slider(min=50, max=1000, default=cfg.green_missile_speed, step=1, text='Green Speed', parent=control_panel, position=(col2_x, start_y - 4*gap_y), scale=sl_scale)
green_fire_slider = Slider(min=0.1, max=10, default=cfg.green_fire_interval, step=0.1, text='Green Interval', parent=control_panel, position=(col2_x, start_y - 5*gap_y), scale=sl_scale)
defender_detect_radius = Slider(
    min=100, 
    max=3000, # Dinaikkan agar bisa mencakup area lebih luas
    default=cfg.defender_detect_radius, 
    step=10, 
    text='Detect Radius', 
    parent=control_panel, 
    position=(col2_x, start_y - 6*gap_y), 
    scale=sl_scale
)
predict_dist_slider = Slider(
    min=0, 
    max=1500, 
    default=cfg.intercept_prediction_dist, 
    step=10, 
    text='Prediction Dist', 
    parent=control_panel, 
    position=(col2_x, start_y - 7*gap_y), # Sesuaikan posisi y-nya
    scale=sl_scale
)
angle_corner = Slider(min=1, max=45, default=cfg.angle_corner, step=0.1, text='Angle Corner', parent=control_panel, position=(col2_x, start_y - 8*gap_y), scale=sl_scale)

# building = Slider(min=10, max=100, default=cfg.building, step=0.1, text='Building Amount', parent=control_panel, position=(col2_x, start_y - 7*gap_y), scale=sl_scale)

# Apply Button

Button('Apply Changes', parent=control_panel, color=color.azure, scale=(0.25, 0.08), position=(0, -0.4), on_click=apply_settings)

# ──────────────────────── EXPLOSION ──────────────────────────────
def spawn_explosion(pos, clr=color.orange, size=4.0):
    e1 = Entity(model='sphere', position=pos,
                color=color.rgba(*clr.rgb, 200), scale=0.3)
    e2 = Entity(model='sphere', position=pos,
                color=color.rgba(255, 240, 80, 150), scale=0.2)
    state.explosions.append({'e': e1, 'e2': e2, 'timer': 0.0, 'dur': 0.6, 'size': size})

# ──────────────────────── RESPAWN TARGET ─────────────────────────
def respawn_target(t_obj):
    # Pindahkan target ke posisi acak baru dalam radius timnya
    tx = t_obj.center_pos.x + random.uniform(-100, 100)
    tz = t_obj.center_pos.z + random.uniform(-100, 100)
    th = random.uniform(5, 15)
    t_obj.position = (tx, th/2, tz)
    t_obj.scale_y  = th

# ────────────────── YELLOW SUB-MUNITION (NEW) ────────────────────
class YellowSubmunition:
    def __init__(self, start_pos, start_vel):
        self.pos = Vec3(start_pos)
        self.vel = Vec3(start_vel)
        self.alive = True
        self.body = Entity(
            model='sphere',
            color=color.yellow,
            scale=0.7,
            position=self.pos
        )

    def advance(self, dt):
        if not self.alive:
            return None
        
        # Apply gravity
        self.vel.y -= cfg.gravity * dt
        self.pos += self.vel * dt
        self.body.position = self.pos

        if self.pos.y <= 0:
            self.destroy()
            spawn_explosion(self.pos, color.yellow, 3.0)
            
            # Check for hits on any target
            for target_ent in state.targets:
                if (self.pos - target_ent.position).length() < 15.0:
                    state.yellow_score += 1 # Score one point per submunition hit
                    if not target_ent.is_base:
                        respawn_target(target_ent)
                        if target_ent.team == 'blue':
                            state.blue_destroyed += 1
                        elif target_ent.team == 'green':
                            state.green_destroyed += 1
                    # Break to prevent one submunition from scoring on multiple targets
                    break 
            return 'hit'
        return Vec3(self.pos)

    def destroy(self):
        self.alive = False
        destroy(self.body)

# ─────────────────── YELLOW ATTACK MISSILE (NEW) ─────────────────
class YellowAttackMissile:
    def __init__(self):
        self.origin = Vec3(cfg.yellow_pos.x, 10, cfg.yellow_pos.z)
        self.target_ent = random.choice(state.targets)
        self.target = self.target_ent.position
        self.t = 0.0
        self.dist = (self.target - self.origin).length()
        self.speed = cfg.yellow_missile_speed
        self.alive = True
        self.split_done = False

        self.body = Entity(model='sphere', color=color.yellow, scale=1.8)
        self.body.position = self.origin

    def _get_arc_pos(self, t):
        p = lerp(self.origin, self.target, t)
        p.y += cfg.arc_height * math.sin(math.pi * t)
        return p

    def advance(self, dt):
        if not self.alive or dt == 0: return None

        # Hitung perubahan waktu normalisasi untuk frame ini
        delta_t_norm = (self.speed / max(self.dist, 1.0)) * dt
        t_before = self.t
        self.t += delta_t_norm

        pos = self._get_arc_pos(min(self.t, 1.0))
        self.body.position = pos

        # Cek jika misil baru saja melewati puncak busur (t=0.5)
        if t_before < cfg.yellow_split_threshold and self.t >= cfg.yellow_split_threshold and not self.split_done:
            self.split_done = True
            # Hitung kecepatan sesaat berdasarkan posisi frame sebelumnya dan sekarang
            pos_before = self._get_arc_pos(t_before)
            current_vel = (pos - pos_before) / dt
            for _ in range(5):
                spread_vel = Vec3(random.uniform(-20, 20), 0, random.uniform(-20, 20))
                state.sub_munitions.append(YellowSubmunition(self.body.position, current_vel + spread_vel))
            self.destroy()
            return 'split'
        if self.t >= 1.0: self.destroy(); return None
        return Vec3(pos)

    def destroy(self):
        self.alive = False
        destroy(self.body)

# ──────────────────────── ATTACK MISSILE ─────────────────────────
class AttackMissile:
    def __init__(self):
        self.origin = Vec3(cfg.attacker_pos.x, 10, cfg.attacker_pos.z)
        # Pilih target acak dari daftar (Markas atau Gedung)
        self.target_ent = random.choice(state.targets)
        self.target = self.target_ent.position + Vec3(random.uniform(-3,3), 0, random.uniform(-3,3))
        self.t      = 0.0
        self.dist   = (self.target - self.origin).length()
        self.speed  = cfg.attacker_missile_speed
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_freq  = random.uniform(2.5, 4.0) # Frekuensi lebih tinggi
        self.alive  = True

        # Badan misil — sphere seperti rocket_ur2
        self.body = Entity(
            model='sphere',
            color=color.red,
            scale=1.5,
        )
        # Trail spheres
        self.trail = []
        for k in range(8):
            tr = Entity(model='sphere', scale=0.8,
                        color=color.rgba(255, 160, 40, 130))
            self.trail.append({'e': tr, 'pos': Vec3(self.origin)})

        self._set_pos(self.origin)

    def _get_arc_pos(self, t):
        p = lerp(self.origin, self.target, t)
        p.y += cfg.arc_height * math.sin(math.pi * t)
        
        if t > 0.5:
            ramp = (t - 0.5) * 2.0
            side = cfg.attacker_missile_wobble * math.sin(
                self.wobble_phase + self.wobble_freq * t * math.pi * 4)
            p.z += side * ramp
        return p

    def _set_pos(self, pos):
        self.body.position = pos
        for i in range(len(self.trail) - 1, 0, -1):
            self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
        self.trail[0]['pos'] = Vec3(pos)
        for i, tr in enumerate(self.trail):
            tr['e'].position = tr['pos']
            a = max(0, 130 - i * 18)
            tr['e'].color = color.rgba(255, max(40, 160 - i*15), 40, a)
            tr['e'].scale = max(0.2, 0.8 - i * 0.08)

    def advance(self, dt):
        if not self.alive:
            return None
        self.t += (self.speed / max(self.dist, 1.0)) * dt
        pos = self._get_arc_pos(min(self.t, 1.0))
        self._set_pos(pos)

        if self.t >= 1.0:
            hit_pos = self.body.position
            self.destroy()
            state.attacker_score += 1
            spawn_explosion(hit_pos, color.orange, 5.0)
            
            # Cek jika target adalah gedung random dan jarak ledakan cukup dekat (kena)
            if not self.target_ent.is_base:
                if (hit_pos - self.target_ent.position).length() < 15.0:
                    respawn_target(self.target_ent)
                    if self.target_ent.team == 'blue':
                        state.blue_destroyed += 1
                    elif self.target_ent.team == 'green':
                        state.green_destroyed += 1
            return 'hit'
        return Vec3(pos)

    def destroy(self):
        self.alive = False
        destroy(self.body)
        for tr in self.trail:
            destroy(tr['e'])

# ──────────────────── REALISTIC SMART INTERCEPT MISSILE (TWO Phase) ──────────────────────────
class InterceptMissile:
    def __init__(self, target_atk, start_pos, team_color, team_name):
        self.target   = target_atk
        self.pos      = Vec3(start_pos.x, 10, start_pos.z)
        self.team     = team_name
        
        self.speed = cfg.blue_missile_speed if self.team == 'blue' else cfg.green_missile_speed
        self.lifetime = cfg.defender_missile_lifetime
        self.alive    = True

        # Logika Gerakan Realistik
        self.current_dir = Vec3(0, 1, 0).normalized()
        self.turn_speed = 2.8 # gerakan berbelok max 4 min 0.1

        # Timer Penghancuran Otomatis (Fase 2)
        self.intercept_phase_started = False
        self.intercept_timer = cfg.selfdestruction # Batas waktu detik setelah kalkulasi dimulai

        self.body = Entity(
            model='cube',
            color=color.yellow,
            scale=(0.8, 0.8, 2.5),
        )
        self.trail = []
        for _ in range(6):
            tr = Entity(model='sphere', scale=0.5, color=color.yellow)
            self.trail.append({'e': tr, 'pos': Vec3(self.pos)})

        self.body.position = self.pos

    def advance(self, dt):
        if not self.alive or not self.target or not self.target.alive:
            if self.alive: self.destroy()
            return None
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.destroy()
            return None

        target_pos = Vec3(self.target.body.position)
        distance_to_target = (target_pos - self.pos).length()
        
        # --- LOGIKA TARGET DIRECTION ---
        if distance_to_target > cfg.intercept_prediction_dist:
            # FASE 1: Pure Pursuit
            ideal_dir = (target_pos - self.pos).normalized()
        else:
            # FASE 2: Predictive Interception Dimulai
            if not self.intercept_phase_started:
                self.intercept_phase_started = True # Tandai awal kalkulasi
            
            # Jalankan Timer 3 Detik
            self.intercept_timer -= dt
            if self.intercept_timer <= 0:
                spawn_explosion(self.pos, color.yellow, size=2.0) # Ledakan gagal
                self.destroy()
                return None

            # Kalkulasi Titik Temu
            # t_future = min(self.target.t + 0.02, 1.0)
            time_to_reach = distance_to_target / max(self.speed, 1.0)
            prediction_lookahead = clamp(time_to_reach / 100, 0.005, 0.03) 
            t_future = min(self.target.t + prediction_lookahead, 1.0)
            pos_future = self.target._get_arc_pos(t_future)
            target_vel = (pos_future - target_pos) / max(dt, 0.001)
            time_to_reach = distance_to_target / max(self.speed, 1.0)
            intercept_point = target_pos + (target_vel * time_to_reach)
            ideal_dir = (intercept_point - self.pos).normalized()

        # --- PEMBATASAN SUDUT & ROTASI (REALISTIK) ---
        angle_rad = math.acos(clamp(self.current_dir.dot(ideal_dir), -1, 1))
        angle_deg = math.degrees(angle_rad)

        if angle_deg > cfg.angle_corner: # Batas sudut belok derajat
            t_limit = cfg.angle_corner / angle_deg
            actual_target_dir = lerp(self.current_dir, ideal_dir, t_limit).normalized()
        else:
            actual_target_dir = ideal_dir

        self.current_dir = lerp(self.current_dir, actual_target_dir, dt * self.turn_speed).normalized()

        # --- EKSEKUSI POSISI ---
        self.pos += self.current_dir * self.speed * dt
        self.pos.y = max(self.pos.y, 0.5)

        self.body.position = self.pos
        self.body.look_at(self.pos + self.current_dir)

        # Visual Trail
        for i in range(len(self.trail) - 1, 0, -1):
            self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
        self.trail[0]['pos'] = Vec3(self.pos)
        for i, tr in enumerate(self.trail):
            tr['e'].position = tr['pos']
            a = max(0, 110 - i * 20)
            tr['e'].color = color.rgba(self.body.color.r*255, self.body.color.g*255, self.body.color.b*255, a)
            tr['e'].scale = max(0.1, 0.5 - i * 0.06)

        if distance_to_target < 5.0:
            return 'intercept'
        
        return Vec3(self.pos)

    def destroy(self):
        self.alive = False
        if self.body:
            destroy(self.body)
        for tr in self.trail:
            destroy(tr['e'])

# # ──────────────────── INTERCEPT MISSILE (V1)──────────────────────────
# class InterceptMissile:
#     def __init__(self, target_atk: AttackMissile, start_pos, team_color, team_name):
#         self.target   = target_atk
#         self.pos      = Vec3(start_pos.x, 10, start_pos.z)
#         self.team     = team_name
#         # Tentukan kecepatan berdasarkan tim
#         if self.team == 'blue':
#             self.speed = cfg.blue_missile_speed
#         else: # green
#             self.speed = cfg.green_missile_speed
#         self.lifetime = cfg.defender_missile_lifetime
#         self.alive    = True

#         self.body = Entity(
#             model='cube',
#             color=color.yellow,
#             scale=(0.8, 0.8, 2.5),
#         )
#         self.trail = []
#         for _ in range(6):
#             tr = Entity(model='sphere', scale=0.5,
#                         color=color.yellow)
#             self.trail.append({'e': tr, 'pos': Vec3(self.pos)})

#         self.body.position = self.pos

#     def advance(self, dt):
#         if not self.alive:
#             return None
#         self.lifetime -= dt
#         if self.lifetime <= 0 or not self.target.alive:
#             self.destroy()
#             return None

#         tgt = Vec3(self.target.body.position)
#         direction = (tgt - self.pos).normalized()
#         self.pos += direction * self.speed * dt
#         self.pos.y = max(self.pos.y, 0.5)

#         self.body.position = self.pos
#         if direction.length() > 0.001:
#             self.body.look_at(self.pos + direction)

#         for i in range(len(self.trail) - 1, 0, -1):
#             self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
#         self.trail[0]['pos'] = Vec3(self.pos)
#         for i, tr in enumerate(self.trail):
#             tr['e'].position = tr['pos']
#             a = max(0, 110 - i * 20)
#             tr['e'].color = color.rgba(self.body.color.r*255, self.body.color.g*255, self.body.color.b*255, a)
#             tr['e'].scale = max(0.1, 0.5 - i * 0.06)

#         if (self.pos - tgt).length() < 3.0:
#             return 'intercept'
#         return Vec3(self.pos)

#     def destroy(self):
#         self.alive = False
#         destroy(self.body)
#         for tr in self.trail:
#             destroy(tr['e'])



# ─────────────────────────── RESET ───────────────────────────────
def reset_game():
    for m in list(state.attack_missiles):
        m.destroy()
    for m in list(state.yellow_missiles):
        m.destroy()
    for m in list(state.sub_munitions):
        m.destroy()
    for m in list(state.intercept_missiles):
        m.destroy()
    for exp in list(state.explosions):
        try:
            destroy(exp['e'])
            destroy(exp['e2'])
        except:
            pass
    state.attack_missiles.clear()
    state.yellow_missiles.clear()
    state.sub_munitions.clear()
    state.intercept_missiles.clear()
    state.explosions.clear()
    state.attacker_score = 0
    state.yellow_score   = 0
    state.blue_score     = 0
    state.green_score    = 0
    state.blue_destroyed = 0
    state.green_destroyed = 0
    state.attacker_fired = 0
    state.yellow_fired   = 0
    state.blue_fired     = 0
    state.green_fired    = 0
    state.attack_timer   = 0.0
    state.yellow_attack_timer = 0.0
    state.blue_defend_timer = 0.0
    state.green_defend_timer= 0.0

# ─────────────────────────── UPDATE ──────────────────────────────
def update():
    # ── Camera Fly Control (WASD + RMB) ──
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

    if state.paused:
        return

    dt = time.dt

    # ── Spawn attack missile (RED) ──
    if cfg.red_team_active:
        state.attack_timer += dt
        if state.attack_timer >= cfg.attacker_fire_interval:
            state.attack_timer = 0.0
            state.attack_missiles.append(AttackMissile())
            state.attacker_fired += 1

    # ── Spawn attack missile (YELLOW) ──
    if cfg.yellow_team_active:
        state.yellow_attack_timer += dt
        if state.yellow_attack_timer >= cfg.attacker_fire_interval:
            state.yellow_attack_timer = 0.0
            state.yellow_missiles.append(YellowAttackMissile())
            state.yellow_fired += 1

    # ── Advance attack missiles ──
    dead_a = []
    for m in state.attack_missiles:
        if not m.alive:
            dead_a.append(m); continue
        res = m.advance(dt)
        if res in ('hit', None):
            dead_a.append(m)
    for m in dead_a:
        if m in state.attack_missiles:
            state.attack_missiles.remove(m)

    # ── Advance yellow missiles ──
    dead_y = []
    for m in state.yellow_missiles:
        if not m.alive: dead_y.append(m); continue
        if m.advance(dt) in ('split', None): dead_y.append(m)
    for m in dead_y:
        if m in state.yellow_missiles: state.yellow_missiles.remove(m)

    # ── Advance sub-munitions ──
    dead_sub = []
    for m in state.sub_munitions:
        if not m.alive: dead_sub.append(m); continue
        if m.advance(dt) in ('hit', None): dead_sub.append(m)
    for m in dead_sub:
        if m in state.sub_munitions: state.sub_munitions.remove(m)


    # --- Combine all threats for defenders ---
    all_threats = [m for m in state.attack_missiles if m.alive] + \
                  [m for m in state.yellow_missiles if m.alive] + \
                  [m for m in state.sub_munitions if m.alive]

    # ── DEFENSE LOGIC (BLUE) ──
    blue_threats = [m for m in all_threats if
                    (m.body.position - cfg.blue_pos).length() <= cfg.defender_detect_radius]
    
    state.blue_defend_timer += dt
    if blue_threats and state.blue_defend_timer >= cfg.blue_fire_interval:
        state.blue_defend_timer = 0.0
        targeted = {im.target for im in state.intercept_missiles if im.alive}
        free     = [t for t in blue_threats if t not in targeted]
        tgt      = free[0] if free else blue_threats[0]
        state.intercept_missiles.append(
            InterceptMissile(tgt, cfg.blue_pos, color.blue, 'blue'))
        state.blue_fired += 1

    # ── DEFENSE LOGIC (GREEN) ──
    green_threats = [m for m in all_threats if
                     (m.body.position - cfg.green_pos).length() <= cfg.defender_detect_radius]
    
    state.green_defend_timer += dt
    if green_threats and state.green_defend_timer >= cfg.green_fire_interval:
        state.green_defend_timer = 0.0
        targeted = {im.target for im in state.intercept_missiles if im.alive}
        free     = [t for t in green_threats if t not in targeted]
        tgt      = free[0] if free else green_threats[0]
        state.intercept_missiles.append(
            InterceptMissile(tgt, cfg.green_pos, color.green, 'green'))
        state.green_fired += 1

    # ── Advance intercept missiles ──
    dead_i = []
    for im in state.intercept_missiles:
        if not im.alive:
            dead_i.append(im); continue
        res = im.advance(dt)
        if res == 'intercept':
            pos = Vec3(im.target.body.position)
            im.target.destroy()
            # Remove from any list it might be in
            for missile_list in [state.attack_missiles, state.yellow_missiles, state.sub_munitions]:
                if im.target in missile_list:
                    missile_list.remove(im.target)
            im.destroy()
            dead_i.append(im)
            if im.team == 'blue':
                state.blue_score += 1
            else:
                state.green_score += 1
            spawn_explosion(pos, im.body.color, 4.0)
        elif res is None:
            dead_i.append(im)
    for im in dead_i:
        if im in state.intercept_missiles:
            state.intercept_missiles.remove(im)

    # ── Animate explosions ──
    dead_exp = []
    for exp in state.explosions:
        exp['timer'] += dt
        prog = exp['timer'] / exp['dur']
        s    = exp['size'] * math.sin(math.pi * prog)
        try:
            exp['e'].scale  = s
            exp['e2'].scale = s * 0.55
            a = int(200 * (1 - prog))
            exp['e'].color  = color.rgba(255, 140, 40, a)
            exp['e2'].color = color.rgba(255, 240, 60, a)
        except:
            pass
        if prog >= 1.0:
            try:
                destroy(exp['e'])
                destroy(exp['e2'])
            except:
                pass
            dead_exp.append(exp)
    for e in dead_exp:
        if e in state.explosions:
            state.explosions.remove(e)

    # ── HUD ──
    atk_rate   = (state.attacker_score / state.attacker_fired * 100) if state.attacker_fired > 0 else 0.0
    blue_rate  = (state.blue_score / state.blue_fired * 100) if state.blue_fired > 0 else 0.0
    green_rate = (state.green_score / state.green_fired * 100) if state.green_fired > 0 else 0.0
    yellow_rate = (state.yellow_score / (state.yellow_fired * 5) * 100) if state.yellow_fired > 0 else 0.0

    stats_ui.text = (
        f'<red>RED TEAM (Attacker)\n<white>Fired: {state.attacker_fired}  |  Hits: {state.attacker_score}\nHit Rate: {atk_rate:.1f}%\n\n'
        f'<gold>YELLOW TEAM (Attacker)\n<white>Fired: {state.yellow_fired}  |  Hits: {state.yellow_score}\nHit Rate: {yellow_rate:.1f}%\n\n'
        f'<blue>BLUE TEAM (Defender)\n<white>Fired: {state.blue_fired}  |  Intercepts: {state.blue_score}\nSuccess Rate: {blue_rate:.1f}%  |  Lost: {state.blue_destroyed}\n\n'
        f'<green>GREEN TEAM (Defender)\n<white>Fired: {state.green_fired}  |  Intercepts: {state.green_score}\nSuccess Rate: {green_rate:.1f}%  |  Lost: {state.green_destroyed}'
    )



# ──────────────────────── INPUT ──────────────────────────────────
def input(key):
    if key == 'escape':
        application.quit()
    elif key == 'p':
        state.paused = not state.paused
    elif key == 'e':
        control_panel.enabled = not control_panel.enabled
    elif key == 'r':
        reset_game()

# ─────────────────────────── RUN ─────────────────────────────────
print("""
╔══════════════════════════════════════════════╗
║   MISSILE INTERCEPT SIMULATION  v2  FIXED    ║
╠══════════════════════════════════════════════╣
║  P       = Pause / Resume                    ║
║  R       = Reset                             ║
║  ESC     = Quit                              ║
║  E       = Control Panel                     ║
║  WASD    = Fly Movement                      ║
║  RMB     = Look Around                       ║
╚══════════════════════════════════════════════╝
""")

app.run()