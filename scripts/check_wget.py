import subprocess
res = subprocess.run(["pgrep", "-a", "wget"], capture_output=True, text=True)
print("Running wget processes:")
print(res.stdout)
