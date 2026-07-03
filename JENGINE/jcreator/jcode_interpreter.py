# jcode_interpreter.py
import os
import re
from engine_state import state

class JCodeInterpreter:
    def __init__(self, filename):
        self.filename = filename
        self.filepath = os.path.join(state.project_dir, filename)
        self.lines = []
        self.pc = 0  # Program Counter tracking line index
        self.is_terminated = False
        self.waiting_for_touch = None  # Holds tuple (obj1, obj2) when yielding
        
        self.load_file()

    def load_file(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Runtime Error: JCode script '{self.filename}' was not found.")
        with open(self.filepath, 'r') as f:
            self.lines = [line.strip() for line in f.readlines()]

    def step(self):
        """Executes a single step. Returns 'CLOSE' if closegame is executed."""
        if self.is_terminated or self.pc >= len(self.lines):
            self.is_terminated = True
            return None

        line = self.lines[self.pc]

        # 1. Bypass comments and blanks immediately
        if not line or line.startswith("//"):
            self.pc += 1
            return None

        # 2. Extract command tokens
        if 'displaytext' in line:
            tokens = line.split(' ', 1)
        else:
            tokens = line.split()

        if not tokens:
            self.pc += 1
            return None

        cmd = tokens[0].lower()

        # 3. Process Execution Tree
        if cmd == "playermodel":
            state.player_model = tokens[1]

        elif cmd == "movetype":
            state.player_movetype = tokens[1].lower()

        elif cmd == "setplayerpos":
            axis = tokens[1].lower()
            val = state.clamp_position(tokens[2])
            if axis == 'x': state.player_x = val
            elif axis == 'y': state.player_y = val

        elif cmd == "assignobj":
            obj_name = tokens[1]
            model_file = tokens[2]
            # Dynamic Creation Trigger Rule
            if obj_name not in state.active_objects:
                state.active_objects[obj_name] = {"model": model_file, "pushable": 0, "x": 0.0, "y": 0.0}
            else:
                state.active_objects[obj_name]["model"] = model_file

        # Strict Existence Validation Checking
        elif cmd in ["objpushable", "setobjpos", "waituntiltouch"]:
            obj_name = tokens[1]
            if obj_name not in state.active_objects:
                raise RuntimeError(f"Critical Engine Crash: Attempted usage of undefined reference '{obj_name}' on context: '{line}'")

            if cmd == "objpushable":
                state.active_objects[obj_name]["pushable"] = int(tokens[2])
            elif cmd == "setobjpos":
                axis = tokens[2].lower()
                val = state.clamp_position(tokens[3])
                if axis == 'x': state.active_objects[obj_name]["x"] = val
                elif axis == 'y': state.active_objects[obj_name]["y"] = val
            elif cmd == "waituntiltouch":
                obj2 = tokens[2]
                if obj2 not in state.active_objects:
                    raise RuntimeError(f"Critical Engine Crash: Attempted usage of undefined reference '{obj2}' on context: '{line}'")
                # Engage Non-blocking Thread/Loop Yield state
                self.waiting_for_touch = (obj_name, obj2)
                return "YIELD"

        elif cmd == "displaytext":
            match = re.search(r'"([^"]*)"', line)
            if match:
                text = match.group(1)
                state.display_text = text
                # Letter Length Translation Formula Rule (chars / 4 = seconds duration)
                state.display_text_duration = len(text) / 4

        elif cmd == "bgmloop":
            import winsound
            
            # Grabs the file name from your script (e.g., narbacular_up.wav)
            track_name = tokens[1]
            track_path = os.path.join(state.project_dir, track_name)
            
            if os.path.exists(track_path):
                # SND_FILENAME: Finds the file path
                # SND_ASYNC: Runs in the background so your walking inputs don't freeze
                # SND_LOOP: Loops the track indefinitely
                winsound.PlaySound(track_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
                print(f"Looping track '{track_name}' as background music")
            else:
                print(f"Error: Sound asset '{track_name}' missing from project folder.")

        elif cmd == "cammode":
            state.camera_mode = int(tokens[1])

        elif cmd == "runscript":
            # Handled directly inside Script Manager
            return ("RUN_SCRIPT", tokens[1])

        elif cmd == "end":
            self.is_terminated = True
            return None

        elif cmd == "closegame":
            return "CLOSE"

        self.pc += 1
        return None