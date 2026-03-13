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
import os

# ─────────────────────────── APP INIT ────────────────────────────
app = Ursina(title='Missile Intercept Simulation-By. Wahyu Luna', borderless=False)

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
# ──────────────────────────── SETTINGS ───────────────────────────
class Settings:
    attacker_fire_interval  = 3.0
    red_team_active         = True
    yellow_team_active      = False
    orange_team_active      = False   # New Orange Team
    orange_fire_interval    = 4.0
    orange_drone_speed      = 60.0
    orange_drone_maneuver   = 2.0     # Tingkat manuver acak
    orange_drone_curve      = 50.0    # Tingkat lengkungan S
    yellow_fire_interval    = 5.0
    blue_fire_interval      = 2.0
    green_fire_interval     = 2.0
    attacker_missile_speed  = 100.0   
    attacker_missile_wobble = 10    
    yellow_missile_speed    = 120.0
    yellow_split_threshold  = 0.5     
    blue_missile_speed      = 80.0    # Misil pencegat sengaja dibuat lebih lambat
    green_missile_speed     = 80.0
    defender_detect_radius  = 3000.0  
    building                = 200     
    limit_intercept_salvo   = True
    misile_lerp             = 0.5     
    defender_missile_lifetime = 100.0
    gravity                 = 9.8
    arc_height              = 600.0
    attacker_pos = Vec3(-4000, 0, 0)  
    yellow_pos   = Vec3(-4000, 0, -800)
    orange_pos   = Vec3(-4000, 0, 800) 
    blue_pos     = Vec3( 800, 0, -2200) 
    green_pos    = Vec3( 800, 0,  2200) 

cfg = Settings()

# ──────────────────────────── GAME STATE ─────────────────────────
class GameState:
    attacker_score    = 0
    blue_score        = 0
    green_score       = 0
    yellow_score      = 0
    blue_destroyed    = 0
    green_destroyed   = 0
    orange_score      = 0
    attacker_fired    = 0
    yellow_fired      = 0
    orange_fired      = 0
    blue_fired        = 0
    green_fired       = 0
    paused            = False
    attack_timer      = 0.0
    yellow_attack_timer = 0.0
    orange_attack_timer = 0.0
    blue_defend_timer = 0.0
    green_defend_timer= 0.0
    attack_missiles   = []
    yellow_missiles   = []
    orange_drones     = []
    sub_munitions     = []
    intercept_missiles= []
    explosions        = []
    targets           = []
    show_trajectories = False # Status Panel Visual

state = GameState()

# ──────────────────────── HELPER: LOAD 3D MODEL ──────────────────

# ──────────────────────── HELPER: LOAD 3D MODEL ──────────────────
def create_rocket_visual(parent_entity, model_filename, color_tint, size=4.0, rotation_offset=(0, 0, 0)):
    # Gunakan path relatif dari lokasi script. Script ada di 'Advance_Sim', model ada di '../3d asset/fileobj'
    model_path = os.path.join('..', '3d asset', 'fileobj', model_filename)
    
    vis = Entity(parent=parent_entity, model=model_path, color=color_tint, texture='white_cube')
    if vis.model:
        vis.rotation = rotation_offset
        # Normalisasi Ukuran (Logic dari asset_viewer.py)
        max_dim = max(vis.bounds.size)
        vis.scale = size / max_dim if max_dim > 0 else 1.0
    return vis

# ────────────────────── ATTACKER BASE (RED) ──────────────────────
launcher_model_path = os.path.join('..', '3d asset', 'fileobj', 'Launcher_rocket.obj')

atk_launcher = Entity(
    model=launcher_model_path,
    color=color.red,
    position=cfg.attacker_pos,
    rotation_y=270,
    rotation_x=270,
    texture='white_cube'
)
if atk_launcher.model:
    max_dim = max(atk_launcher.bounds.size)
    atk_launcher.scale = 20 / max_dim if max_dim > 0 else 1.0
atk_launcher.y = 10

# ────────────────────── ATTACKER BASE (ORANGE - NEW) ────────────────
orange_launcher = Entity(
    model=launcher_model_path,
    color=color.orange,
    position=cfg.orange_pos,
    rotation_y=270,
    rotation_x=270,
    texture='white_cube'
)
if orange_launcher.model:
    max_dim = max(orange_launcher.bounds.size)
    orange_launcher.scale = 20 / max_dim if max_dim > 0 else 1.0
orange_launcher.y = 10

# ────────────────────── DEFENDER BASE (BLUE) ─────────────────────
blue_launcher = Entity(
    model=launcher_model_path,
    color=color.blue,
    position=cfg.blue_pos,
    rotation_y=125,
    rotation_x=270,
    texture='white_cube'
)
if blue_launcher.model:
    max_dim = max(blue_launcher.bounds.size)
    blue_launcher.scale = 20 / max_dim if max_dim > 0 else 1.0
blue_launcher.y = 10

# ────────────────────── DEFENDER BASE (GREEN) ────────────────────
green_launcher = Entity(
    model=launcher_model_path,
    color=color.green,
    position=cfg.green_pos,
    rotation_y=55,
    rotation_x=270,
    texture='white_cube'
)
if green_launcher.model:
    max_dim = max(green_launcher.bounds.size)
    green_launcher.scale = 20 / max_dim if max_dim > 0 else 1.0
