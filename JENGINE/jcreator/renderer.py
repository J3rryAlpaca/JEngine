# renderer.py
import os
import math
import dearpygui.dearpygui as dpg
from engine_state import state

class OBJModel:
    def __init__(self, filename):
        self.vertices = []
        self.faces = []
        self.loaded = False
        
        if state.project_dir:
            path = os.path.join(state.project_dir, filename)
            if os.path.exists(path):
                self.parse_obj(path)
                self.loaded = True

    def parse_obj(self, path):
        with open(path, 'r') as f:
            for line in f:
                if line.startswith('v '):
                    parts = line.split()
                    self.vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                elif line.startswith('f '):
                    parts = line.split()
                    face = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                    self.faces.append(face)

class EngineRenderer:
    def __init__(self):
        self.model_cache = {}

    def get_model(self, filename):
        if filename not in self.model_cache:
            self.model_cache[filename] = OBJModel(filename)
        return self.model_cache[filename]

    def draw_3d_viewport(self, drawlist_tag, width=640, height=360):
        if not dpg.does_item_exist(drawlist_tag):
            return
            
        dpg.delete_item(drawlist_tag, children_only=True)
        
        px, py = state.player_x, state.player_y
        cam_mode = state.camera_mode
        
        # Original working 3rd person tracking position values
        cx, cy, cz = px, 5.0, py + 10.0
        if cam_mode == 1:
            cx, cy, cz = px, 1.5, py + 0.1

        def project(x, y, z):
            """Restored stable original 3D perspective projection."""
            rx = x - cx
            ry = y - cy
            rz = z - cz
            
            if rz >= -0.1: 
                rz = -0.1
                
            fov = 300.0
            screen_x = int((rx * fov / -rz) + (width / 2))
            screen_y = int((-ry * fov / -rz) + (height / 2))
            return [screen_x, screen_y]

        # --- 1. DRAW 40-STUD SURFACE PLANE GRID ---
        for z_line in range(0, 41, 4):
            dpg.draw_line(project(0, 0, z_line), project(40, 0, z_line), color=[80, 80, 80, 255], parent=drawlist_tag)
        for x_line in range(0, 41, 4):
            dpg.draw_line(project(x_line, 0, 0), project(x_line, 0, 40), color=[80, 80, 80, 255], parent=drawlist_tag)

        # --- 2. DRAW REGISTERED OBJECTS WITH TRUE MESH GEOMETRY ---
        for name, data in state.active_objects.items():
            ox, oz = data["x"], data["y"]
            color = [230, 90, 90, 255] if data["pushable"] else [130, 130, 130, 255]
            
            model = self.get_model(data["model"])
            if model.loaded and model.vertices:
                for face in model.faces:
                    pts = []
                    for v_idx in face:
                        if v_idx < len(model.vertices):
                            v = model.vertices[v_idx]
                            pts.append(project(ox + v[0]*0.2, v[1]*0.2, oz + v[2]*0.2))
                    if len(pts) >= 3:
                        dpg.draw_polyline(pts, color=color, thickness=1, parent=drawlist_tag)
            else:
                b0 = project(ox-0.5, 0, oz-0.5); b1 = project(ox+0.5, 0, oz-0.5)
                b2 = project(ox+0.5, 0, oz+0.5); b3 = project(ox-0.5, 0, oz+0.5)
                t0 = project(ox-0.5, 1, oz-0.5); t1 = project(ox+0.5, 1, oz-0.5)
                t2 = project(ox+0.5, 1, oz+0.5); t3 = project(ox-0.5, 1, oz+0.5)
                dpg.draw_quad(b0, b1, b2, b3, color=color, parent=drawlist_tag)
                dpg.draw_quad(t0, t1, t2, t3, color=color, parent=drawlist_tag)

        # --- 3. DRAW PLAYER VISUAL CUBE ---
        if cam_mode == 3:
            p_color = [60, 160, 255, 255]
            pb0 = project(px-0.4, 0, py-0.4); pb1 = project(px+0.4, 0, py-0.4)
            pb2 = project(px+0.4, 0, py+0.4); pb3 = project(px-0.4, 0, py+0.4)
            pt0 = project(px-0.4, 1.6, py-0.4); pt1 = project(px+0.4, 1.6, py-0.4)
            pt2 = project(px+0.4, 1.6, py+0.4); pt3 = project(px-0.4, 1.6, py+0.4)
            dpg.draw_quad(pb0, pb1, pb2, pb3, color=p_color, parent=drawlist_tag)
            dpg.draw_quad(pt0, pt1, pt2, pt3, color=p_color, parent=drawlist_tag)