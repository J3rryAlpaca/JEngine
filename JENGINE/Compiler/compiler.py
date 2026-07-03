# compiler.py
import os
import struct
import subprocess
import shutil

def compile_game():
    entry_script = "BASE.jcode"
    output_ore_filename = "game.ore"
    
    if not os.path.exists(entry_script):
        print(f"❌ Error: Cannot find '{entry_script}'")
        return
        
    scripts_to_scan = [entry_script]
    required_files = set([entry_script])

    # Scan scripts recursively for runscript dependencies
    while scripts_to_scan:
        current_script = scripts_to_scan.pop(0)
        if not os.path.exists(current_script):
            continue
            
        with open(current_script, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("//"): 
                    continue
                tokens = line.split()
                if not tokens: 
                    continue
                cmd = tokens[0].lower()
                
                if cmd in ["playermodel", "bgmloop"] and len(tokens) > 1:
                    required_files.add(tokens[1])
                elif cmd == "assignobj" and len(tokens) > 2:
                    required_files.add(tokens[2])
                elif cmd == "runscript" and len(tokens) > 1:
                    script_name = tokens[1]
                    if script_name not in required_files:
                        required_files.add(script_name)
                        scripts_to_scan.append(script_name)

    file_list = list(required_files)
    print(f"📦 Packing assets into cartridge: {file_list}")
    
    file_payloads = []
    for file_name in file_list:
        if os.path.exists(file_name):
            with open(file_name, 'rb') as f_in:
                file_payloads.append((file_name, f_in.read()))
        else:
            print(f"❌ Dependency Missing from workspace: {file_name}")
            return

    # Write pure unpadded Narbacular .ore format
    with open(output_ore_filename, 'wb') as ore_out:
        ore_out.write(struct.pack("<I", len(file_payloads)))
        for name, data in file_payloads:
            name_bytes = name.encode('utf-8')
            ore_out.write(struct.pack("B", len(name_bytes)))
            ore_out.write(name_bytes)
            ore_out.write(struct.pack("<I", len(data)))
        for name, data in file_payloads:
            ore_out.write(data)
            
    print("🚀 game.ore cartridge generated successfully.")

    if not os.path.exists("player.py"):
        print("❌ Error: player.py missing")
        return

    print("⚡ Building standalone player.exe runtime pipeline...")
    try:
        subprocess.run(["pyinstaller", "--onefile", "--noconsole", "player.py"], check=True)
        
        dist_dir = "MyCompiledGame"
        os.makedirs(dist_dir, exist_ok=True)
        
        shutil.move(os.path.join("dist", "player.exe"), os.path.join(dist_dir, "player.exe"))
        shutil.move(output_ore_filename, os.path.join(dist_dir, output_ore_filename))
        
        if os.path.exists("build"): shutil.rmtree("build")
        if os.path.exists("dist"): shutil.rmtree("dist")
        if os.path.exists("player.spec"): os.remove("player.spec")
        
        print(f"\n🎉 DONE! Run player.exe in the folder: '{dist_dir}'")
    except Exception as e:
        print(f"❌ Build failed: {e}")

if __name__ == "__main__":
    compile_game()