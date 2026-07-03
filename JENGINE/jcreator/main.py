# main.py
import os
import sys
import time
import dearpygui.dearpygui as dpg
from engine_state import state
from jcode_interpreter import JCodeInterpreter
from renderer import EngineRenderer

class ScriptManager:
    def __init__(self):
        self.threads = []

    def spawn(self, filename):
        try:
            interpreter = JCodeInterpreter(filename)
            self.threads.append(interpreter)
        except Exception as e:
            self.crash_engine(str(e))

    def update(self, delta_time):
        if state.display_text_duration > 0:
            state.display_text_duration -= delta_time
            if state.display_text_duration <= 0:
                state.display_text = ""

        active_threads = []
        for script in self.threads:
            if script.is_terminated:
                continue

            if script.waiting_for_touch:
                obj1, obj2 = script.waiting_for_touch
                if obj1 in state.active_objects and obj2 in state.active_objects:
                    o1_pos = (state.active_objects[obj1]["x"], state.active_objects[obj1]["y"])
                    o2_pos = (state.active_objects[obj2]["x"], state.active_objects[obj2]["y"])
                    
                    if abs(o1_pos[0] - o2_pos[0]) < 1.0 and abs(o1_pos[1] - o2_pos[1]) < 1.0:
                        script.waiting_for_touch = None
                        script.pc += 1
                    else:
                        active_threads.append(script)
                        continue
                else:
                    active_threads.append(script)
                    continue

            try:
                status = script.step()
                if status == "CLOSE":
                    stop_game_simulation()
                    return
                elif isinstance(status, tuple) and status[0] == "RUN_SCRIPT":
                    self.spawn(status[1])
                    script.pc += 1
            except Exception as e:
                self.crash_engine(str(e))
                return

            if not script.is_terminated:
                active_threads.append(script)
        self.threads = active_threads

    def crash_engine(self, error_msg):
        stop_game_simulation()
        show_error_modal("Runtime Fatal Crash", error_msg)

script_manager = ScriptManager()
renderer = EngineRenderer()

def load_project_folder(folder_path):
    base_file = os.path.join(folder_path, "BASE.jcode")
    if not os.path.exists(base_file):
        show_error_modal("Missing Entry Point", "Engine Initialization Failed!\n'BASE.jcode' was not found.")
        return False
    state.project_dir = folder_path
    return True

def start_game_simulation():
    state.reset_runtime_state()
    script_manager.threads.clear()
    state.is_game_running = True
    dpg.configure_item("runtime_status_indicator", default_value="STATUS: RUNNING SIMULATION", color=[100, 255, 100])
    script_manager.spawn("BASE.jcode")

def stop_game_simulation():
    state.reset_runtime_state()
    
    try:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass
        
    dpg.configure_item("runtime_status_indicator", default_value="STATUS: DEV WORKSPACE IDLE", color=[255, 180, 50])

def folder_selected_callback(sender, app_data):
    chosen_dir = app_data['current_path']
    if load_project_folder(chosen_dir):
        dpg.configure_item("editor_workspace_window", show=True)
        dpg.configure_item("launcher_window", show=False)

def show_error_modal(title, message):
    if dpg.does_item_exist("error_popup_modal"):
        dpg.delete_item("error_popup_modal")
    with dpg.window(label=title, modal=True, tag="error_popup_modal"):
        dpg.add_text(message, color=[255, 90, 90])
        dpg.add_button(label="Acknowledge", width=120, callback=lambda: dpg.configure_item("error_popup_modal", show=False))

dpg.create_context()
dpg.create_viewport(title="2.5D Custom Game Engine Workspace", width=1280, height=760)

with dpg.file_dialog(directory_selector=True, show=False, callback=folder_selected_callback, id="engine_folder_picker", width=600, height=400):
    dpg.add_file_extension(".*")

with dpg.window(label="Boot Launcher", tag="launcher_window", width=420, height=200, no_resize=True, no_move=True):
    dpg.add_text("Welcome Developer!")
    dpg.add_spacer(height=15)
    dpg.add_button(label="Select Project Directory", callback=lambda: dpg.show_item("engine_folder_picker"), width=240, height=45)

