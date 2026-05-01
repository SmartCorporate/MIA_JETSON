import subprocess
res = subprocess.run(["pgrep", "-a", "pip"], capture_output=True, text=True)
print("Running pip processes:")
print(res.stdout)
res = subprocess.run(["pgrep", "-a", "cc1plus"], capture_output=True, text=True)
print("Running compiler processes:")
print(res.stdout)
