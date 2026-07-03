# JCode Scripting Language Documentation

Welcome to the official **JCode** developer documentation. It is a programming language I built in literally 15 minutes for my game engine. Scripts are executed line-by-line via parallel execution threads and can be compiled into raw binary `.ore` cartridges for standalone deployment (yes I play narbacular drop).

---

## 🛠 Command Reference Matrix

### 1. Player & Input Configuration
* **`movetype <mode>`**
  * **Description:** Selects the active player input scheme.
  * **Parameters:** `wasd` (Standard WASD movement) or `arrow` (Arrow keys movement).
  * **Example:** `movetype wasd`

* **`setplayerpos <axis> <coordinate>`**
  * **Description:** Snaps the player directly to a coordinate on the plane (one axis at a time).
  * **Parameters:** * `axis`: `x` or `y`
    * `coordinate`: Float value from `0.0` to `40.0` (automatically clamped).
  * **Example:** `setplayerpos x 20.0`

---

### 2. Camera Configuration
* **`cammode <mode>`**
  * **Description:** Toggles the perspective projection matrix for the engine's viewport canvas.
  * **Parameters:** `1` (First-Person Eye-Level Camera) or `3` (Third-Person Isometric Camera tracking behind the player).
  * **Example:** `cammode 3`

---

### 3. Entity Management & Physics
* **`assignobj <id> <filename>.obj`**
  * **Description:** Spawns a mesh entity inside the engine environment. If the object ID already exists, it swaps the active model mesh layout instead.
  * **Parameters:** * `id`: Unique alphanumeric string identifier.
    * `<filename>.obj`: Path to the raw Wavefront 3D wireframe mesh.
  * **Example:** `assignobj CompanionCube box.obj`

* **`setobjpos <id> <axis> <coordinate>`**
  * **Description:** Manually teleports an instantiated object to a specific location on the grid floor.
  * **Parameters:**
    * `id`: Target alphanumeric object identifier.
    * `axis`: `x` or `y`
    * `coordinate`: Float value from `0.0` to `40.0`.
  * **Example:** `setobjpos CompanionCube y 15.5`

* **`objpushable <id> <state>`**
  * **Description:** Toggles the rigid body collision physics rules for an object. When pushable, player movement handles line vector offset displacement updates.
  * **Parameters:** `1` (True, object can be pushed around) or `0` (False, acts as a static collision wall).
  * **Example:** `objpushable CompanionCube 1`

---

### 4. Logic Control & Script Threading
* **`waituntiltouch <id1> <id2>`**
  * **Description:** Non-blocking script engine loop yield. Pauses execution of the *current* script thread until the bounding boxes of the two objects touch on the grid map plane. *Note: Does not freeze player inputs or parallel running script tracks.*
  * **Parameters:** Alphanumeric identifier names for two instantiated objects.
  * **Example:** `waituntiltouch CompanionCube WinSwitch`

* **`runscript <filename>.jcode`**
  * **Description:** Multi-threaded task launcher. Automatically spawns an entirely new execution runner to handle a secondary script file side-by-side without stopping the current one.
  * **Example:** `runscript level2_mechanics.jcode`

* **`end`**
  * **Description:** Explicit script thread terminator. Instantly stops execution and cleans the active execution task runner from the RAM pipeline stack.
  * **Example:** `end`

* **`closegame`**
  * **Description:** Universal program override exit. In developer mode, it ends execution and safely returns you to the tool panel IDE. In the compiled standalone player binary, it closes the entire window out instantly.
  * **Example:** `closegame`

---

### 5. Audiovisual Overlay Effects
* **`displaytext "<string>"`**
  * **Description:** Flashes a high-contrast text layout message string across the screen viewport. 
  * **Duration Rule:** Automatically calculates screen time duration using the letter translation length formula: `number of characters / 4 = seconds visible`.
  * **Formatting Note:** Text scale rendering triggers at standard size inside the editor, but automatically inflates to a massive **5x scale marquee look** when running inside the standalone binary package.
  * **Example:** `displaytext "PUZZLE SOLVED!"`

* **`bgmloop <filename>.wav`**
  * **Description:** Hands a background music track call to the Windows audio array. The audio stream automatically registers as asynchronous to prevent frame lag and loops indefinitely.
  * **Example:** `bgmloop narbacular_up.wav`

---

## Code Implementation Examples

### Example 1: `BASE.jcode` (Core Setup and Puzzle Switch)
```text
// Initialization Configurations
movetype wasd
cammode 3
bgmloop narbacular_up.wav

// Set up Player Starter Location
setplayerpos x 5.0
setplayerpos y 5.0

// Load Map Obstacles and Logic Triggers
assignobj Blockade wall_pillar.obj
setobjpos Blockade x 20.0
setobjpos Blockade y 20.0
objpushable Blockade 0

assignobj WeightedBox cube.obj
setobjpos WeightedBox x 10.0
setobjpos WeightedBox y 10.0
objpushable WeightedBox 1

assignobj WinSwitch button_pad.obj
setobjpos WinSwitch x 30.0
setobjpos WinSwitch y 30.0
objpushable WinSwitch 0

// Boot custom particle track or map layout rules on a parallel thread
runscript ambient_fx.jcode

// Yield Execution Sequence until conditions are reached
waituntiltouch WeightedBox WinSwitch

// Win State Triggers
displaytext "STAGE CLEAR!"
waituntiltouch Blockade WinSwitch // Placeholder pause or layout delay
closegame