green_launcher.y = 10

# ─────────────────── ATTACKER BASE (YELLOW - NEW) ────────────────
yellow_launcher = Entity(
    model=launcher_model_path,
    color=color.yellow,
    position=cfg.yellow_pos,
    rotation_y=270,
    rotation_x=270,
    texture='white_cube'
)
if yellow_launcher.model:
    max_dim = max(yellow_launcher.bounds.size)
    yellow_launcher.scale = 20 / max_dim if max_dim > 0 else 1.0
yellow_launcher.y = 10



# ────────────────────── EXTRA TARGETS (BLUE & GREEN) ─────────────
blue_launcher.is_base = True
green_launcher.is_base = True
blue_launcher.team = 'blue'
green_launcher.team = 'green'
state.targets = [blue_launcher, green_launcher]

# texture_path = os.path.join('..', '3d asset', 'fileobj')
# Target Biru
for _ in range(cfg.building):
    # building_range = cfg.defender_detect_radius
    tx = cfg.blue_pos.x + random.uniform(-1000, 1000)
    tz = cfg.blue_pos.z + random.uniform(-1000, 1000)
    th = random.uniform(5, 20) # Tinggi bervariasi bangunan
    t_obj = Entity(
        model='cube', texture='brick', color=color.white,
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
        model='cube', texture='brick', color=color.white,
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
dome_Yellow = Entity(
    model    = 'sphere',
    position = cfg.yellow_pos,
    scale    = 400,
    color    = color.yellow,
    wireframe= True,
)
dome_orange = Entity(
    model    = 'sphere',
    position = cfg.orange_pos,
    scale    = 400,
    color    = color.orange,
    wireframe= True,
)
# ──────────────────────── CAMERA SETUP ───────────────────────────
camera.position = cfg.attacker_pos + Vec3(0, 300, 0)
camera.rotation = (60, 0, 0)

# ───────────────────────── HUD / UI ──────────────────────────────
# Latar judul (desain baru)
Title = Entity(parent=camera.ui, enabled=True, z=-5)
Text(parent=Title, text='[ MISSILE INTERCEPT SIMULATION ]', position=(0, 0.45), origin=(0,0), scale=1.5, color=color.yellow)

stats_ui = Text(parent=camera.ui, text='', position=(-0.88, 0.45), scale=0.75,
                color=color.white, origin=(-0.5, 0.5), unlit=True, line_height=1)


Text(parent=camera.ui,
     text='[P] Pause  [R] Reset  [Q] Visual  [E] Control  [ESC] Quit  |  WASD=Fly  RMB=Look  Shift=Fast',
     position=(0,-0.485), scale=0.72,
     color=color.rgba(210,210,210,180), origin=(0,0))

# Label Tim

def teleport_camera(target_pos):
    # Teleport kamera ke atas target dengan sudut pandang isometrik/atas
    camera.position = target_pos + Vec3(0, 300, 0)
    

# Konfigurasi susunan tombol vertikal di bawah HUD Status
btn_scale = (0.2, 0.06)  # Ukuran diperkecil
btn_x = -0.76            # Posisi X (kiri, di bawah status)
btn_start_y = -0.10      # Posisi Y awal (di bawah teks status yang panjang)
btn_gap = 0.07           # Jarak antar tombol

Button(parent=camera.ui, text='[A] RED FORCE', position=(btn_x, btn_start_y),
       scale=btn_scale, color=color.rgba(200,0,0,200),
       on_click=Func(teleport_camera, cfg.attacker_pos))

Button(parent=camera.ui, text='[Y] YELLOW FORCE', position=(btn_x, btn_start_y - btn_gap),
       scale=btn_scale, color=color.rgba(220,220,0,200), text_color=color.black,
       on_click=Func(teleport_camera, cfg.yellow_pos))

Button(parent=camera.ui, text='[O] ORANGE DRONE', position=(btn_x, btn_start_y - btn_gap*2),
       scale=btn_scale, color=color.orange, text_color=color.black,
       on_click=Func(teleport_camera, cfg.orange_pos))

Button(parent=camera.ui, text='[B] BLUE FORCE', position=(btn_x, btn_start_y - btn_gap*3),
       scale=btn_scale, color=color.rgba(0,0,200,200),
       on_click=Func(teleport_camera, cfg.blue_pos))

Button(parent=camera.ui, text='[G] GREEN FORCE', position=(btn_x, btn_start_y - btn_gap*4),
       scale=btn_scale, color=color.rgba(0,200,0,200),
       on_click=Func(teleport_camera, cfg.green_pos))

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
    cfg.orange_team_active = bool(orange_team_slider.value)
    cfg.orange_drone_speed = orange_speed_slider.value
    cfg.orange_fire_interval = orange_fire_slider.value
    cfg.orange_drone_maneuver = orange_maneuver_slider.value
    cfg.orange_drone_curve = orange_curve_slider.value
    cfg.yellow_missile_speed = yellow_speed_slider.value
    cfg.yellow_split_threshold = yellow_split_slider.value
    cfg.defender_missile_lifetime = defender_missile_lifetime.value
    cfg.limit_intercept_salvo = bool(limit_salvo_slider.value)
    cfg.misile_lerp = misile_lerp.value
    
    # Skala dikali 2 karena radius adalah setengah dari diameter (scale)
    dome_blue.scale = cfg.defender_detect_radius * 2
    dome_green.scale = cfg.defender_detect_radius * 2
    
    control_panel.enabled = False 

# ──────────────────────── CUSTOM CONTROL PANEL UI ────────────────
control_panel = Entity(parent=camera.ui, enabled=False, z=-5)
Text(parent=control_panel, text='CONTROLS [E]', position=(0, 0.45), origin=(0,0), scale=1.5, color=color.yellow)

# Layout Constants
col1_x = -0.35
col2_x = 0.35
start_y = 0.40
gap_y = 0.065   # Sedikit dirapatkan agar muat
sl_scale = 0.65 # Sedikit diperkecil

# --- LEFT COLUMN (ATTACKERS: RED & ORANGE) ---
red_team_slider = Slider(min=0, max=1, default=int(cfg.red_team_active), step=1, text='Red Team Active', parent=control_panel, position=(col1_x, start_y), scale=sl_scale)
arc_slider = Slider(min=10, max=2500, default=cfg.arc_height, step=1, text='Arc Height', parent=control_panel, position=(col1_x, start_y - gap_y), scale=sl_scale)
atk_speed_slider = Slider(min=5, max=1500, default=cfg.attacker_missile_speed, step=1, text='Red Speed', parent=control_panel, position=(col1_x, start_y - 2*gap_y), scale=sl_scale)
attacker_missile_wobble = Slider(min=0, max=100, default=cfg.attacker_missile_wobble, step=1, text='Missile Wobble', parent=control_panel, position=(col1_x, start_y - 3*gap_y), scale=sl_scale)
atk_fire_slider = Slider(min=0.1, max=120, default=cfg.attacker_fire_interval, step=0.1, text='Red Interval', parent=control_panel, position=(col1_x, start_y - 4*gap_y), scale=sl_scale)

orange_team_slider = Slider(min=0, max=1, default=int(cfg.orange_team_active), step=1, text='Orange Drone Active', parent=control_panel, position=(col1_x, start_y - 5.5*gap_y), scale=sl_scale)
orange_speed_slider = Slider(min=20, max=300, default=cfg.orange_drone_speed, step=1, text='Drone Speed', parent=control_panel, position=(col1_x, start_y - 6.5*gap_y), scale=sl_scale)
orange_fire_slider = Slider(min=0.5, max=120, default=cfg.orange_fire_interval, step=0.5, text='Drone Interval', parent=control_panel, position=(col1_x, start_y - 7.5*gap_y), scale=sl_scale)
orange_maneuver_slider = Slider(min=0, max=50, default=cfg.orange_drone_maneuver, step=1, text='Maneuver Level', parent=control_panel, position=(col1_x, start_y - 8.5*gap_y), scale=sl_scale)
orange_curve_slider = Slider(min=0, max=300, default=cfg.orange_drone_curve, step=10, text='Curve Trajectory', parent=control_panel, position=(col1_x, start_y - 9.5*gap_y), scale=sl_scale)

# --- RIGHT COLUMN (YELLOW & DEFENDERS) ---
yellow_team_slider = Slider(min=0, max=1, default=int(cfg.yellow_team_active), step=1, text='Yellow Active', parent=control_panel, position=(col2_x, start_y), scale=sl_scale)
yellow_speed_slider = Slider(min=50, max=300, default=cfg.yellow_missile_speed, step=1, text='Yellow Speed', parent=control_panel, position=(col2_x, start_y - gap_y), scale=sl_scale)
yellow_fire_slider = Slider(min=0.5, max=120, default=cfg.yellow_fire_interval, step=0.5, text='Yellow Interval', parent=control_panel, position=(col2_x, start_y - 2*gap_y), scale=sl_scale)
yellow_split_slider = Slider(min=0.1, max=0.9, default=cfg.yellow_split_threshold, step=0.05, text='Yellow Split', parent=control_panel, position=(col2_x, start_y - 3*gap_y), scale=sl_scale)

blue_speed_slider = Slider(min=50, max=1000, default=cfg.blue_missile_speed, step=1, text='Blue Speed', parent=control_panel, position=(col2_x, start_y - 4*gap_y), scale=sl_scale)
blue_fire_slider = Slider(min=0.1, max=30, default=cfg.blue_fire_interval, step=0.1, text='Blue Interval', parent=control_panel, position=(col2_x, start_y - 5*gap_y), scale=sl_scale)
green_speed_slider = Slider(min=50, max=1000, default=cfg.green_missile_speed, step=1, text='Green Speed', parent=control_panel, position=(col2_x, start_y - 6*gap_y), scale=sl_scale)
green_fire_slider = Slider(min=0.1, max=30, default=cfg.green_fire_interval, step=0.1, text='Green Interval', parent=control_panel, position=(col2_x, start_y - 7*gap_y), scale=sl_scale)

defender_missile_lifetime = Slider(min=1, max=100, default=cfg.defender_missile_lifetime, step=1, text='Def. Lifetime', parent=control_panel, position=(col2_x, start_y - 8*gap_y), scale=sl_scale)
limit_salvo_slider = Slider(min=0, max=1, default=int(cfg.limit_intercept_salvo), step=1, text='Limit 3/Target', parent=control_panel, position=(col2_x, start_y - 9*gap_y), scale=sl_scale)
defender_detect_radius = Slider(min=100, max=3000, default=cfg.defender_detect_radius, step=10, text='Detect Radius', parent=control_panel, position=(col2_x, start_y - 10*gap_y), scale=sl_scale)
misile_lerp = Slider(min=0.1, max=10, default=cfg.misile_lerp, step=0.1, text='Lerp', parent=control_panel, position=(col2_x, start_y - 11*gap_y), scale=sl_scale)

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
    tx = t_obj.center_pos.x + random.uniform(-1000, 1000)
    tz = t_obj.center_pos.z + random.uniform(-1000, 1000)
    th = random.uniform(5, 20)
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
        
        # Orientasi sesuai arah jatuh
        if self.vel.length_squared() > 0.1:
            self.body.look_at(self.pos + self.vel)

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

        self.body = Entity()
        create_rocket_visual(self.body, 'Rocket_v3.obj', color.yellow, size=4,rotation_offset=(180, 0, 0))

        # Visual Trajectory Lines
        self.line_arc = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.red, enabled=False)
        self.split_marker = Entity(model='sphere', color=color.yellow, scale=15, enabled=False)

        self.trail = []
        for j in range(8):
            tr = Entity(model='sphere', scale=0.8,
                        color=color.yellow)
            self.trail.append({'e': tr, 'pos': Vec3(self.origin)})
        
        self._set_pos(self.origin)
        
    def _get_arc_pos(self, t):
        p = lerp(self.origin, self.target, t)
        p.y += cfg.arc_height * math.sin(math.pi * t)
        return p

    def _set_pos(self, pos):
        self.body.position = pos
        for i in range(len(self.trail) - 1, 0, -1):
            self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
        self.trail[0]['pos'] = Vec3(pos)
        for i, tr in enumerate(self.trail):
            tr['e'].position = tr['pos']
            a = max(0, 130 - i * 18)
            tr['e'].color = color.rgba(255, 255, 0, a)
            tr['e'].scale = max(0.2, 0.8 - i * 0.08)

    def advance(self, dt):
        if not self.alive or dt == 0: return None

        delta_t_norm = (self.speed / max(self.dist, 1.0)) * dt
        t_before = self.t
        self.t += delta_t_norm

        pos = self._get_arc_pos(min(self.t, 1.0))
        self._set_pos(pos)

        future_pos = self._get_arc_pos(min(self.t + 0.01, 1.0))
        self.body.look_at(future_pos)

        if t_before < cfg.yellow_split_threshold and self.t >= cfg.yellow_split_threshold and not self.split_done:
            self.split_done = True
            pos_before = self._get_arc_pos(t_before)
            current_vel = (pos - pos_before) / dt
            for _ in range(10):
                spread_vel = Vec3(random.uniform(-20, 20), 0, random.uniform(-20, 20))
                state.sub_munitions.append(YellowSubmunition(self.body.position, current_vel + spread_vel))
            self.destroy()
            return 'split'

        # ── Visual Lines Update ──
        if state.show_trajectories and not self.split_done:
            self.line_arc.enabled = True
            self.split_marker.enabled = True
            # Draw future arc from current t to 1.0
            pts = []
            steps = 15
            for i in range(steps + 1):
                sim_t = self.t + (1.0 - self.t) * (i / steps)
                pts.append(self._get_arc_pos(min(sim_t, 1.0)))
            self.line_arc.model.vertices = pts
            self.line_arc.model.generate()
            # Set marker position
            self.split_marker.position = self._get_arc_pos(cfg.yellow_split_threshold)
        else:
            self.line_arc.enabled = False
            self.split_marker.enabled = False

        # Ground collision check
        if pos.y <= 0:
            self.destroy()
            spawn_explosion(pos, color.yellow, 5.0)
            return 'hit'

        if self.t >= 1.0: self.destroy(); return None
        return Vec3(pos)

    def destroy(self):
        self.alive = False
        destroy(self.line_arc)
        destroy(self.split_marker)
        destroy(self.body)
        for tr in self.trail:
            destroy(tr['e'])

