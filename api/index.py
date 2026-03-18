from flask import Flask, request, jsonify, session, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
import sqlite3
import numpy as np
try:
    import face_recognition
except Exception as e:
    print(f"Error importing face_recognition: {e}")
    face_recognition = None

try:
    import cv2
except Exception as e:
    print(f"Error importing cv2: {e}")
    cv2 = None
from cryptography.fernet import Fernet
import os
import functools
import logging
import uuid
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
app.config['SECRET_KEY'] = 'visage-track-2026-super-secure-key-32bytes'
app.config['JWT_SECRET_KEY'] = 'visage-track-2026-super-secure-key-32bytes'
app.config['JWT_TOKEN_LOCATION'] = ['headers']

jwt = JWTManager(app)

# Environment-specific configuration
IS_VERCEL = os.environ.get('VERCEL') == '1'
# BASE_DIR should point to the root where uploads/ and database.db are
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = '/tmp' if IS_VERCEL else BASE_DIR

# Ensure uploads directory exists
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Encryption key persistence
env_key = os.environ.get('ENCRYPTION_KEY')
KEY_FILE = os.path.join(DATA_DIR, 'encryption.key')

if env_key:
    key = env_key.encode()
    logger.info("Using encryption key from environment variable.")
elif os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as f:
        key = f.read()
    logger.info(f"Using encryption key from {KEY_FILE}")
else:
    key = Fernet.generate_key()
    if not IS_VERCEL:
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
    logger.info("Generated new encryption key.")

cipher = Fernet(key)

# Database
DB_PATH = os.path.join(DATA_DIR, 'database.db')

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    logger.info(f"Initializing database at {DB_PATH}")
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
            logger.info(f"Created data directory: {DATA_DIR}")
    except Exception as e:
        logger.error(f"Failed to create data directory: {e}")

    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            email TEXT UNIQUE, 
            password TEXT, 
            role TEXT, 
                    embedding BLOB,
                    image_path TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    home_address TEXT,
                    dob TEXT,
                    department TEXT,
                    job_designation TEXT
                )''')
            c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp TEXT,
                    status TEXT
                )''')

            # Check if new columns exist
            c.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in c.fetchall()]
            cols_to_add = {
                'image_path': 'TEXT',
                'first_name': 'TEXT',
                'last_name': 'TEXT',
                'home_address': 'TEXT',
                'dob': 'TEXT',
                'department': 'TEXT',
                'job_designation': 'TEXT'
            }
            for col, col_type in cols_to_add.items():
                if col not in columns:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type}")

            # Add default admin
            c.execute("SELECT * FROM users WHERE email = ?", ('admin@ex.com',))
            if not c.fetchone():
                c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                        ('Admin', 'admin@ex.com', generate_password_hash('pass123'), 'admin'))

            # Add default employee
            c.execute("SELECT * FROM users WHERE email = ?", ('employee@ex.com',))
            if not c.fetchone():
                c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                        ('Employee', 'employee@ex.com', generate_password_hash('pass123'), 'employee'))

            conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

init_db()

# Helpers
def encode_embedding(embedding):
    return cipher.encrypt(embedding.tobytes())

def decode_embedding(encrypted):
    return np.frombuffer(cipher.decrypt(encrypted), dtype=np.float64)

# JWT Error Handlers
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({'message': 'Missing Authorization Header'}), 401

@jwt.invalid_token_loader
def invalid_token_response(callback):
    return jsonify({'message': 'Invalid Token', 'details': str(callback)}), 422

@app.before_request
def log_request_info():
    if request.path.startswith('/api/'):
        logger.info(f"API Request: {request.method} {request.path}")

@app.errorhandler(Exception)
def handle_error(e):
    if isinstance(e, HTTPException):
        return e
    
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({'message': 'An internal error occurred', 'error': str(e)}), 500

# ====================== API ROUTES ======================

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        'status': 'healthy',
        'modules': {
            'face_recognition': face_recognition is not None,
            'cv2': cv2 is not None,
            'sqlite3': True
        },
        'environment': {
            'is_vercel': IS_VERCEL,
            'data_dir': DATA_DIR
        }
    }), 200

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/logout', methods=['POST'])
def api_logout():
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'message': 'Email and password required'}), 400

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, role, password FROM users WHERE email = ?", (email,))
        user = c.fetchone()

    if user and check_password_hash(user['password'], password):
        token = create_access_token(identity=str(user['id']), additional_claims={"role": user['role']})
        return jsonify({
            'message': 'Login successful',
            'access_token': token, 
            'role': user['role']
        }), 200
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def api_user_profile():
    user_id = get_jwt_identity()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, email, role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({'message': 'User not found'}), 404
        return jsonify(dict(user)), 200

@app.route('/api/user/stats', methods=['GET'])
@jwt_required()
def api_user_stats():
    user_id = get_jwt_identity()
    # Simple mock stats for the dashboard
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as count FROM attendance WHERE user_id = ?", (user_id,))
        present_count = c.fetchone()['count']
        return jsonify({
            'present': present_count,
            'absent': 0 # For prototype simplicity
        }), 200

