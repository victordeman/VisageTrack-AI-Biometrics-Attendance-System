from flask import Flask, request, jsonify, send_from_directory
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import sqlite3
import numpy as np
import face_recognition
import cv2
from cryptography.fernet import Fernet
import base64
import os

app = Flask(__name__, static_folder='.', static_url_path='')
api = Api(app)
app.config['JWT_SECRET_KEY'] = 'super-secret-key'  # Change in production
jwt = JWTManager(app)

# Generate encryption key (store securely in production)
key = Fernet.generate_key()
cipher = Fernet(key)

# Database setup
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, embedding BLOB)''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, user_id INTEGER, timestamp TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Helper to encode/decode embeddings
def encode_embedding(embedding):
    return cipher.encrypt(embedding.tobytes())

def decode_embedding(encrypted):
    return np.frombuffer(cipher.decrypt(encrypted), dtype=np.float64)

# Liveness detection (basic: check for motion between frames)
def is_live(frames):
    if len(frames) < 2:
        return False
    gray1 = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frames[1], cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(gray1, gray2)
    return np.mean(diff) > 5  # Threshold for motion

class Enroll(Resource):
    def post(self):
        data = request.form
        name = data['name']
        email = data['email']
        images = [request.files[f'image{i}'] for i in range(1, 11) if f'image{i}' in request.files]  # Up to 10 images
        frames = [cv2.imdecode(np.frombuffer(img.read(), np.uint8), cv2.IMREAD_COLOR) for img in images]
        
        if not is_live(frames[:2]):  # Check first two for liveness
            return {'message': 'Liveness check failed'}, 400
        
        embeddings = []
        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb)
            if face_locations:
                embeddings.append(face_recognition.face_encodings(rgb, face_locations)[0])
        
        if not embeddings:
            return {'message': 'No face detected'}, 400
        
        avg_embedding = np.mean(embeddings, axis=0)
        encrypted = encode_embedding(avg_embedding)
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (name, email, embedding) VALUES (?, ?, ?)", (name, email, encrypted))
        conn.commit()
        conn.close()
        
        return {'message': 'Enrollment successful'}, 200

class Recognize(Resource):
    def post(self):
        image = request.files['image']
        frame = cv2.imdecode(np.frombuffer(image.read(), np.uint8), cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        if not face_locations:
            return {'message': 'No face detected'}, 400
        
        new_embedding = face_recognition.face_encodings(rgb, face_locations)[0]
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id, embedding FROM users")
        users = c.fetchall()
        conn.close()
        
        for user_id, encrypted in users:
            stored_embedding = decode_embedding(encrypted)
            distance = face_recognition.face_distance([stored_embedding], new_embedding)[0]
            if distance < 0.6:  # Threshold
                # Log attendance
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, datetime('now'), 'present')", (user_id,))
                conn.commit()
                conn.close()
                return {'message': 'Attendance recorded with your face', 'user_id': user_id}, 200
        
        return {'message': 'Face not recognized'}, 401

class Login(Resource):
    def post(self):
        # Simple demo login
        data = request.json
        # Validate credentials (add real auth)
        access_token = create_access_token(identity=data['email'])
        return {'access_token': access_token}

api.add_resource(Enroll, '/api/enroll')
api.add_resource(Recognize, '/api/recognize')
api.add_resource(Login, '/api/login')

# Serve frontend
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
