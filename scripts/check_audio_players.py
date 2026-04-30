import os
import subprocess
print("Checking for mpv:")
subprocess.call(["which", "mpv"])
print("Checking for ffplay:")
subprocess.call(["which", "ffplay"])
