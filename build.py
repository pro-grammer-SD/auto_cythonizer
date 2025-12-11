import subprocess
import glob
import os
import shutil

# Remove existing dist folder
if os.path.exists("dist"):
    shutil.rmtree("dist")

# Uninstall old version
subprocess.run("pip uninstall auto_cythonizer -y", shell=True, check=True)

# Build wheel with Hatch
subprocess.run("python -m hatch build", shell=True, check=True)

# Auto-detect latest wheel
wheels = glob.glob(os.path.join("dist", "*.whl"))
if not wheels:
    raise RuntimeError("No wheel found in dist folder!")

latest_wheel = max(wheels, key=os.path.getmtime)

# Install the new wheel
subprocess.run(f"pip install --upgrade {latest_wheel}", shell=True, check=True)
print(f"✅ Installed {latest_wheel}")

# Test the library CLI
subprocess.run("auto-cythonizer -h", shell=True, check=True)
