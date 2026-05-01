import subprocess
res = subprocess.run(["pip3", "--version"], capture_output=True, text=True)
print(res.stdout)
import packaging
print(f"Packaging version: {packaging.__version__}")
