# engine_state.py

class EngineState:
    def __init__(self):
        self.project_dir = None
        self.is_game_running = False
        
        # Player Component
        self.player_model = None
        self.player_movetype = "wasd"
        self.player_x = 20.0  # Default to the middle of the 40-stud plane
        self.player_y = 20.0
        
        # Scene Database
        self.active_objects = {}  # {obj_name: {"model": str, "pushable": 0/1, "x": float, "y": float}}
        self.camera_mode = 1      # 1 = 1st person, 3 = 3rd person
        
        # UI Messaging Buffer
        self.display_text = ""
        self.display_text_duration = 0.0

        # Camera Orbit Controls
        self.cam_yaw = -90.0  # Facing forward down the grid
        self.cam_pitch = -30.0 # Looking slightly downward at the plane
        self.cam_distance = 12.0 # How far back the camera sits

    def reset_runtime_state(self):
        self.is_game_running = False
        self.player_model = None
        self.player_movetype = "wasd"
        self.player_x = 20.0
        self.player_y = 20.0
        self.active_objects.clear()
        self.camera_mode = 1
        self.display_text = ""
        self.display_text_duration = 0.0

    def clamp_position(self, value):
        return max(0.0, min(float(value), 40.0))

state = EngineState()