# ─────────────────── ORANGE DRONE (NEW) ──────────────────────
class OrangeDrone:
    def __init__(self):
        self.origin = Vec3(cfg.orange_pos.x, 20, cfg.orange_pos.z)
        self.target_ent = random.choice(state.targets)
        self.target = self.target_ent.position + Vec3(random.uniform(-10,10), 0, random.uniform(-10,10))
        self.dist = (self.target - self.origin).length()
        self.speed = cfg.orange_drone_speed
        self.t = 0.0
        self.alive = True
        
        # Random phase untuk animasi noise
        self.noise_offset_x = random.uniform(0, 100)
        self.noise_offset_y = random.uniform(0, 100)

        self.body = Entity()
        create_rocket_visual(self.body, 'Rocket_v1.obj', color.orange, size=3,rotation_offset=(0, 270, 0))

        # Visual Trajectory Lines
        self.line_straight = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.cyan, enabled=False)
        self.line_path = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.red, enabled=False)

        # Trail spheres (Updated)
        self.trail = []
        for j in range(8):
            tr = Entity(model='sphere', scale=0.8, color=color.orange)
            self.trail.append({'e': tr, 'pos': Vec3(self.origin)})
            
        self._set_pos(self.origin)

    def _get_pos_at_t(self, t):
        # Helper untuk menghitung posisi pada waktu t (normalized 0..1)
        # Ini memungkinkan kita memprediksi posisi masa depan untuk rotasi yang mulus
        t = clamp(t, 0, 1)
        base_pos = lerp(self.origin, self.target, t)
        
        # Kurva S (Frekuensi dikurangi agar lengkungan lebih luas/halus)
        curve_amp = cfg.orange_drone_curve
        s_offset = Vec3(0,0,0)
        if curve_amp > 0:
            s_offset.z = math.sin(t * math.pi * 4) * curve_amp 

        # Manuver Acak (Noise)
        maneuver_amp = cfg.orange_drone_maneuver
        m_offset = Vec3(0,0,0)
        if maneuver_amp > 0:
            # Frekuensi dikurangi drastis (50->12, 40->8) agar tidak 'jittery' tapi 'flowing'
            m_offset.y = math.sin(t * 12 + self.noise_offset_y) * maneuver_amp
            m_offset.z += math.cos(t * 8 + self.noise_offset_x) * maneuver_amp
            
        final_pos = base_pos + s_offset + m_offset
        # final_pos.y = max(final_pos.y, 10) # Dihapus agar bisa menyentuh tanah
        return final_pos

    def _set_pos(self, pos):
        self.body.position = pos
        for i in range(len(self.trail) - 1, 0, -1):
            self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
        # Mundurkan titik awal trail ke ekor roket (offset dari pusat)
        # self.body.back adalah vektor yang menunjuk ke belakang dari arah hadap drone
        trail_start_pos = pos + self.body.back * 1.5
        self.trail[0]['pos'] = Vec3(trail_start_pos)

        for i, tr in enumerate(self.trail):
            tr['e'].position = tr['pos']
            a = max(0, 130 - i * 18)
            tr['e'].color = color.rgba(255, 165, 0, a)
            tr['e'].scale = max(0.2, 0.8 - i * 0.08)

    def advance(self, dt):
        if not self.alive or dt == 0: return None
        
        self.t += (self.speed / max(self.dist, 1.0)) * dt
        
        # Hitung posisi saat ini
        final_pos = self._get_pos_at_t(self.t)
        
        self._set_pos(final_pos)
        
        # Hitung posisi masa depan (lookahead) untuk orientasi badan
        # Ini membuat drone benar-benar menghadap ke arah belokan kurva
        future_pos = self._get_pos_at_t(self.t + 0.02)
        
        if (future_pos - final_pos).length_squared() > 0.001:
            self.body.look_at(future_pos)

        # ── Visual Lines Update ──
        if state.show_trajectories:
            self.line_straight.enabled = True
            self.line_path.enabled = True
            self.line_straight.model.vertices = [self.body.position, self.target]
            self.line_straight.model.generate()
            
            pts = []
            for i in range(16): # Sample future path
                sim_t = self.t + (1.0 - self.t) * (i / 15)
                pts.append(self._get_pos_at_t(sim_t))
            self.line_path.model.vertices = pts
            self.line_path.model.generate()
        else:
            self.line_straight.enabled = False
            self.line_path.enabled = False

        # Ground collision check
        if final_pos.y <= 0:
            self.destroy()
            spawn_explosion(final_pos, color.orange, 5.0)
            return 'hit' # Dianggap 'hit' agar hilang dari list, tapi tidak menambah skor

        if self.t >= 1.0:
            self.destroy()
            spawn_explosion(final_pos, color.orange, 5.0)
            # Cek jika drone mengenai target yang dituju
            if (final_pos - self.target_ent.position).length() < 15.0:
                state.orange_score += 1
                if not self.target_ent.is_base: # Jika bukan markas utama
                    respawn_target(self.target_ent)
                    if self.target_ent.team == 'blue': state.blue_destroyed += 1
                    elif self.target_ent.team == 'green': state.green_destroyed += 1
            return 'hit' # Return 'hit' agar drone dihapus dari list aktif
            
        return Vec3(final_pos)

    def destroy(self):
        self.alive = False
        destroy(self.line_straight)
        destroy(self.line_path)
        destroy(self.body)
        for tr in self.trail:
            destroy(tr['e'])

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

        # Badan misil diganti 3D Model
        self.body = Entity()
        create_rocket_visual(self.body, 'Rocket_v2.obj', color.red, size=4.0,rotation_offset=(0, 0, 0))

        # Visual Trajectory Lines
        self.line_straight = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.cyan, enabled=False)
        self.line_arc = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.red, enabled=False)

        # Trail spheres
        self.trail = []
        for k in range(8):
            tr = Entity(model='sphere',scale=0.8,
                        color=color.yellow)
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
        # Hitung arah untuk look_at (simple approach: look at next pos)
        # Karena wobble, look_at target kadang terlihat aneh, tapi kita coba look_at target utama + arc
        # Atau lebih baik: look_at posisi framer berikutnya di advance (kurang akurat di _set_pos static)
        
        for i in range(len(self.trail) - 1, 0, -1):
            self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
        self.trail[0]['pos'] = Vec3(pos)
        for i, tr in enumerate(self.trail):
            tr['e'].position = tr['pos']
            a = max(0, 130 - i * 18)
            tr['e'].color = color.rgba(255, 255, 0, a) # Paksa Kuning (R=255, G=255, B=0)
            tr['e'].scale = max(0.2, 0.8 - i * 0.08)

    def advance(self, dt):
        if not self.alive:
            return None
        self.t += (self.speed / max(self.dist, 1.0)) * dt
        pos = self._get_arc_pos(min(self.t, 1.0))
        self._set_pos(pos)
        
        # Update rotasi agar moncong menghadap depan
        future_pos = self._get_arc_pos(min(self.t + 0.01, 1.0))
        self.body.look_at(future_pos)

        # ── Visual Lines Update ──
        if state.show_trajectories:
            self.line_straight.enabled = True
            self.line_arc.enabled = True
            self.line_straight.model.vertices = [self.body.position, self.target]
            self.line_straight.model.generate()
            
            pts = []
            for i in range(16):
                sim_t = self.t + (1.0 - self.t) * (i / 15)
                pts.append(self._get_arc_pos(min(sim_t, 1.0)))
            self.line_arc.model.vertices = pts
            self.line_arc.model.generate()
        else:
            self.line_straight.enabled = False
            self.line_arc.enabled = False

        # Ground collision check
        if pos.y <= 0:
            self.destroy()
            spawn_explosion(pos, color.red, 5.0)
            return 'hit' # Dianggap 'hit' agar hilang dari list, tapi tidak menambah skor

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
        destroy(self.line_straight)
        destroy(self.line_arc)
        destroy(self.body)
        for tr in self.trail:
            destroy(tr['e'])

