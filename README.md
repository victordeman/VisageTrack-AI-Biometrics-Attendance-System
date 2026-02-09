# VisageTrack AI - Face Recognition Attendance System

**Record attendance with your face** — a touchless, secure, and efficient web-based attendance tracking prototype using facial recognition.

This project is a full-stack prototype that allows users to **record attendance with your face** via a laptop webcam. It includes:

- Modern, responsive frontend (inspired by VisageTrack design)
- Flask backend for face enrollment and recognition
- Real-time facial recognition using `face_recognition` and OpenCV
- Basic liveness detection (motion check between frames)
- SQLite database for storing encrypted face embeddings and attendance logs
- JWT-based authentication (basic implementation)
- Touchless clock-in experience

Perfect for educational institutions, small offices, or research projects — especially in resource-constrained environments like many parts of Nigeria.

## Features

- **Enroll Face**: Capture multiple images → generate and encrypt face embedding
- **Clock In / Record Attendance with Your Face**: Live webcam preview → capture frame → send to backend → verify identity → log attendance
- **Liveness Check**: Prevents photo/video spoofing with basic motion detection
- **Privacy**: Stores only encrypted numerical embeddings (not photos)
- **Admin-friendly**: Attendance logs stored in SQLite (easy to query/export)
- **Responsive UI**: Tailwind CSS + dark mode support
- **Local-first**: Runs entirely on your laptop (no cloud required for development)

## Tech Stack

**Frontend**
- HTML5 + Tailwind CSS (via CDN)
- JavaScript (vanilla + Feather Icons)
- WebRTC for webcam access

**Backend**
- Python 3.10+
- Flask + Flask-RESTful + Flask-JWT-Extended
- face_recognition (dlib-based embeddings)
- OpenCV (image processing)
- SQLite (database)
- cryptography (Fernet encryption for embeddings)

## Prerequisites

- Python 3.10 or higher
- Git
- Webcam-enabled laptop/computer
- (Windows users may need Visual Studio Build Tools for dlib compilation)

## Installation & Local Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/victordeman/Face-Capture-System.git
cd Face-Capture-System
```
## Step-by-Step Integration Process

### 2. Clone the Repository Locally (If Not Already Done):

```
Navigate to your project folder: cd path/to/Face-Capture-System.
If not cloned: git clone https://github.com/victordeman/Face-Capture-System.git.

Create a virtual environment: python -m venv venv (activate: venv\Scripts\activate on Windows, source venv/bin/activate on macOS/Linux).
Install dependencies: pip install flask flask-restful flask-jwt-extended face_recognition opencv-python sqlite3 cryptography.
flask: Web framework.
flask-restful: For APIs.
flask-jwt-extended: For authentication.
face_recognition: For embeddings (installs dlib automatically).
opencv-python: For image processing.
cryptography: For encryption.
```

Create requirements.txt: pip freeze > requirements.txt (add to repo for deployment).

### 1. Create Backend Files:

```
In the root folder, create app.py (main Flask app).
Create a database.db file (SQLite will generate it).
Update frontend JS (script.js) to send requests to backend APIs (e.g., /api/enroll, /api/recognize).
Add liveness detection logic (basic motion check) in backend.

Implement the Backend Code:
Copy the code below into the respective files.
This backend serves the index.html as the root, handles APIs, and records attendance with your face.

### 2. Test Locally:

```
Run: python app.py.
Open http://127.0.0.1:5000 in browser.
Test enrollment: Navigate to enroll form, capture face—it sends to backend to store embedding.
Test attendance: Capture frame, backend recognizes and logs if match, recording attendance with your face.

### 3. Commit and Push Changes:

```
git add .
git commit -m "Integrate Flask backend for face recognition and attendance logging"
git push origin main

### 4. Deploy to a Hosting Platform (e.g., Render):

```
Go to render.com, sign up, create a new "Web Service".
Connect your GitHub repo.
Set: Runtime = Python, Build Command = pip install -r requirements.txt, Start Command = python app.py.
Environment variables: None needed initially.
Deploy—Render builds and hosts. URL: e.g., https://your-app.onrender.com.
For webcam: Ensure HTTPS (Render provides it) as browsers require secure context for camera access.
In Nigeria, use a VPN if deployment fails due to network issues.

### 5. Troubleshooting:

```
Errors with dlib/face_recognition: Ensure CMake is installed (for building dlib).
Database issues: Check permissions.
Webcam: Frontend must use HTTPS for production.
Scale: For production, migrate to PostgreSQL and add worker queues.
