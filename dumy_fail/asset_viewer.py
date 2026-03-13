
from ursina import *
import os
import math

app = Ursina()

# ──────────────────────── KONFIGURASI ────────────────────────
window.title = "OBJ Asset Viewer"
window.color = color.black
window.borderless = False

# Folder tempat file .obj disimpan
# Pastikan folder ini ada di direktori yang sama dengan file script ini
asset_folder = '3d asset/fileobj' 

# Kamera & Environment
cam = EditorCamera()
cam.position = (0, 5, -20)
cam.look_at(Vec3(0, 0, 0))

light = DirectionalLight(shadows=True)
light.look_at(Vec3(1, -1, 1))
AmbientLight(color=color.rgba(100, 100, 100, 100))

# Lantai Grid
Entity(model='plane', scale=100, color=color.gray, texture='white_cube', texture_scale=(50,50))

# List untuk menyimpan objek yang akan dianimasikan
animated_objects = []

def load_obj_files():
    if not os.path.exists(asset_folder):
        print(f"ERROR: Folder '{asset_folder}' tidak ditemukan.")
        Text(text=f"Folder '{asset_folder}' not found!", scale=2, origin=(0,0), color=color.red)
        return

    # Ambil semua file berakhiran .obj
    files = [f for f in os.listdir(asset_folder) if f.endswith('.obj')]
    files.sort()

    if not files:
        Text(text="No .obj files found in folder.", scale=2, origin=(0,0), color=color.yellow)
        return

    spacing = 8.0 # Jarak antar objek
    start_x = -((len(files) - 1) * spacing) / 2

    print(f"Found {len(files)} assets: {files}")

    for i, filename in enumerate(files):
        # Load Model
        file_path = os.path.join(asset_folder, filename)
        
        # Buat Entity
        obj_ent = Entity(
            model=file_path,
            position=(start_x + (i * spacing), 1, 0),
        )
        
        # Atur Ukuran agar seragam (Normalisasi max dimensi ke 5 unit)
        # Setelah model dimuat, Ursina menghitung 'bounds' untuk Entity.
        # Kita gunakan obj_ent.bounds, bukan obj_ent.model.bounds yang menyebabkan error.
        if obj_ent.model:
            max_dim = max(obj_ent.bounds.size)
            obj_ent.scale = 5.0 / max_dim if max_dim > 0 else 1.0
        else:
            obj_ent.scale = 1.0
            
        # Atur Warna Berbeda (HSV Cycle)
        obj_ent.color = color.hsv(i * (360 / len(files)), 0.7, 0.9)

        # Tambahkan Label Nama File di atas objek
        txt_scale = 8.0 / obj_ent.scale_x if obj_ent.scale_x > 0 else 8.0
        # Hitung posisi Y untuk teks. Ini adalah posisi lokal relatif terhadap parent (obj_ent).
        # Kita butuh tinggi asli model (sebelum di-scale). Ini didapat dari (bounds.size.y / scale.y).
        # Asumsi origin model di tengah, maka puncaknya ada di (tinggi / 2).
        model_height_unscaled = obj_ent.bounds.size.y / obj_ent.scale_y if obj_ent.model and obj_ent.scale_y != 0 else 0
        txt_y = (model_height_unscaled / 2) + 0.5 if model_height_unscaled > 0 else 2.0
        Text(parent=obj_ent, text=filename, y=txt_y, scale=txt_scale, billboard=True, color=color.cyan, origin=(0,0))

        # Cek apakah ini rocket_v1 s/d rocket_v4 untuk animasi
        # Kita cek string lowercase agar tidak case-sensitive
        name_lower = filename.lower()
        if 'rocket_v' in name_lower and any(ver in name_lower for ver in ['1', '2', '3', '4']):
            animated_objects.append(obj_ent)

load_obj_files()


app.run()