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

# Обновленный HTML-интерфейс в соответствии с вашей таблицей режимов
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ESP32-CAM Админка</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0f1e; margin: 0; padding: 20px; color: #eee; }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; }
        .photo-grid { display: flex; flex-direction: column; gap: 30px; }
        .photo-card { background: #1e2a3a; border-radius: 20px; padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
        .photo-card img { 
            width: 100%; 
            max-height: 85vh; 
            object-fit: contain; 
            border-radius: 12px; 
            cursor: pointer;
            border: 1px solid #3a4a5a;
        }
        .timestamp { color: #8aa; font-size: 0.9em; margin: 10px 0; text-align: center; }
        .response { text-align: center; font-size: 1.2em; margin: 15px 0; padding: 10px; background: #0a1520; border-radius: 10px; color: #4caf50; }
        .button-panel { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 15px; }
        .cmd-btn { 
            font-size: 1.3rem; 
            font-weight: bold; 
            padding: 12px 25px; 
            border: none; 
            border-radius: 50px; 
            cursor: pointer; 
            transition: 0.1s; 
            color: white;
        }
        .cmd-btn:active { transform: scale(0.96); }
        .btn-A { background: #2e7d32; }
        .btn-A:hover { background: #1b5e20; }
        .btn-B { background: #ed6c02; }
        .btn-B:hover { background: #e65100; }
        .btn-C { background: #d32f2f; }
        .btn-C:hover { background: #c62828; }
        .btn-D { background: #9c27b0; }
        .btn-D:hover { background: #7b1fa2; }
        .off-btn { background: #555; }
        .off-btn:hover { background: #333; }
        .delete-btn { background: #b71c1c; margin-top: 10px; }
        .delete-btn:hover { background: #8b0000; }
        .clear-btn { background: #555; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 20px; }
        .clear-btn:hover { background: #333; }
        .refresh-btn { background: #2196f3; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; margin-bottom: 20px; margin-left: 10px; }
        .refresh-btn:hover { background: #1976d2; }
        .header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .instructions { 
            background: #0a1520; 
            padding: 15px; 
            border-radius: 10px; 
            margin-bottom: 20px;
            font-size: 0.9em;
            text-align: center;
        }
        .instructions span { display: inline-block; margin: 0 10px; }
        .led-demo { width: 20px; height: 20px; border-radius: 50%; display: inline-block; vertical-align: middle; margin-right: 5px; }
        .led-green { background: #2e7d32; box-shadow: 0 0 5px #2e7d32; }
        .led-yellow { background: #ed6c02; box-shadow: 0 0 5px #ed6c02; }
        .led-red { background: #d32f2f; box-shadow: 0 0 5px #d32f2f; }
        .led-blue { background: #9c27b0; box-shadow: 0 0 5px #9c27b0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📸 ESP32-CAM Админка</h1>
            <div>
                <button class="refresh-btn" onclick="location.reload()">🔄 Обновить</button>
                <button class="clear-btn" onclick="clearHistory()">🗑 Очистить всё</button>
            </div>
        </div>
        
        <!-- Описания изменены под вашу комбинацию режимов -->
        <div class="instructions">
            <span><span class="led-demo led-green"></span> Вариант А (Статичный) — Горит постоянно</span>
            <span><span class="led-demo led-yellow"></span> Вариант Б (Медленный) — 1 сек / 1 сек</span>
            <span><span class="led-demo led-red"></span> Вариант В (Быстрый) — 0.2 сек / 0.2 сек</span>
            <span><span class="led-demo led-blue"></span> Вариант Г (Сложный) — 2 вспышки / пауза</span>
            <span><span class="led-demo"></span> OFF — Выключен</span>
        </div>
        
        <div class="photo-grid">
            {% for photo in photos %}
            <div class="photo-card" id="card-{{ photo.id }}">
                <img src="/uploads/{{ photo.filename }}" onclick="this.requestFullscreen()">
                <div class="timestamp">📅 {{ photo.timestamp }}</div>
                <div class="response" id="response-{{ photo.id }}">
                    {% if responses.get(photo.id) %}
                    💬 Текущий режим: Вариант {{ responses[photo.id] }}
                    {% else %}
                    ⏳ Нет ответа (По умолчанию: OFF)
                    {% endif %}
                </div>
                <div class="button-panel">
                    <button class="cmd-btn btn-A" onclick="sendCommand('{{ photo.id }}', 'A')">🟢 А (Статичный)</button>
                    <button class="cmd-btn btn-B" onclick="sendCommand('{{ photo.id }}', 'B')">🟠 Б (Медленный)</button>
                    <button class="cmd-btn btn-C" onclick="sendCommand('{{ photo.id }}', 'C')">🔴 В (Быстро)</button>
                    <button class="cmd-btn btn-D" onclick="sendCommand('{{ photo.id }}', 'D')">🟣 Г (Сложный)</button>
                    <button class="cmd-btn off-btn" onclick="sendCommand('{{ photo.id }}', 'OFF')">⚫ OFF</button>
                </div>
                <div class="button-panel">
                    <button class="cmd-btn delete-btn" onclick="deletePhoto('{{ photo.id }}')">🗑 Удалить фото</button>
                </div>
            </div>
            {% endfor %}
        </div>
        
        {% if not photos %}
        <p style="text-align: center;">⏳ Нет фотографий. Ожидание загрузки от ESP32-CAM...</p>
        {% endif %}
    </div>
    
    <script>
        async function sendCommand(photoId, command) {
            const responseDiv = document.getElementById('response-' + photoId);
            responseDiv.innerHTML = '📤 Установка режима ' + command + '...';
            
            const res = await fetch('/send_response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photo_id: photoId, response: command })
            });
            
            if (res.ok) {
                responseDiv.innerHTML = '✅ Активен: Вариант ' + command;
            } else {
                responseDiv.innerHTML = '❌ Ошибка изменения режима';
            }
        }
        
        async function deletePhoto(photoId) {
            if(confirm('Удалить это фото?')) {
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
            if(confirm('Удалить всю историю и фотографии?')) {
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
    
    # Сразу определяем текущую активную команду перед сохранением нового кадра
    current_response = "OFF"
    for photo in history['photos']:
        if photo['cam_id'] == cam_id:
            if photo['id'] in history['responses']:
                current_response = history['responses'][photo['id']]
            break

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
    print(f"📸 Фото получено от {cam_id}. На ESP32 отправлен режим: {current_response}")
    
    # В ответе на POST-запрос ESP32 сразу получает букву нужного режима (A, B, V, G или OFF)
    return jsonify({
        "status": "ok", 
        "photo_id": photo_id,
        "response": current_response
    })

@app.route('/send_response', methods=['POST'])
def send_response():
    data = request.json
    photo_id = data.get('photo_id')
    response = data.get('response')
    
    if photo_id and response:
        history['responses'][photo_id] = response
        save_history(history)
        print(f"⚙️ Установлен Вариант {response} для снимка {photo_id}")
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
            print(f"🗑 Запись {photo_id} удалена")
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
    
    return jsonify({"response": "OFF", "cleared": True})

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
        "message": "ESP32-CAM сервер работает в штатном режиме",
        "admin": "/admin"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
