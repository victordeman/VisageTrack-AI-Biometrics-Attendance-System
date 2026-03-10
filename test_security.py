import os
from flask import Flask, send_from_directory

# Mocking the setup in app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = BASE_DIR
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def static_files_logic(path):
    ALLOWED_EXTENSIONS = {'.html', '.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.json'}
    ALLOWED_FOLDERS = {'components', 'uploads'}
    
    ext = os.path.splitext(path)[1].lower()
    
    if path == '' or path == '/':
        return "index.html"

    is_in_allowed_folder = any(path.startswith(f + '/') for f in ALLOWED_FOLDERS)
    is_allowed_top_level = '/' not in path and ext in ALLOWED_EXTENSIONS
    
    if (is_in_allowed_folder or is_allowed_top_level) and ext in ALLOWED_EXTENSIONS:
        if path.startswith('uploads/'):
            filename = path.replace('uploads/', '', 1)
            upload_path = os.path.join(UPLOAD_FOLDER, filename)
            return f"serving from uploads: {filename}"
        
        full_path = os.path.join(BASE_DIR, path)
        return f"serving from base: {path}"
        
    return "index.html (default)"

# Test cases
tests = [
    ("", "index.html"),
    ("index.html", "serving from base: index.html"),
    ("script.js", "serving from base: script.js"),
    ("app.py", "index.html (default)"),
    ("requirements.txt", "index.html (default)"),
    ("components/navbar.js", "serving from base: components/navbar.js"),
    ("uploads/test.jpg", "serving from uploads: test.jpg"),
    (".env", "index.html (default)"),
    ("database.db", "index.html (default)"),
]

for path, expected in tests:
    result = static_files_logic(path)
    print(f"Path: {path:25} Expected: {expected:40} Result: {result}")
    assert result == expected

print("All security tests passed!")
