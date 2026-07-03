## Compiling your game

Before anything, you need to install **pyinstaller**. Just run this command in **powershell**:

`pip install pyinstaller`

In the JENGINE folder, you're going to see a folder called Compiler. Inside the Compiler folder, you're going to see two .py files: `compiler.py` and `player.py`. Copy those files and paste them into your game folder with the .jcode scripts, .obj 3d models and .wav sounds. After you paste the files, run `compiler.py`. After it finishes its job, you're going to see a folder called MyCompiledGame. Inside the MyCompiledGame folder, you're going to see two files: `player.exe` and `game.ore`. To play your game, run `Player.exe`.