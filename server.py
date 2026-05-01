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
        body { font-family: Arial; padding: 20px; background: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        .photo-card { 
            display: inline-block; 
            width: 300px; 
            margin: 10px; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 8px;
            background: #f9f9f9;
            vertical-align: top;
        }
        img { width: 100%; border-radius: 5px; }
        .timestamp { color: #666; font-size: 0.8em; margin: 5px 0; }
        .response { color: green; font-weight: bold; margin: 5px 0; }
        input[type=text] { width: calc(100% - 20px); padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        button { padding: 6px 12px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #45a049; }
        .clear-btn { background: #f44336; margin-bottom: 20px; }
        .clear-btn:hover { background: #d32f2f; }
        h1 { text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ESP32-CAM Админка</h1>
            <button class="clear-btn" onclick="clearHistory()">Очистить историю</button>
        </div>
        
        <div id="photos">
            {% for photo in photos %}
            <div class="photo-card" id="card-{{ photo.id }}">
                <img src="/uploads/{{ photo.filename }}">
                <div class="timestamp">{{ photo.timestamp }}</div>
                <div class="response" id="response-{{ photo.id }}">
                    {% if responses.get(photo.id) %}
                    Ответ: {{ responses[photo.id] }}
                    {% else %}
                    Нет ответа
                    {% endif %}
                </div>
                <form onsubmit="sendResponse('{{ photo.id }}', event)">
                    <input type="text" id="response-input-{{ photo.id }}" placeholder="Ответ (ok, wait, error, off, или любой текст)">
                    <button type="submit">Отправить</button>
                </form>
            </div>
            {% endfor %}
        </div>
        
        {% if not photos %}
        <p>Нет фотографий. Ожидание...</p>
        {% endif %}
    </div>
    
    <script>
        function sendResponse(photoId, event) {
            event.preventDefault();
            const response = document.getElementById('response-input-' + photoId).value;
            
            fetch('/send_response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photo_id: photoId, response: response })
            })
            .then(res => res.json())
            .then(() => location.reload());
        }
        
        function clearHistory() {
            if(confirm('Удалить все фото?')) {
                fetch('/clear_history', { method: 'POST' })
                .then(() => location.reload());
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
        print(f"💬 Ответ на {photo_id}: {response}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/get_response', methods=['GET'])
def get_response():
    cam_id = request.args.get('cam', 'unknown')
    
    for photo in history['photos']:
        if photo['cam_id'] == cam_id:
            photo_id = photo['id']
            if photo_id in history['responses']:
                return jsonify({"response": history['responses'][photo_id]})
            break
    
    return jsonify({"response": ""})

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