with dpg.window(label="Developer Workspace Panel", tag="editor_workspace_window", show=False, no_bring_to_front_on_focus=True):
    with dpg.menu_bar():
        with dpg.menu(label="Project"):
            dpg.add_menu_item(label="Quit", callback=lambda: sys.exit())

    with dpg.group(horizontal=True):
        dpg.add_button(label="▶ RUN 'BASE.jcode'", width=150, height=35, callback=start_game_simulation)
        dpg.add_button(label="⏹ STOP GAME", width=120, height=35, callback=stop_game_simulation)
        dpg.add_text("STATUS: DEV WORKSPACE IDLE", tag="runtime_status_indicator", color=[255, 180, 50])

    dpg.add_separator()

    with dpg.group(horizontal=True):
        with dpg.child_window(width=660, height=420, label="3D Viewport Target Layer"):
            dpg.add_text("", tag="text_screen_overlay")
            dpg.add_drawlist(width=640, height=360, tag="canvas_viewport_id")
            
        with dpg.child_window(width=580, height=420, label="State Telemetry"):
            dpg.add_text(tag="player_telemetry")
            dpg.add_separator()
            dpg.add_text(tag="registry_inspector_text")

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_item_pos("launcher_window", [430, 240])

last_frame_time = time.time()

while dpg.is_dearpygui_running():
    current_time = time.time()
    dt = current_time - last_frame_time
    last_frame_time = current_time

    if dpg.is_item_shown("editor_workspace_window"):
        dpg.set_item_width("editor_workspace_window", dpg.get_viewport_width())
        dpg.set_item_height("editor_workspace_window", dpg.get_viewport_height() - 25)
        dpg.set_item_pos("editor_workspace_window", [0, 0])

        if state.is_game_running:
            script_manager.update(dt)

            # --- ORIGINAL WORKING KEYBOARD CONTROLS ---
            move_speed = 12.0 * dt
            dx, dy = 0.0, 0.0
            
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
                target_px = state.clamp_position(state.player_x + dx)
                target_py = state.clamp_position(state.player_y + dy)
                can_move = True
                
                for name, obj in state.active_objects.items():
                    adjusted_obj_y = obj["y"] + 3.5  
                    
                    if abs(target_px - obj["x"]) < 1.0 and abs(target_py - adjusted_obj_y) < 1.0:
                        if obj["pushable"] == 1:
                            obj["x"] = state.clamp_position(obj["x"] + dx)
                            obj["y"] = state.clamp_position(obj["y"] + dy)
                        else:
                            can_move = False
                            
                if can_move:
                    state.player_x = target_px
                    state.player_y = target_py

        # Dynamic center coordinates calculation
        viewport_w = dpg.get_item_width("canvas_viewport_id")
        viewport_h = dpg.get_item_height("canvas_viewport_id")
        renderer.draw_3d_viewport("canvas_viewport_id", width=viewport_w, height=viewport_h)

        # Sync text overlay using safe global sizing factors (Reverted to 1.0 for Developer Mode!)
        if state.display_text:
            dpg.set_value("text_screen_overlay", f"TEXT SCREEN EVENT: {state.display_text}")
            dpg.configure_item("text_screen_overlay", color=[255, 255, 50])
            dpg.set_global_font_scale(1.0)  # Fixed: Stays normal so the sidebars don't break!
        else:
            dpg.set_value("text_screen_overlay", "[ VIEWPORT DRAW CANVAS ]")
            dpg.configure_item("text_screen_overlay", color=[255, 255, 255])
            dpg.set_global_font_scale(1.0)  # Always normal scale in editor mode

        # Sync readouts
        dpg.set_value("player_telemetry", f"Player Matrix Configuration:\n - Model: {state.player_model}\n - Input Mod: {state.player_movetype.upper()}\n - Plane Coordinate Vector: ({state.player_x:.2f}, {state.player_y:.2f})\n - Cam View Mode: Mode {state.camera_mode}")
        
        obj_registry_dump = "ACTIVE SURFACE ENTITY MAP:\n"
        for name, data in state.active_objects.items():
            obj_registry_dump += f"\n📦 Reference: '{name}'\n ├── Mesh: {data['model']}\n ├── Push Physics: {bool(data['pushable'])}\n └── Grid Vector: ({data['x']:.1f}, {data['y']:.1f})\n"
        dpg.set_value("registry_inspector_text", obj_registry_dump if state.active_objects else "ACTIVE SURFACE ENTITY MAP:\n\n[ Empty Registry Matrix ]")

    dpg.render_dearpygui_frame()

dpg.destroy_context()