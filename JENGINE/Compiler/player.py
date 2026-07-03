import os
import sys
import time
import struct
import dearpygui.dearpygui as dpg
import winsound

cartridge_assets = {}

def mount_cartridge():
    ore_path = "game.ore"
    if not os.path.exists(ore_path):
        sys.exit(1)
    with open(ore_path, 'rb') as f:
        file_count = struct.unpack("<I", f.read(4))[0]
        directory = []
        for _ in range(file_count):
            name_len = struct.unpack("B", f.read(1))[0]
            name = f.read(name_len).decode('utf-8')
            file_size = struct.unpack("<I", f.read(4))[0]
            directory.append((name, file_size))
        for name, file_size in directory:
            cartridge_assets[name] = f.read(file_size)

class PlayerState:
    def __init__(self):
        self.player_x, self.player_y = 20.0, 20.0
        self.player_movetype = "wasd"
        self.camera_mode = 3  # Start in 3rd person by default
        self.display_text = ""
        self.display_text_duration = 0.0
        self.active_objects = {}
        self.running = True
    def clamp(self, val): return max(0.0, min(40.0, val))

state = PlayerState()

class MemoryOBJModel:
    def __init__(self, filename):
        self.vertices, self.faces = [], []
        if filename in cartridge_assets:
            text_data = cartridge_assets[filename].decode('utf-8')
            for line in text_data.splitlines():
                if line.startswith('v '):
                    parts = line.split()
                    self.vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif line.startswith('f '):
                    face = [int(p.split('/')[0]) - 1 for p in line.split()[1:]]
                    self.faces.append(face)

# A single active script execution tracker
class ScriptThread:
    def __init__(self, filename):
        self.filename = filename
        self.instructions = []
        self.pc = 0
        self.waiting_for_touch = None
        self.is_alive = True
        
        if filename in cartridge_assets:
            lines = cartridge_assets[filename].decode('utf-8').splitlines()
            self.instructions = [l.strip() for l in lines if l.strip() and not l.strip().startswith("//")]
        else:
            self.is_alive = False