# ──────────────────── YELLOW LINE INTERCEPT LOGIC ──────────────────────────
class InterceptMissile:
    def __init__(self, target_atk, start_pos, team_color, team_name):
        self.target   = target_atk
        self.pos      = Vec3(start_pos.x, 10, start_pos.z)
        self.team     = team_name
        
        self.speed = cfg.blue_missile_speed if self.team == 'blue' else cfg.green_missile_speed
        self.lifetime = cfg.defender_missile_lifetime
        self.alive    = True

        # Inisialisasi arah awal ke atas agar peluncuran terlihat alami
        self.current_dir = Vec3(0, 1, 0).normalized()
        
        self.body = Entity()
        create_rocket_visual(self.body, 'Rocket_v4.obj', team_color, size=3.0,rotation_offset=(0, 0, 0))

        # Visual Trajectory Lines
        self.line_target_vis = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.orange, enabled=False)
        self.line_predict_vis = Entity(model=Mesh(vertices=[], mode='line', thickness=2), color=color.pink, enabled=False)

        # Visual Trail
        self.trail = []
        for k in range(6):
            tr = Entity(model='sphere', scale=0.8, color=color.yellow)
            self.trail.append({'e': tr, 'pos': Vec3(self.pos)})

        self._set_pos(self.pos)

    def _set_pos(self, pos):
        self.body.position = pos
        for i in range(len(self.trail) - 1, 0, -1):
            self.trail[i]['pos'] = Vec3(self.trail[i-1]['pos'])
        self.trail[0]['pos'] = Vec3(pos)
        for i, tr in enumerate(self.trail):
            tr['e'].position = tr['pos']
            a = max(0, 130 - i * 18)
            tr['e'].color = color.rgba(255, 255, 0, a) # Paksa Kuning (R=255, G=255, B=0)
            tr['e'].scale = max(0.2, 0.8 - i * 0.08)

    def advance(self, dt):
        if not self.alive or not self.target or not self.target.alive:
            if self.alive: self.destroy()
            return None
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.destroy()
            return None

        target_pos = Vec3(self.target.body.position)
        my_pos = self.pos

        # Estimasi Kecepatan Target (Vektor) berdasarkan tipe target
        if isinstance(self.target, (AttackMissile, YellowAttackMissile)):
            # Prediksi untuk misil balistik dengan _get_arc_pos
            t_sample = 0.01
            future_target_pos = self.target._get_arc_pos(min(self.target.t + t_sample, 1.0))
            target_velocity_vec = (future_target_pos - target_pos) / t_sample
        elif isinstance(self.target, YellowSubmunition):
            # Prediksi sederhana untuk submunisi yang hanya dipengaruhi gravitasi
            target_velocity_vec = self.target.vel
        else:
            # Fallback jika tipe target tidak diketahui
            target_velocity_vec = Vec3(0,0,0)
            
        # Fix untuk OrangeDrone yang tidak punya _get_arc_pos tapi punya metode gerakan lain
        # Kita pakai finite difference sederhana dari posisi
        if isinstance(self.target, OrangeDrone):
            # Kecepatan drone relatif konstan ke arah target + noise
            target_velocity_vec = (self.target.target - self.target.origin).normalized() * self.target.speed

        # MENCARI TITIK TEMU (INTERCEPT POINT)
        rel_pos = target_pos - my_pos
        rel_dist = rel_pos.length()
        time_to_intercept = rel_dist / (self.speed + target_velocity_vec.length()) if (self.speed + target_velocity_vec.length()) > 0 else 0

        # Titik Temu = Posisi Target Sekarang + (Vektor Gerak Target * Waktu Perjalanan Kita)
        # Kita gunakan multiplier 0.9 agar misil tidak terlalu "pede" membidik terlalu jauh ke depan
        intercept_point = target_pos + (target_velocity_vec * time_to_intercept * 0.9)

        # 4. STEERING (KEMUDI)
        # Arahkan misil ke titik temu tersebut
        desired_dir = (intercept_point - my_pos).normalized()
        
        # Gunakan Slerp atau Lerp agar belokan tidak patah (menciptakan efek garis kuning melengkung)
        # Semakin rendah nilai 5.0, semakin lebar lengkungan misilnya
        self.current_dir = lerp(self.current_dir, desired_dir, dt * cfg.misile_lerp).normalized()

        # 5. GERAK & ROTASI
        self.pos += self.current_dir * self.speed * dt
        
        # Visual Update
        self.body.position = self.pos
        self.body.look_at(self.pos + self.current_dir)
        self._set_pos(self.pos)

        # ── Visual Lines Update ──
        if state.show_trajectories:
            self.line_target_vis.enabled = True
            self.line_predict_vis.enabled = True
            self.line_target_vis.model.vertices = [self.pos, target_pos]
            self.line_target_vis.model.generate()
            
            self.line_predict_vis.model.vertices = [self.pos, intercept_point]
            self.line_predict_vis.model.generate()
        else:
            self.line_target_vis.enabled = False
            self.line_predict_vis.enabled = False

        # Ground collision check
        if self.pos.y <= 0:
            self.destroy()
            spawn_explosion(self.pos, self.body.color, 3.0)
            return None # Dianggap selesai/gagal

        # 6. CEK TABRAKAN (DI UDARA)
        if (target_pos - self.pos).length() < 8.0: # Radius ledakan di udara
            return 'intercept'
        
        return Vec3(self.pos)

    def destroy(self):
        self.alive = False
        destroy(self.line_target_vis)
        destroy(self.line_predict_vis)
        if self.body:
            destroy(self.body)
        for tr in self.trail:
            destroy(tr['e'])

