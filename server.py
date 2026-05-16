from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
import json
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HISTORY_FILE = 'history.json'

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {'photos': [], 'responses': {}}

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

history = load_history()

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ESP32-CAM Админка</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; margin: 0; padding: 20px; color: #eee; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; }
        .photo-grid { display: flex; flex-direction: column; gap: 30px; }
        .photo-card { background: #1e2a3a; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .photo-card img { width: 100%; max-height: 80vh; object-fit: contain; border-radius: 12px; cursor: pointer; }
        .timestamp { color: #8aa; font-size: 0.9em; margin: 10px 0; text-align: center; }
        .response { text-align: center; font-size: 1.2em; margin: 15px 0; padding: 10px; background: #0a1520; border-radius: 10px; color: #4caf50; }
        .button-panel { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 15px; }
        .cmd-btn { font-size: 1.2rem; font-weight: bold; padding: 12px 25px; border: none; border-radius: 50px; cursor: pointer; transition: 0.1s; color: white; }
        .cmd-btn:active { transform: scale(0.96); }
        .btn-A { background: #2e7d32; }
        .btn-B { background: #ed6c02; }
        .btn-C { background: #d32f2f; }
        .btn-D { background: #9c27b0; }
        .off-btn { background: #555; }
        .delete-btn { background: #b71c1c; margin-top: 10px; }
        .clear-btn { background: #555; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>📸 ESP32-CAM Админка</h1>
            <button class="clear-btn" onclick="clearHistory()">🗑 Очистить всё</button>
        </div>
        
        <div class="photo-grid">
            {% for photo in photos %}
            <div class="photo-card" id="card-{{ photo.id }}">
                <img src="/uploads/{{ photo.filename }}" onclick="this.requestFullscreen()">
                <div class="timestamp">📅 {{ photo.timestamp }}</div>
                <div class="response" id="response-{{ photo.id }}">
                    {% if responses.get(photo.id) %}
                    💬 Ответ: {{ responses[photo.id] }}
                    {% else %}
                    ⏳ Нет ответа
                    {% endif %}
                </div>
                <div class="button-panel">
                    <button class="cmd-btn btn-A" onclick="sendCommand('{{ photo.id }}', 'A')">🟢 А (постоянно)</button>
                    <button class="cmd-btn btn-B" onclick="sendCommand('{{ photo.id }}', 'B')">🟠 Б (1 сек)</button>
                    <button class="cmd-btn btn-C" onclick="sendCommand('{{ photo.id }}', 'C')">🔴 В (0.2 сек)</button>
                    <button class="cmd-btn btn-D" onclick="sendCommand('{{ photo.id }}', 'D')">🟣 Г (2+пауза)</button>
                    <button class="cmd-btn off-btn" onclick="sendCommand('{{ photo.id }}', 'OFF')">⚫ OFF</button>
                </div>
                <div class="button-panel">
                    <button class="cmd-btn delete-btn" onclick="deletePhoto('{{ photo.id }}')">🗑 Удалить фото</button>
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if not photos %}
        <p style="text-align: center;">⏳ Нет фотографий. Нажми кнопку на ESP32-CAM</p>
        {% endif %}
    </div>
    
    <script>
        async function sendCommand(photoId, command) {
            const responseDiv = document.getElementById('response-' + photoId);
            responseDiv.innerHTML = '📤 Отправка команды ' + command + '...';
            
            const res = await fetch('/send_response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photo_id: photoId, response: command })
            });
            
            if (res.ok) {
                responseDiv.innerHTML = '✅ Ответ: ' + command;
            } else {
                responseDiv.innerHTML = '❌ Ошибка отправки';
            }
        }
        
        async function deletePhoto(photoId) {
            if(confirm('Удалить это фото? При удалении светодиод на ESP32 перестанет мигать.')) {
                const res = await fetch('/delete_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ photo_id: photoId })
                });
                if (res.ok) {
                    document.getElementById('card-' + photoId).remove();
                }
            }
        }
        
        async function clearHistory() {
            if(confirm('Удалить все фото?')) {
                await fetch('/clear_history', { method: 'POST' });
                location.reload();
            }
        }
    </script>
</body>
</html>
'''

@app.route('/upload', methods=['POST'])
def upload():
    cam_id = request.headers.get('X-Camera-ID', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{cam_id}_{timestamp}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    with open(filepath, 'wb') as f:
        f.write(request.data)
    
    photo_id = f"{cam_id}_{timestamp}"
    history['photos'].insert(0, {
        'id': photo_id,
        'filename': filename,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'cam_id': cam_id
    })
    
    if len(history['photos']) > 50:
        old_photos = history['photos'][50:]
        for old in old_photos:
            old_path = os.path.join(UPLOAD_FOLDER, old['filename'])
            if os.path.exists(old_path):
                os.remove(old_path)
        history['photos'] = history['photos'][:50]
    
    save_history(history)
    print(f"📸 Фото от {cam_id}: {filename}")
    return jsonify({"status": "ok", "photo_id": photo_id})

@app.route('/send_response', methods=['POST'])
def send_response():
    data = request.json
    photo_id = data.get('photo_id')
    response = data.get('response')
    
    if photo_id and response:
        history['responses'][photo_id] = response
        save_history(history)
        print(f"💬 Команда {response} на {photo_id}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    data = request.json
    photo_id = data.get('photo_id')
    
    for photo in history['photos']:
        if photo['id'] == photo_id:
            filepath = os.path.join(UPLOAD_FOLDER, photo['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
            history['photos'].remove(photo)
            if photo_id in history['responses']:
                del history['responses'][photo_id]
            save_history(history)
            
            # Отправляем сигнал ESP32, что режим нужно сбросить
            print(f"🗑 Фото {photo_id} удалено, сигнал CLEAR")
            return jsonify({"status": "ok"})
    
    return jsonify({"status": "error"}), 404

@app.route('/get_response', methods=['GET'])
def get_response():
    cam_id = request.args.get('cam', 'unknown')
    
    for photo in history['photos']:
        if photo['cam_id'] == cam_id:
            photo_id = photo['id']
            if photo_id in history['responses']:
                return jsonify({
                    "response": history['responses'][photo_id],
                    "last_photo_id": photo_id
                })
            break
    
    return jsonify({"response": "", "cleared": True})

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML, photos=history['photos'], responses=history['responses'])

@app.route('/clear_history', methods=['POST'])
def clear_history():
    global history
    for photo in history['photos']:
        filepath = os.path.join(UPLOAD_FOLDER, photo['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
    history = {'photos': [], 'responses': {}}
    save_history(history)
    return jsonify({"status": "ok"})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/')
def home():
    return jsonify({
        "status": "ok",
        "message": "ESP32-CAM сервер работает",
        "admin": "/admin"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
