from flask import Flask, request, jsonify, session, send_from_directory
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS
import sqlite3
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

# Lazy loading of heavy/problematic modules
_face_recognition = None
_cv2 = None
_numpy = None
_fernet = None
_cipher = None

def get_face_recognition():
    global _face_recognition
    if _face_recognition is None:
        try:
            import face_recognition
            _face_recognition = face_recognition
        except Exception as e:
            logger.error(f"Error importing face_recognition: {e}")
    return _face_recognition

def get_cv2():
    global _cv2
    if _cv2 is None:
        try:
            import cv2
            _cv2 = cv2
        except Exception as e:
            logger.error(f"Error importing cv2: {e}")
    return _cv2

def get_numpy():
    global _numpy
    if _numpy is None:
        import numpy
        _numpy = numpy
    return _numpy

def get_cipher():
    global _cipher, _fernet
    if _cipher is None:
        from cryptography.fernet import Fernet
        _fernet = Fernet

        env_key = os.environ.get('ENCRYPTION_KEY')
        DATA_DIR = get_data_dir()
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
            if not is_vercel():
                try:
                    with open(KEY_FILE, 'wb') as f:
                        f.write(key)
                except:
                    pass
            logger.info("Generated new encryption key.")

        _cipher = Fernet(key)
    return _cipher

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configuration
app.config['SECRET_KEY'] = 'visage-track-2026-super-secure-key-32bytes'
app.config['JWT_SECRET_KEY'] = 'visage-track-2026-super-secure-key-32bytes'
app.config['JWT_TOKEN_LOCATION'] = ['headers']

jwt = JWTManager(app)

# Environment-specific configuration
def is_vercel():
    return os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

def get_data_dir():
    if is_vercel():
        return '/tmp'
    # Use the absolute path to the project root for local development
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_upload_folder():
    return os.path.join(get_data_dir(), 'uploads')

def get_db_path():
    return os.path.join(get_data_dir(), 'database.db')

@contextmanager
def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    db_path = get_db_path()
    data_dir = get_data_dir()
    upload_folder = get_upload_folder()

    logger.info(f"Initializing database at {db_path}")
    try:
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
            logger.info(f"Created data directory: {data_dir}")

        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            logger.info(f"Created uploads directory: {upload_folder}")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")

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
            c.execute("SELECT * FROM users WHERE email = ?", ('victor@ex.com',))
            if not c.fetchone():
                c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                        ('Victor', 'victor@ex.com', generate_password_hash('victor@2026'), 'admin'))

            # Add default stuntmen
            c.execute("SELECT * FROM users WHERE email = ?", ('mark@ex.com',))
            if not c.fetchone():
                c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                        ('Mark', 'mark@ex.com', generate_password_hash('mark@2026'), 'employee'))

            conn.commit()
            logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

_db_initialized = False

def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True

# Helpers
def encode_embedding(embedding):
    return get_cipher().encrypt(embedding.tobytes())

def decode_embedding(encrypted):
    np = get_numpy()
    return np.frombuffer(get_cipher().decrypt(encrypted), dtype=np.float64)

# JWT Error Handlers
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({'message': 'Missing Authorization Header'}), 401

@jwt.invalid_token_loader
def invalid_token_response(callback):
    return jsonify({'message': 'Invalid Token', 'details': str(callback)}), 422

@app.before_request
def setup_app():
    ensure_db_initialized()
    if request.path.startswith('/api/'):
        logger.info(f"API Request: {request.method} {request.path}")

@app.errorhandler(Exception)
def handle_error(e):
    if isinstance(e, HTTPException):
        return e
    
    logger.error(f"Error: {str(e)}", exc_info=True)
    return jsonify({'message': 'An internal error occurred', 'error': str(e)}), 500

# ====================== API ROUTES ======================

@app.route('/')
def api_root():
    return jsonify({
        'message': 'VisageTrack AI API',
        'status': 'online',
        'version': '1.0.0'
    }), 200

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api/ping', methods=['GET'])
def api_ping():
    return jsonify({'message': 'pong'}), 200

@app.route('/api/diag', methods=['GET'])
def api_diag():
    import platform
    import sys

    # Don't trigger heavy imports unless explicitly requested via query param
    check_heavy = request.args.get('heavy') == '1'

    diag_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'os_name': os.name,
        'is_vercel': is_vercel(),
        'data_dir': get_data_dir(),
        'modules_available': {
            'face_recognition': (_face_recognition is not None) if not check_heavy else (get_face_recognition() is not None),
            'cv2': (_cv2 is not None) if not check_heavy else (get_cv2() is not None)
        }
    }

    try:
        with open('/proc/meminfo', 'r') as f:
            diag_info['meminfo'] = [next(f) for _ in range(5)]
    except:
        pass

    return jsonify(diag_info), 200

@app.route('/api/health', methods=['GET'])
def api_health():
    # Keep it simple and don't trigger heavy imports
    return jsonify({
        'status': 'healthy',
        'modules_loaded': {
            'face_recognition': _face_recognition is not None,
            'cv2': _cv2 is not None,
            'sqlite3': True
        },
        'environment': {
            'is_vercel': is_vercel(),
            'data_dir': get_data_dir()
        }
    }), 200

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(get_upload_folder(), filename)

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
    filepath = os.path.join(get_upload_folder(), filename)
    image_file.save(filepath)

    fr = get_face_recognition()
    cv = get_cv2()
    if fr is None or cv is None:
        return jsonify({'message': 'Biometric modules not available on this server'}), 503

    try:
        frame = cv.imread(filepath)
        rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
        locations = fr.face_locations(rgb)
        if not locations:
            return jsonify({'message': 'No face detected in the image'}), 400
        
        embedding = fr.face_encodings(rgb, locations)[0]
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
    fr = get_face_recognition()
    cv = get_cv2()
    np = get_numpy()
    if fr is None or cv is None:
        return jsonify({'message': 'Biometric modules not available on this server'}), 503

    if 'image' not in request.files:
        return jsonify({'message': 'No image file'}), 400

    image_file = request.files['image']
    file_bytes = image_file.read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    frame = cv.imdecode(nparr, cv.IMREAD_COLOR)
    
    if frame is None:
        return jsonify({'message': 'Invalid image'}), 400

    rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    locations = fr.face_locations(rgb)
    if not locations:
        return jsonify({'message': 'No face detected'}), 400

    new_embedding = fr.face_encodings(rgb, locations)[0]

    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, embedding FROM users WHERE embedding IS NOT NULL")
        users = c.fetchall()

        for user in users:
            try:
                stored = decode_embedding(user['embedding'])
                distance = fr.face_distance([stored], new_embedding)[0]
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