# ─────────────────────────── RESET ───────────────────────────────
def reset_game():
    for m in list(state.attack_missiles):
        m.destroy()
    for m in list(state.yellow_missiles):
        m.destroy()
    for m in list(state.orange_drones):
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
    state.orange_drones.clear()
    state.sub_munitions.clear()
    state.intercept_missiles.clear()
    state.explosions.clear()
    state.attacker_score = 0
    state.yellow_score   = 0
    state.orange_score   = 0
    state.blue_score     = 0
    state.green_score    = 0
    state.blue_destroyed = 0
    state.green_destroyed = 0
    state.attacker_fired = 0
    state.yellow_fired   = 0
    state.orange_fired   = 0
    state.blue_fired     = 0
    state.green_fired    = 0
    state.attack_timer   = 0.0
    state.yellow_attack_timer = 0.0
    state.orange_attack_timer = 0.0
    state.blue_defend_timer = 0.0
    state.green_defend_timer= 0.0

# ─────────────────────────── HUD UPDATE ────────────────────────
def update_hud():
    atk_rate   = (state.attacker_score / state.attacker_fired * 100) if state.attacker_fired > 0 else 0.0
    blue_rate  = (state.blue_score / state.blue_fired * 100) if state.blue_fired > 0 else 0.0
    green_rate = (state.green_score / state.green_fired * 100) if state.green_fired > 0 else 0.0
    yellow_rate = (state.yellow_score / (state.yellow_fired * 5) * 100) if state.yellow_fired > 0 else 0.0
    orange_rate = (state.orange_score / state.orange_fired * 100) if state.orange_fired > 0 else 0.0

    stats_ui.text = (
        f'<red>RED TEAM (Attacker)\n<white>Fired: {state.attacker_fired}  |  Hits: {state.attacker_score}\nHit Rate: {atk_rate:.1f}%\n\n'
        f'<yellow>YELLOW TEAM (Attacker)\n<white>Fired: {state.yellow_fired}  |  Hits: {state.yellow_score}\nHit Rate: {yellow_rate:.1f}%\n\n'
        f'<orange>ORANGE TEAM (Drone)\n<white>Fired: {state.orange_fired}  |  Hits: {state.orange_score}\nHit Rate: {orange_rate:.1f}%\n\n'
        f'<blue>BLUE TEAM (Defender)\n<white>Fired: {state.blue_fired}  |  Intercepts: {state.blue_score}\nSuccess Rate: {blue_rate:.1f}%  |  Lost: {state.blue_destroyed}\n\n'
        f'<green>GREEN TEAM (Defender)\n<white>Fired: {state.green_fired}  |  Intercepts: {state.green_score}\nSuccess Rate: {green_rate:.1f}%  |  Lost: {state.green_destroyed}'
    )

    # Indikator Visual
    if state.show_trajectories:
        stats_ui.text += '\n\n<cyan>VISUAL PANEL: ON'
    else:
        stats_ui.text += '\n\n<gray>VISUAL PANEL: OFF'

    # Indikator Pause
    if state.paused:
        stats_ui.text += '\n\n<red>GAME PAUSED'

