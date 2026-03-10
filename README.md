# VisageTrack-AI-Biometrics-Attendance-System


**VisageTrack-AI-Biometrics-Attendance-System
** is a touchless, secure, and efficient biometric attendance tracking system. Leveraging advanced facial recognition technology, it provides a seamless way for organizations to manage attendance while ensuring data privacy and security.

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

### 1. Clone the Repository
```bash
git clone https://github.com/victordeman/VisageTrack-AI-Biometrics-Attendance-System.git
cd Face-Capture-System
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
pip install -r requirements.txt
```
*Note: Windows users may need to install [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) for `dlib` compilation.*

## 🚀 Running the Application

1. **Initialize the Database**: The database is automatically initialized upon the first run.
2. **Start the Server**:
   ```bash
   python app.py
   ```
3. **Access the App**: Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

## ☁️ Vercel Deployment

This application is ready for deployment on [Vercel](https://vercel.com/).

### Important Considerations for Serverless
*   **Ephemeral Filesystem**: Serverless functions have a read-only filesystem except for the `/tmp` directory. Data stored in `/tmp` (SQLite DB and uploads) is **temporary** and will be lost when the function instance restarts.
*   **Persistence**: For a production-ready system, you **must** migrate to a persistent database (e.g., PostgreSQL via Neon or Supabase) and external storage (e.g., AWS S3 or Vercel Blob).

### Steps to Deploy
1.  **Environment Variables**: Set the `ENCRYPTION_KEY` environment variable in Vercel to a stable base64 string (generate one with `Fernet.generate_key()`). This prevents data from becoming unreadable if the function restarts and generates a new key.
2.  **Deployment**: Push this repository to GitHub and connect it to Vercel. Vercel will automatically detect the `vercel.json` and `requirements.txt`.

## 👤 Default Credentials

- **Admin**: `admin@ex.com` / `pass123`
- **Employee**: `employee@ex.com` / `pass123`

## 📁 Project Structure

- `app.py`: Main Flask backend handling API routes and biometric processing.
- `script.js`: Modular frontend logic for camera handling, API calls, and UI updates.
- `index.html`: Login and landing page.
- `dashboard.html`: Employee portal for viewing attendance logs.
- `attendance.html`: Public clock-in interface.
- `enroll.html`: User registration and biometric capture interface.
- `admin.html`: Administrative management dashboard.
- `components/`: Reusable frontend components (e.g., Navbar).
- `requirements.txt`: Project dependencies.

## 🔒 Security Note

This project is a prototype. For production use:
- Ensure the application is served over **HTTPS** (required for camera access in most browsers).
- Migrate from SQLite to a production-grade database like PostgreSQL.
- Implement more robust liveness detection mechanisms.
- Secure the `encryption.key` and `JWT_SECRET_KEY` using environment variables.

---
Developed with ❤️ by [Victor Deman](https://github.com/victordeman)
