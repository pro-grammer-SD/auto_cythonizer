import subprocess
import glob
import os
import shutil
from pipreqs.pipreqs import init as pipreqs_init

args = {
    '<path>': '.',
    '--force': True,
    '--encoding': 'utf-8',
    '--ignore': '',
    '--print': False,
    '--savepath': None,
    '--no-follow-links': False,
    '--use-local': False,
    '--proxy': None,
    '--pypi-server': None,
    '--diff': None,
    '--clean': None,
    '--mode': None
}

pipreqs_init(args)

# Remove old build/dist folders
for folder in ("dist", "build", ".hatch"):
    if os.path.exists(folder):
        shutil.rmtree(folder)

# Uninstall old version if installed
subprocess.run("pip uninstall auto_cythonizer -y", shell=True, check=True)

# Build new wheel using Hatch
subprocess.run("python -m hatch build", shell=True, check=True)

# Auto-detect latest wheel
wheels = glob.glob(os.path.join("dist", "*.whl"))
if not wheels:
    raise RuntimeError("❌ No wheel found in dist folder!")

latest_wheel = max(wheels, key=os.path.getmtime)

# Install the new wheel
subprocess.run(f"pip install --upgrade {latest_wheel}", shell=True, check=True)
print(f"✅ Installed {latest_wheel}")

# Test the CLI
subprocess.run("auto-cythonizer -h", shell=True, check=True)
