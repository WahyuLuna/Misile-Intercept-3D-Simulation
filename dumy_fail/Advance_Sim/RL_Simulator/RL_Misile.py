import gymnasium as gym
import numpy as np
import math
import random
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

# --- Konfigurasi Simulasi (disamakan dengan file visual) ---
class SimConfig:
    # Parameter yang diacak per episode tidak lagi di sini
    attacker_missile_wobble = 10 # Sesuai permintaan, nilai tetap
    gravity                 = 9.8
    attacker_pos            = np.array([-4000.0, 0.0, 0.0])
    blue_pos                = np.array([800.0, 0.0, 0.0])
    # Timestep untuk simulasi headless, misal 30 FPS
    dt = 1/30.0

cfg = SimConfig()

# --- Kelas Headless (Tanpa Grafis Ursina) ---

class AttackMissileHeadless:
    """Versi AttackMissile tanpa komponen visual Entity dari Ursina."""
    def __init__(self, speed, arc_height, wobble):
        self.origin = np.array([cfg.attacker_pos[0], 10.0, cfg.attacker_pos[2]])
        # Target disederhanakan ke markas biru untuk konsistensi episode
        self.target = np.array([cfg.blue_pos[0], 0.0, cfg.blue_pos[2]])
        self.t = 0.0
        self.dist = np.linalg.norm(self.target - self.origin)
        self.speed = speed
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.alive = True
        self.position = np.copy(self.origin)
        self.velocity = np.zeros(3)
        self.last_pos = np.copy(self.origin)
        # Simpan parameter yang diacak
        self.arc_height = arc_height
        self.wobble = wobble

    def _get_arc_pos(self, t):
        p = self.origin + (self.target - self.origin) * t
        p[1] += self.arc_height * math.sin(math.pi * t)
        if t > 0.5:
            ramp = (t - 0.5) * 2.0
            side = self.wobble * math.sin(self.wobble_phase + 3.0 * t * math.pi * 4)
            p[2] += side * ramp
        return p

    def advance(self, dt):
        if not self.alive: return None
        self.t += (self.speed / max(self.dist, 1.0)) * dt
        pos = self._get_arc_pos(min(self.t, 1.0))
        
        if dt > 0:
            self.velocity = (pos - self.last_pos) / dt
        self.last_pos = np.copy(pos)
        self.position = pos

        if self.t >= 1.0:
            self.alive = False
            return 'hit'
        return self.position

class RLInterceptMissileHeadless:
    """Versi RLInterceptMissile tanpa komponen visual Entity dari Ursina."""
    def __init__(self, target_atk, start_pos, speed):
        self.target = target_atk
        self.pos = np.array([start_pos[0], 10.0, start_pos[2]])
        self.speed = speed
        self.alive = True
        
        self.current_dir = np.array([0.0, 1.0, 0.0])
        self.velocity = self.current_dir * self.speed
        self.max_turn_rate = 3.0 # Radian per detik
        
        self.prev_distance = np.linalg.norm(self.target.position - self.pos) if self.target else 0
        self.time_alive = 0.0

    def get_state(self):
        if not self.target or not self.target.alive:
            return np.zeros(9, dtype=np.float32)
            
        target_pos = self.target.position
        target_vel = self.target.velocity
        
        rel_pos = (target_pos - self.pos) / 1000.0
        rel_vel = (target_vel - self.velocity) / 200.0
        
        state_array = np.concatenate([rel_pos, rel_vel, self.current_dir])
        return state_array.astype(np.float32)

    def compute_reward(self, terminal_state):
        if not self.target or not self.target.alive: return 0.0
        
        current_distance = np.linalg.norm(self.target.position - self.pos)
        
        # 1. Reward mendekati target
        dist_reward = (self.prev_distance - current_distance) * 0.1
        self.prev_distance = current_distance
        reward = dist_reward
        
        # 2. Penalti waktu agar lebih efisien
        reward -= 0.01

        # 3. Sparse Rewards (kondisi terminal)
        if terminal_state == 'intercept': reward += 100.0
        elif terminal_state == 'crash': reward -= 50.0
        elif terminal_state == 'miss': reward -= 20.0
            
        return reward

    def apply_action(self, action, dt):
        pitch_cmd = action[0] * self.max_turn_rate * dt
        yaw_cmd = action[1] * self.max_turn_rate * dt

        right = np.cross(self.current_dir, np.array([0.0, 1.0, 0.0]))
        if np.linalg.norm(right) == 0: right = np.array([1.0, 0.0, 0.0])
        up = np.cross(right, self.current_dir)
        
        new_dir = self.current_dir + (up * pitch_cmd) + (right * yaw_cmd)
        self.current_dir = new_dir / np.linalg.norm(new_dir)
        self.velocity = self.current_dir * self.speed

    def advance(self, action, dt):
        if not self.alive: return None, None
        
        self.time_alive += dt
        self.apply_action(action, dt)
        self.pos += self.velocity * dt
        
        # Cek Kondisi Terminal
        if not self.target or not self.target.alive:
            self.alive = False
            return 'miss', self.compute_reward('miss')
            
        current_distance = np.linalg.norm(self.target.position - self.pos)
        if current_distance < 10.0:
            self.alive = False
            return 'intercept', self.compute_reward('intercept')
            
        if self.pos[1] <= 0 or np.linalg.norm(self.pos) > 5000 or self.time_alive > 20:
            self.alive = False
            return 'crash', self.compute_reward('crash')

        reward = self.compute_reward(None)
        return None, reward

