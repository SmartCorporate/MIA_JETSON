import subprocess
import os

variations = [
    "MIA",
    "Mee-ah",
    "Mee ah",
    "Meea",
    "Meeya",
    "Me ah",
    "M I A"
]

print("Testing pico2wave pronunciations...")
for v in variations:
    tmp = f"test_{v.replace(' ', '_').replace('-', '_')}.wav"
    print(f"Testing: {v} -> {tmp}")
    subprocess.run(["pico2wave", "-l=en-US", f"-w={tmp}", v])
    # I can't hear it, but I'll list the files
    if os.path.exists(tmp):
        print(f"  [OK] Generated {tmp}, size {os.path.getsize(tmp)}")
    else:
        print(f"  [FAIL] Failed to generate {tmp}")
