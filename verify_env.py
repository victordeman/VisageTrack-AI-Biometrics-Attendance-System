import subprocess
import sys
import importlib.util

def check_command(command):
    try:
        subprocess.run([command, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_package(package_name):
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def main():
    print("--- VisageTrack Environment Verification ---\n")

    # Check System Tools
    print("System Tools:")
    cmake_ok = check_command("cmake")
    print(f"  [ {'OK' if cmake_ok else '!!'} ] cmake")

    # Try different names for C++ compiler
    cc_ok = check_command("g++") or check_command("clang++")
    print(f"  [ {'OK' if cc_ok else '!!'} ] C++ compiler (g++ or clang++)")

    if not cmake_ok or not cc_ok:
        print("\n  Tip: Ensure cmake and a C++ compiler are installed and in your PATH.")
        print("  Windows users: Restart your terminal after adding CMake to PATH.\n")

    # Check Python Packages
    print("Python Packages:")
    packages = [
        "flask", "flask_cors", "flask_jwt_extended",
        "cv2", "dlib", "face_recognition",
        "cryptography", "werkzeug", "numpy"
    ]

    all_packages_ok = True
    for pkg in packages:
        ok = check_package(pkg)
        print(f"  [ {'OK' if ok else '!!'} ] {pkg}")
        if not ok:
            all_packages_ok = False

    if not all_packages_ok:
        print("\n  Tip: Run 'pip install -r requirements.txt' to install missing packages.")
        print("  If dlib fails to install, try running './install_dlib.sh' (Linux/macOS).")

    print("\n--- Verification Complete ---")
    if cmake_ok and cc_ok and all_packages_ok:
        print("Status: Environment looks good! 🚀")
    else:
        print("Status: Some issues were found. Please check the tips above. 🛠️")

if __name__ == "__main__":
    main()