# --- Gym Environment ---
class MissileEnv(gym.Env):
    """Custom Environment yang mengikuti interface OpenAI Gym."""
    def __init__(self):
        super(MissileEnv, self).__init__()
        self.action_space = gym.spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(9,), dtype=np.float32)
        self.dt = cfg.dt

    def reset(self, seed=None, options=None):
        # Gymnasium mengharuskan reset untuk menerima 'seed' dan mengembalikan (obs, info)
        super().reset(seed=seed)

        # --- RANDOMISASI PARAMETER PER EPISODE ---
        # Sesuai permintaan, nilai diacak dalam rentang dengan step tertentu
        attacker_speed = random.randrange(50, 301, 5)
        interceptor_speed = 95
        # interceptor_speed = random.randrange(80, 151, 5)
        arc_height = 600
        # arc_height = random.randrange(20, 801, 10)
        # Variabel baru 'detection_dome' ditambahkan dan diacak
        self.detection_radius = 3000
        # self.detection_radius = random.randrange(500, 3001, 100)

        self.attacker = AttackMissileHeadless(
            speed=attacker_speed,
            arc_height=arc_height,
            wobble=cfg.attacker_missile_wobble # Wobble tetap sesuai permintaan
        )
        self.interceptor = RLInterceptMissileHeadless(
            self.attacker,
            cfg.blue_pos,
            speed=interceptor_speed
        )
        obs = self.interceptor.get_state()
        info = {} # info bisa diisi dengan nilai acak jika ingin di-log
        return obs, info

    def step(self, action):
        self.attacker.advance(self.dt)
        terminal_state, reward = self.interceptor.advance(action, self.dt)
        # Gymnasium menggunakan 'terminated' dan 'truncated'
        terminated = terminal_state is not None
        truncated = False # Tidak ada kondisi truncated untuk saat ini
        obs = self.interceptor.get_state()
        info = {}
        return obs, reward, terminated, truncated, info

    def render(self, mode='human'):
        pass

# --- Main Training Loop ---
if __name__ == '__main__':
    print("Membuat dan memeriksa environment...")
    env = MissileEnv()
    check_env(env)

    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_missile_tensorboard/")

    print("\nMemulai proses training... (Ini bisa memakan waktu beberapa menit)")
    model.learn(total_timesteps=500000)
    print("Training selesai.")

    model_path = "ppo_missile_model_4.zip"
    model.save(model_path)
    print(f"Model disimpan di: {model_path}")
    print(f"\nSekarang Anda bisa menjalankan file 'test2.py' untuk melihat hasilnya.")