# ─────────────────────────── UPDATE ──────────────────────────────
def update():
    # ── Camera Fly Control (WASD + RMB) ──
    if held_keys['right mouse']:
        camera.rotation_y += mouse.velocity.x * 150
        camera.rotation_x -= mouse.velocity.y * 150
        camera.rotation_x = clamp(camera.rotation_x, -90, 90)

    speed = 200 * time.dt
    if held_keys['shift']: speed *= 8  # Sprint

    if held_keys['w']: camera.position += camera.forward * speed
    if held_keys['s']: camera.position -= camera.forward * speed
    if held_keys['a']: camera.position -= camera.right * speed
    if held_keys['d']: camera.position += camera.right * speed


    if state.paused:
        update_hud()
        return

    dt = time.dt

    # ── Spawn attack missile (RED) ──
    if cfg.red_team_active:
        state.attack_timer += dt
        if state.attack_timer >= cfg.attacker_fire_interval:
            state.attack_timer = 0.0
            state.attack_missiles.append(AttackMissile())
            state.attacker_fired += 1

    # ── Spawn Orange Drone ──
    if cfg.orange_team_active:
        state.orange_attack_timer += dt
        if state.orange_attack_timer >= cfg.orange_fire_interval:
            state.orange_attack_timer = 0.0
            state.orange_drones.append(OrangeDrone())
            state.orange_fired += 1

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

    # ── Advance Orange Drones ──
    dead_o = []
    for m in state.orange_drones:
        if not m.alive: dead_o.append(m); continue
        if m.advance(dt) in ('hit', None): dead_o.append(m)
    for m in dead_o:
        if m in state.orange_drones: state.orange_drones.remove(m)

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
                  [m for m in state.orange_drones if m.alive]

    # ── DEFENSE LOGIC (BLUE) ──
    blue_threats = [m for m in all_threats if
                    (m.body.position - cfg.blue_pos).length() <= cfg.defender_detect_radius]
    
    state.blue_defend_timer += dt
    if blue_threats and state.blue_defend_timer >= cfg.blue_fire_interval:
        state.blue_defend_timer = 0.0
        
        target_to_engage = None
        if cfg.limit_intercept_salvo:
            # Hitung berapa banyak pencegat yang sudah mengarah ke setiap ancaman
            intercept_counts = {t: 0 for t in blue_threats}
            for im in state.intercept_missiles:
                if im.alive and im.team == 'blue' and im.target in intercept_counts:
                    intercept_counts[im.target] += 1
            
            # Cari ancaman yang memiliki < 3 pencegat
            for threat in blue_threats:
                if intercept_counts.get(threat, 0) < 3:
                    target_to_engage = threat
                    break # Target ditemukan, keluar dari loop
        else:
            # Logika original: tembak target yang belum ditarget sama sekali
            targeted = {im.target for im in state.intercept_missiles if im.alive}
            free = [t for t in blue_threats if t not in targeted]
            if free:
                target_to_engage = free[0]
            else: # Jika semua sudah ditarget, tembak yang paling dekat (logika original)
                target_to_engage = blue_threats[0]

        if target_to_engage:
            state.intercept_missiles.append(
                InterceptMissile(target_to_engage, cfg.blue_pos, color.blue, 'blue'))
            state.blue_fired += 1

    # ── DEFENSE LOGIC (GREEN) ──
    green_threats = [m for m in all_threats if
                     (m.body.position - cfg.green_pos).length() <= cfg.defender_detect_radius]
    
    state.green_defend_timer += dt
    if green_threats and state.green_defend_timer >= cfg.green_fire_interval:
        state.green_defend_timer = 0.0

        target_to_engage = None
        if cfg.limit_intercept_salvo:
            intercept_counts = {t: 0 for t in green_threats}
            for im in state.intercept_missiles:
                if im.alive and im.team == 'green' and im.target in intercept_counts:
                    intercept_counts[im.target] += 1
            
            for threat in green_threats:
                if intercept_counts.get(threat, 0) < 3:
                    target_to_engage = threat
                    break
        else:
            targeted = {im.target for im in state.intercept_missiles if im.alive}
            free = [t for t in green_threats if t not in targeted]
            target_to_engage = free[0] if free else green_threats[0]

        if target_to_engage:
            state.intercept_missiles.append(
                InterceptMissile(target_to_engage, cfg.green_pos, color.green, 'green'))
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
            for missile_list in [state.attack_missiles, state.yellow_missiles, state.sub_munitions, state.orange_drones]:
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
    update_hud()



# ──────────────────────── INPUT ──────────────────────────────────
def input(key):
    if key == 'escape':
        application.quit()
    elif key == 'p':
        state.paused = not state.paused
    elif key == 'e':
        control_panel.enabled = not control_panel.enabled
    elif key == 'q':
        state.show_trajectories = not state.show_trajectories
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
║  Q       = Visual Panel (Trajectories)       ║
║  WASD    = Fly Movement                      ║
║  RMB     = Look Around                       ║
╚══════════════════════════════════════════════╝
""")

app.run()