# The Multi-Threaded Script Manager
class MultiScriptEngine:
    def __init__(self):
        self.threads = []

    def launch_script(self, filename):
        if any(t.filename == filename and t.is_alive for t in self.threads):
            return
        new_thread = ScriptThread(filename)
        if new_thread.is_alive:
            self.threads.append(new_thread)

    def update(self, dt):
        if state.display_text_duration > 0:
            state.display_text_duration -= dt
            if state.display_text_duration <= 0: state.display_text = ""

        # Update all active execution threads
        for thread in self.threads:
            if not thread.is_alive: 
                continue
                
            if thread.waiting_for_touch:
                o1, o2 = thread.waiting_for_touch
                if o1 in state.active_objects and o2 in state.active_objects:
                    if abs(state.active_objects[o1]["x"] - state.active_objects[o2]["x"]) < 1.0 and abs(state.active_objects[o1]["y"] - state.active_objects[o2]["y"]) < 1.0:
                        thread.waiting_for_touch = None
                        thread.pc += 1
                continue

            if thread.pc >= len(thread.instructions):
                thread.is_alive = False
                continue

            line = thread.instructions[thread.pc]
            tokens = line.split()
            if not tokens:
                thread.pc += 1
                continue
                
            cmd = tokens[0].lower()

            if cmd == "movetype": 
                state.player_movetype = tokens[1].lower(); thread.pc += 1
            elif cmd == "setplayerpos":
                val = float(tokens[2])
                if tokens[1].lower() == 'x': state.player_x = val
                else: state.player_y = val
                thread.pc += 1
            elif cmd == "bgmloop":
                track_name = tokens[1]
                if track_name in cartridge_assets:
                    with open(track_name, "wb") as temp_audio: temp_audio.write(cartridge_assets[track_name])
                    winsound.PlaySound(track_name, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                thread.pc += 1
            elif cmd == "assignobj": 
                state.active_objects[tokens[1]] = {"model": tokens[2], "x": 0.0, "y": 0.0, "pushable": 0}; thread.pc += 1
            elif cmd == "setobjpos":
                obj = state.active_objects[tokens[1]]; val = float(tokens[3])
                if tokens[2].lower() == 'x': obj["x"] = val
                else: obj["y"] = val
                thread.pc += 1
            elif cmd == "objpushable": 
                state.active_objects[tokens[1]]["pushable"] = int(tokens[2]); thread.pc += 1
            elif cmd == "waituntiltouch": 
                thread.waiting_for_touch = (tokens[1], tokens[2])
            elif cmd == "displaytext": 
                state.display_text = line.split('"')[1]; state.display_text_duration = 4.0; thread.pc += 1
            elif cmd == "cammode":
                state.camera_mode = int(tokens[1]); thread.pc += 1
            elif cmd == "runscript":
                self.launch_script(tokens[1])
                thread.pc += 1
            elif cmd == "end":
                thread.is_alive = False
            elif cmd == "closegame":
                state.running = False
                thread.is_alive = False
            else: 
                thread.pc += 1

        # Clean out dead threads
        self.threads = [t for t in self.threads if t.is_alive]

mount_cartridge()
script_engine = MultiScriptEngine()
script_engine.launch_script("BASE.jcode")
model_cache = {}

dpg.create_context()
dpg.create_viewport(title="JPlayer", width=1280, height=720, resizable=True)

def on_viewport_resize():
    width = dpg.get_viewport_width()
    height = dpg.get_viewport_height()
    dpg.configure_item("main_viewport", width=width, height=height)
    dpg.configure_item("canvas", width=width, height=height)

with dpg.window(no_title_bar=True, no_move=True, no_resize=True, tag="main_viewport"):
    dpg.add_text("", tag="overlay_text")
    dpg.add_drawlist(width=1280, height=720, tag="canvas")

dpg.set_viewport_resize_callback(on_viewport_resize)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_item_pos("main_viewport", [0, 0])
on_viewport_resize()

last_time = time.time()
while dpg.is_dearpygui_running() and state.running:
    dt = time.time() - last_time
    last_time = time.time()
    
    script_engine.update(dt)
    if not state.running: 
        break
    
    vw = dpg.get_viewport_width()
    vh = dpg.get_viewport_height()
    half_w = vw // 2
    half_h = vh // 2
    
    move_speed = 12.0 * dt
    dx, dy = 0.0, 0.0
    
    # --- ADDED ARROW KEY INTEGRATION MOVEMENT MODES ---
    if state.player_movetype == "wasd":
        if dpg.is_key_down(dpg.mvKey_W): dy -= move_speed
        if dpg.is_key_down(dpg.mvKey_S): dy += move_speed
        if dpg.is_key_down(dpg.mvKey_A): dx -= move_speed
        if dpg.is_key_down(dpg.mvKey_D): dx += move_speed
    elif state.player_movetype == "arrow":
        if dpg.is_key_down(dpg.mvKey_Up):    dy -= move_speed
        if dpg.is_key_down(dpg.mvKey_Down):  dy += move_speed
        if dpg.is_key_down(dpg.mvKey_Left):  dx -= move_speed
        if dpg.is_key_down(dpg.mvKey_Right): dx += move_speed

    if dx != 0.0 or dy != 0.0:
        t_px, t_py = state.clamp(state.player_x + dx), state.clamp(state.player_y + dy)
        can_move = True
        for name, obj in state.active_objects.items():
            if abs(t_px - obj["x"]) < 1.0 and abs(t_py - (obj["y"] + 3.5)) < 1.0:
                if obj["pushable"] == 1:
                    obj["x"] = state.clamp(obj["x"] + dx)
                    obj["y"] = state.clamp(obj["y"] + dy)
                else: can_move = False
        if can_move: state.player_x, state.player_y = t_px, t_py

    dpg.delete_item("canvas", children_only=True)
    
    # --- FIXED CAMERA DYNAMIC MATRIX ALLOCATION MODES ---
    cx, cy, cz = state.player_x, 5.0, state.player_y + 10.0
    if state.camera_mode == 1:
        cx, cy, cz = state.player_x, 1.5, state.player_y + 0.1
    
    def project(x, y, z):
        rx, ry, rz = x - cx, y - cy, z - cz
        if rz >= -0.1: rz = -0.1
        return [int((rx * 300.0 / -rz) + half_w), int((-ry * 300.0 / -rz) + half_h)]

    for z_line in range(0, 41, 4): dpg.draw_line(project(0, 0, z_line), project(40, 0, z_line), color=[80, 80, 80, 255], parent="canvas")
    for x_line in range(0, 41, 4): dpg.draw_line(project(x_line, 0, 0), project(x_line, 0, 40), color=[80, 80, 80, 255], parent="canvas")

    for name, data in state.active_objects.items():
        if data["model"] not in model_cache: model_cache[data["model"]] = MemoryOBJModel(data["model"])
        m = model_cache[data["model"]]
        col = [230, 90, 90, 255] if data["pushable"] else [130, 130, 130, 255]
        for face in m.faces:
            pts = [project(data["x"] + m.vertices[vi][0]*0.2, m.vertices[vi][1]*0.2, data["y"] + m.vertices[vi][2]*0.2) for vi in face if vi < len(m.vertices)]
            if len(pts) >= 3: dpg.draw_polyline(pts, color=col, thickness=1, parent="canvas")

    # Render tracking box cubes only in 3rd person views
    if state.camera_mode == 3:
        dpg.draw_quad(project(state.player_x-0.4, 0, state.player_y-0.4), project(state.player_x+0.4, 0, state.player_y-0.4), project(state.player_x+0.4, 0, state.player_y+0.4), project(state.player_x-0.4, 0, state.player_y+0.4), color=[60, 160, 255, 255], parent="canvas")
        dpg.draw_quad(project(state.player_x-0.4, 1.6, state.player_y-0.4), project(state.player_x+0.4, 1.6, state.player_y-0.4), project(state.player_x+0.4, 1.6, state.player_y+0.4), project(state.player_x-0.4, 1.6, state.player_y+0.4), color=[60, 160, 255, 255], parent="canvas")

    if state.display_text:
        dpg.set_value("overlay_text", f"{state.display_text}")
        dpg.configure_item("overlay_text", color=[255, 255, 50, 255])
        dpg.set_global_font_scale(5.0)
    else:
        dpg.set_value("overlay_text", "[ GAME RUNTIME LIVE ]")
        dpg.configure_item("overlay_text", color=[255, 255, 255, 255])
        dpg.set_global_font_scale(1.0)

    dpg.render_dearpygui_frame()

winsound.PlaySound(None, winsound.SND_PURGE)
for name in cartridge_assets:
    if name.endswith(".wav") and os.path.exists(name): os.remove(name)
dpg.destroy_context()