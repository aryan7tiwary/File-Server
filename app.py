from flask import Flask, request, redirect, url_for, send_from_directory, render_template, session, abort, send_file
from flask_session import Session
import os
import zipfile
import io

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

UPLOAD_FOLDER = 'uploads'
PASSWORD = 'aryan@304'  # Replace with a strong password

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
@app.route('/<path:subpath>')
def index(subpath=''):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    try:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], subpath)
        if not os.path.exists(full_path):
            abort(404)
        # Get the list of files and directories in the current path
        dirs = []
        files = []
        for item in os.listdir(full_path):
            if os.path.isdir(os.path.join(full_path, item)):
                dirs.append(item)
            else:
                files.append(item)
        return render_template('index.html', dirs=dirs, files=files, subpath=subpath)
    except Exception as e:
        print(f"Error accessing path '{subpath}': {e}")
        abort(500)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return redirect(url_for('index'))
    return render_template('upload.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error sending file '{filename}': {e}")
        abort(500)

@app.route('/download_folder/<path:subpath>')
def download_folder(subpath):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    try:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], subpath)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            abort(404)
        # Create a zip file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, app.config['UPLOAD_FOLDER'])
                    zipf.write(file_path, arcname)
        memory_file.seek(0)
        return send_file(memory_file, download_name=f'{os.path.basename(full_path)}.zip', as_attachment=True)
    except Exception as e:
        print(f"Error creating zip file for '{subpath}': {e}")
        abort(500)

if __name__ == '__main__':
    app.run(debug=True)
