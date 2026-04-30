import subprocess
res = subprocess.run(["pgrep", "-af", "python3"], capture_output=True, text=True)
print("Running Python processes:")
print(res.stdout)
