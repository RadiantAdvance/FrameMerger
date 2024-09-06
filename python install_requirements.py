import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required libraries
required_libraries = [
    "tkinter",
    "ttkbootstrap",
    "opencv-python",
    "os",
    "json",
    "subprocess",
    "threading"
]

# Install each required library
for library in required_libraries:
    try:
        install(library)
        print(f"{library} installed successfully.")
    except Exception as e:
        print(f"Error installing {library}: {e}")

print("All libraries installed.")
