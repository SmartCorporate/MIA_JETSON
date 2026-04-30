import subprocess
try:
    res = subprocess.run(["espeak", "--voices"], capture_output=True, text=True)
    print(res.stdout)
except:
    pass
