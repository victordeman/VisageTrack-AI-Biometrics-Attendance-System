# VisageTrack-AI-Biometrics-Attendance-System


**VisageTrack-AI-Biometrics-Attendance-System
** is a touchless, secure, and efficient biometric attendance tracking system. Leveraging advanced facial recognition technology, it provides a seamless way for organizations to manage attendance while ensuring data privacy and security. Check it out here https://visage-livid.vercel.app/index.html

## 🚀 Features

- **Biometric Enrollment**: 
  - Effortless user registration with a 10-frame image capture process.
  - Detailed employee profiles including:
    - **Personal Info**: First/Last Name, Date of Birth, Email.
    - **Professional Info**: Department, Job Designation.
    - **Contact Info**: Home Address.
  - Built-in **Liveness Detection** to prevent spoofing using photos or videos.
- **Face Recognition Attendance**:
  - Real-time clock-in via webcam.
  - High-speed matching using `dlib`-based facial embeddings.
- **Security & Privacy**:
  - **Encrypted Embeddings**: Raw images are not stored; only encrypted numerical embeddings are kept using Fernet symmetric encryption.
  - **Secure Authentication**: JWT-based session management for secure API access.
  - **Password Hashing**: User passwords are securely hashed using Werkzeug.
- **Admin Dashboard**:
  - **Restricted Access**: Only users with the **Administrator** role can access the dashboard.
  - Comprehensive user management (Add/Delete users).
  - Real-time attendance logs and system statistics.
- **Modern UI**:
  - Clean, responsive interface built with Tailwind CSS.
  - Dark Mode support with user preference persistence.

## 🛠 Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-JWT-Extended, SQLite.
- **Computer Vision**: `face_recognition` (dlib), OpenCV.
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript, Feather Icons.
- **Security**: Cryptography (Fernet), Werkzeug Security.

## ⚙️ Installation

### 0. Prerequisites
The system requires several tools to be installed on your machine for the biometric components (`dlib`) to build correctly:
- **Python 3.10+**
- **CMake**: Used to build the C++ core of dlib.
- **C++ Compiler**:
  - **Linux**: `gcc`/`g++` (usually via `build-essential`)
  - **macOS**: Clang (via Xcode Command Line Tools)
  - **Windows**: Visual Studio Build Tools with "Desktop development with C++" workload.

### 1. Clone the Repository
```bash
git clone https://github.com/victordeman/VisageTrack-AI-Biometrics-Attendance-System.git
cd VisageTrack-AI-Biometrics-Attendance-System
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
cd backend

# If on Linux/macOS and dlib installation fails via pip/uv, use the patch script:
chmod +x install_dlib.sh
./install_dlib.sh

# Then install the remaining dependencies
pip install -r requirements.txt

# (Optional) Verify your environment
python verify_env.py
```
*Note: The `install_dlib.sh` script is specifically for Linux/macOS environments experiencing CMake version conflicts with dlib's bundled pybind11. It automates downloading and patching the source before installation.*

## 🚀 Running the Application

The system is split into a **Backend API** and a **Frontend**.

### 1. Start the Backend API
```bash
cd api
python index.py
```

### 2. Host the Frontend
You can host the `frontend` directory using any static file server. For development:
```bash
cd frontend
python -m http.server 8000
```

### 3. Access the App
Open [http://localhost:8000](http://localhost:8000) in your web browser.

## ☁️ Vercel Deployment

This application is ready for deployment on [Vercel](https://vercel.com/).

### Important Considerations for Serverless
*   **Ephemeral Filesystem**: Serverless functions have a read-only filesystem except for the `/tmp` directory. Data stored in `/tmp` (SQLite DB and uploads) is **temporary** and will be lost when the function instance restarts.
*   **Persistence**: For a production-ready system, you **must** migrate to a persistent database (e.g., PostgreSQL via Neon or Supabase) and external storage (e.g., AWS S3 or Vercel Blob).

### Steps to Deploy
1.  **Environment Variables**: Set the `ENCRYPTION_KEY` environment variable in Vercel to a stable base64 string (generate one with `Fernet.generate_key()`). This prevents data from becoming unreadable if the function restarts and generates a new key.
2.  **Deployment**: Push this repository to GitHub and connect it to Vercel. Vercel will automatically detect the `vercel.json` and `requirements.txt`.

### Troubleshooting `dlib` Build Failures
`face_recognition` depends on `dlib`, which can be difficult to build in constrained environments like Vercel (due to memory limits or missing C++ compilers).
*   **Memory Issues**: If the build fails with an "Out of Memory" or "Killed" error, Vercel's standard build environment may not be sufficient.
*   **Alternative Platforms**: If you encounter persistent `dlib` build issues on Vercel, we recommend deploying using **Docker** on platforms like:
    *   **AWS App Runner**
    *   **Google Cloud Run**
    *   **Railway** (using their Docker support)
    *   **DigitalOcean App Platform**

## 👤 Default Credentials

- **Admin**: `admin@ex.com` / `pass123`
- **Employee**: `employee@ex.com` / `pass123`

## 📁 Project Structure

- `api/index.py`: Main Flask backend handling API routes and biometric processing.
- `frontend/script.js`: Modular frontend logic for camera handling, API calls, and UI updates.
- `frontend/index.html`: Login and landing page.
- `frontend/dashboard.html`: Employee portal for viewing attendance logs.
- `frontend/attendance.html`: Public clock-in interface.
- `frontend/enroll.html`: User registration and biometric capture interface.
- `frontend/admin.html`: Administrative management dashboard.
- `frontend/components/`: Reusable frontend components (e.g., Navbar).

## 🛠️ Troubleshooting

### "cmake not found" or "not in PATH"
This is a common issue on Windows. Ensure that you selected the option to **"Add CMake to the system PATH"** during installation. If you've already installed it, you may need to add it manually:
1. Search for "Edit the system environment variables" in Windows search.
2. Click "Environment Variables".
3. Under "System variables", select "Path" and click "Edit".
4. Add the path to your CMake bin directory (e.g., `C:\Program Files\CMake\bin`).
5. Restart your terminal.

### "No module named 'face_recognition'"
Ensure you have activated your virtual environment before running the application. If you just installed dependencies, try restarting your terminal.

### dlib installation fails on Linux/macOS
Ensure you have run `./install_dlib.sh` inside the `api/` directory. This script handles the necessary patches for modern CMake compatibility.

## 🔒 Security Note

This project is a prototype. For production use:
- Ensure the application is served over **HTTPS** (required for camera access in most browsers).
- Migrate from SQLite to a production-grade database like PostgreSQL.
- Implement more robust liveness detection mechanisms.
- Secure the `encryption.key` and `JWT_SECRET_KEY` using environment variables.

---
Developed with ❤️ by [Victor Deman](https://github.com/victordeman)