@app.route('/api/enroll', methods=['POST'])
@jwt_required(optional=True)
def api_enroll():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    password = request.form.get('password', 'defaultpass')
    home_address = request.form.get('home_address')
    dob = request.form.get('dob')
    department = request.form.get('department')
    job_designation = request.form.get('job_designation')
    is_admin = request.form.get('is_admin') == 'true'
    
    if not first_name or not last_name or not email:
        return jsonify({'message': 'First name, last name and email are required'}), 400

    if is_admin:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'message': 'Authentication required to create admin accounts'}), 401
        
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE id = ?", (current_user_id,))
            user = c.fetchone()
            if not user or user['role'] != 'admin':
                return jsonify({'message': 'Only administrators can create other admin accounts'}), 403

    name = f"{first_name} {last_name}"

    image_file = request.files.get('image1')
    if not image_file:
        return jsonify({'message': 'No image captured'}), 400

    filename = f"{uuid.uuid4()}_{image_file.filename}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    image_file.save(filepath)

    if face_recognition is None:
        return jsonify({'message': 'Face recognition module not available on this server'}), 503

    try:
        frame = cv2.imread(filepath)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        if not locations:
            return jsonify({'message': 'No face detected in the image'}), 400
        
        embedding = face_recognition.face_encodings(rgb, locations)[0]
        encrypted_embedding = encode_embedding(embedding)
    except Exception as e:
        logger.error(f"Error processing face: {e}")
        return jsonify({'message': 'Error processing face image'}), 500

    with get_db() as conn:
        c = conn.cursor()
        try:
            role = 'admin' if is_admin else 'employee'
            c.execute("""INSERT INTO users 
                (name, email, embedding, image_path, role, password, first_name, last_name, home_address, dob, department, job_designation) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (name, email, encrypted_embedding, filename, role, generate_password_hash(password),
                       first_name, last_name, home_address, dob, department, job_designation))
            conn.commit()
            return jsonify({'message': 'Enrollment successful', 'image': filename}), 200
        except sqlite3.IntegrityError:
            return jsonify({'message': 'Email already enrolled'}), 400

@app.route('/api/recognize', methods=['POST'])
@jwt_required()
def api_recognize():
    if face_recognition is None:
        return jsonify({'message': 'Face recognition module not available on this server'}), 503

    if 'image' not in request.files:
        return jsonify({'message': 'No image file'}), 400

    image_file = request.files['image']
    file_bytes = image_file.read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return jsonify({'message': 'Invalid image'}), 400

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb)
    if not locations:
        return jsonify({'message': 'No face detected'}), 400

    new_embedding = face_recognition.face_encodings(rgb, locations)[0]

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, embedding FROM users WHERE embedding IS NOT NULL")
        users = c.fetchall()

        for user in users:
            try:
                stored = decode_embedding(user['embedding'])
                distance = face_recognition.face_distance([stored], new_embedding)[0]
                if distance < 0.6:
                    c.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, datetime('now'), 'present')", (user['id'],))
                    conn.commit()
                    return jsonify({'message': 'Attendance recorded', 'user_id': user['id']}), 200
            except Exception as e:
                logger.error(f"Error matching face: {e}")

    return jsonify({'message': 'Face not recognized'}), 401

@app.route('/api/admin/stats', methods=['GET'])
@jwt_required()
def api_admin_stats():
    user_id = get_jwt_identity()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403

        c.execute("SELECT COUNT(*) as count FROM users")
        user_count = c.fetchone()['count']
        c.execute("SELECT COUNT(*) as count FROM attendance")
        log_count = c.fetchone()['count']
        
        return jsonify({
            'message': 'Stats retrieved successfully',
            'user_count': user_count,
            'log_count': log_count
        }), 200

@app.route('/api/logs', methods=['GET'])
@app.route('/api/admin/attendance', methods=['GET'])
@jwt_required()
def api_admin_attendance():
    user_id = get_jwt_identity()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        
        if not user:
            return jsonify({'message': 'User not found', 'logs': []}), 404

        if user['role'] == 'admin':
            c.execute("SELECT a.id, u.name, a.timestamp, a.status FROM attendance a JOIN users u ON a.user_id = u.id ORDER BY a.timestamp DESC")
        else:
            c.execute("SELECT a.id, u.name, a.timestamp, a.status FROM attendance a JOIN users u ON a.user_id = u.id WHERE u.id = ? ORDER BY a.timestamp DESC", (user['id'],))
        
        logs = [dict(row) for row in c.fetchall()]
        
    return jsonify({'message': 'Logs retrieved successfully', 'logs': logs}), 200

@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def api_admin_users():
    user_id = get_jwt_identity()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403

        c.execute("SELECT id, name, email, role, image_path FROM users")
        users = [dict(row) for row in c.fetchall()]
    return jsonify({'message': 'Users retrieved successfully', 'users': users}), 200

@app.route('/api/admin/users/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def api_admin_delete_user(target_user_id):
    user_id = get_jwt_identity()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403

        c.execute("DELETE FROM attendance WHERE user_id = ?", (target_user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (target_user_id,))
        conn.commit()
    return jsonify({'message': f'User {target_user_id} and their records deleted'}), 200

@app.route('/api/admin/attendance/<int:log_id>', methods=['DELETE'])
@jwt_required()
def api_admin_delete_log(log_id):
    user_id = get_jwt_identity()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Admin access required'}), 403

        c.execute("DELETE FROM attendance WHERE id = ?", (log_id,))
        conn.commit()
    return jsonify({'message': f'Attendance log {log_id} deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
