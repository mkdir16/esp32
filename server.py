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

# Идеальный HTML-интерфейс с автообновлением и правильным отображением картинки
ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ESP32-CAM Мониторинг</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b111e; margin: 0; padding: 15px; color: #eee; }
        .container { max-width: 1000px; margin: 0 auto; }
        h1 { text-align: center; font-weight: 600; letter-spacing: 1px; color: #fff; margin: 10px 0 5px 0; font-size: 1.8rem; }
        .subtitle { text-align: center; color: #707e94; margin-bottom: 20px; font-size: 0.95rem; }
        .photo-card { background: #151f32; border-radius: 16px; padding: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); border: 1px solid #22314d; margin-bottom: 20px; }
        
        /* ИСПРАВЛЕНО: Картинка теперь крупная, широкая и адаптируется под любой экран */
        .photo-card img { 
            width: 100%; 
            height: auto; 
            max-height: 75vh; 
            object-fit: contain; 
            border-radius: 10px; 
            border: 1px solid #2d3f61; 
            display: block;
            margin: 0 auto;
        }
        
        .timestamp { color: #5c6b84; font-size: 0.85em; margin: 12px 0; text-align: center; font-family: monospace; }
        .response { text-align: center; font-size: 1.15rem; margin: 15px 0; padding: 12px; background: #0d1624; border-radius: 8px; color: #4caf50; border: 1px solid #1b2d4a; font-weight: bold; }
        .button-panel { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 15px; }
        .cmd-btn { font-size: 1rem; font-weight: bold; padding: 12px 18px; border: none; border-radius: 30px; cursor: pointer; transition: all 0.2s; color: white; min-width: 140px; flex: 1 1 140px; max-width: 200px; }
        .cmd-btn:hover { opacity: 0.9; transform: translateY(-2px); }
        .cmd-btn:active { transform: translateY(0); }
        .btn-A { background: #2e7d32; box-shadow: 0 4px 12px rgba(46,125,50,0.3); }
        .btn-B { background: #ef6c00; box-shadow: 0 4px 12px rgba(239,108,0,0.3); }
        .btn-C { background: #c62828; box-shadow: 0 4px 12px rgba(198,40,40,0.3); }
        .btn-D { background: #6a1b9a; box-shadow: 0 4px 12px rgba(106,27,154,0.3); }
        .off-btn { background: #455a64; }
        .delete-btn { background: #b71c1c; width: 100%; border-radius: 10px; margin-top: 15px; font-size: 1rem; font-weight: bold; padding: 12px; border: none; color: white; cursor: pointer; }
        .delete-btn:hover { background: #8b0000; }
        .clear-btn { background: #37474f; padding: 10px 15px; border: none; border-radius: 8px; cursor: pointer; color: white; font-weight: bold; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #1e2d4a; padding-bottom: 15px; }
        .no-photos { text-align: center; padding: 60px; background: #151f32; border-radius: 16px; border: 1px dashed #2d3f61; color: #707e94; font-size: 1.1rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>📸 Мониторинг Системы</h1>
                <div style="color: #4caf50; font-size: 0.85rem; font-weight: bold;">● СЕРВЕР СВЯЗИ АКТИВЕН</div>
            </div>
            <button class="clear-btn" onclick="clearHistory()">🗑 Очистить историю</button>
        </div>
        
        <div class="subtitle">Управление светодиодом на основе последнего широкого кадра</div>
        
        <div id="main-content">
            <p style="text-align: center; color: #707e94;">Синхронизация данных...</p>
        </div>
    </div>
    
    <script>
        let currentPhotoId = "";

        async function updateDashboard() {
            try {
                const res = await fetch('/admin?json=1');
                if (!res.ok) return;
                const data = await res.json();
                
                if (data.photos.length === 0) {
                    document.getElementById('main-content').innerHTML = `
                        <div class="no-photos">
                            ⏳ Нет активных снимков.<br><br>
                            <span style="font-size: 0.9rem; color: #4a5a73;">Нажмите физическую кнопку на ESP32-CAM для получения кадра.</span>
                        </div>`;
                    currentPhotoId = "";
                    return;
                }
                
                const latestPhoto = data.photos[0];
                
                if (latestPhoto.id !== currentPhotoId) {
                    currentPhotoId = latestPhoto.id;
                    renderCard(latestPhoto, data.responses[latestPhoto.id] || "OFF");
                } else {
                    const activeMode = data.responses[latestPhoto.id] || "OFF";
                    const respDiv = document.getElementById('response-text');
                    if (respDiv) {
                        if (activeMode === "OFF") respDiv.innerHTML = "⏳ Статус: Светодиод ВЫКЛЮЧЕН";
                        else if (activeMode === "A") respDiv.innerHTML = "✅ Активен режим: Вариант А (Статичный)";
                        else if (activeMode === "B") respDiv.innerHTML = "✅ Активен режим: Вариант Б (Медленный)";
                        else if (activeMode === "C") respDiv.innerHTML = "✅ Активен режим: Вариант В (Быстрый)";
                        else if (activeMode === "D") respDiv.innerHTML = "✅ Активен режим: Вариант Г (Сложный)";
                    }
                }
            } catch (e) {
                console.log("Ошибка обновления");
            }
        }

        function renderCard(photo, activeMode) {
            let modeText = "⏳ Статус: Светодиод ВЫКЛЮЧЕН";
            if (activeMode === "A") modeText = "✅ Активен режим: Вариант А (Статичный)";
            else if (activeMode === "B") modeText = "✅ Активен режим: Вариант Б (Медленный)";
            else if (activeMode === "C") modeText = "✅ Активен режим: Вариант В (Быстрый)";
            else if (activeMode === "D") modeText = "✅ Активен режим: Вариант Г (Сложный)";

            document.getElementById('main-content').innerHTML = `
                <div class="photo-card">
                    <img src="/uploads/${photo.filename}?t=${new Date().getTime()}">
                    <div class="timestamp">📅 Снимок получен: ${photo.timestamp} | Камера: ${photo.cam_id}</div>
                    <div class="response" id="response-text">${modeText}</div>
                    
                    <div class="button-panel">
                        <button class="cmd-btn btn-A" onclick="sendCommand('${photo.id}', 'A')">🟢 А (Статичный)</button>
                        <button class="cmd-btn btn-B" onclick="sendCommand('${photo.id}', 'B')">🟠 Б (Медленный)</button>
                        <button class="cmd-btn btn-C" onclick="sendCommand('${photo.id}', 'C')">🔴 В (Быстрый)</button>
                        <button class="cmd-btn btn-D" onclick="sendCommand('${photo.id}', 'D')">🟣 Г (Сложный)</button>
                        <button class="cmd-btn off-btn" onclick="sendCommand('${photo.id}', 'OFF')">⚫ OFF</button>
                    </div>
                    
                    <button class="delete-btn" onclick="deletePhoto('${photo.id}')">🗑 Удалить этот снимок</button>
                </div>
            `;
        }

        async function sendCommand(photoId, command) {
            document.getElementById('response-text').innerHTML = '📤 Отправка команды...';
            await fetch('/send_response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ photo_id: photoId, response: command })
            });
            updateDashboard();
        }
        
        async function deletePhoto(photoId) {
            if(confirm('Удалить снимок? Светодиод вернется в режим OFF.')) {
                await fetch('/delete_photo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ photo_id: photoId })
                });
                updateDashboard();
            }
        }
        
        async function clearHistory() {
            if(confirm('Очистить всю историю устройств?')) {
                await fetch('/clear_history', { method: 'POST' });
                updateDashboard();
            }
        }

        setInterval(updateDashboard, 3000);
        updateDashboard();
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
    
    if len(history['photos']) > 30:
        old_photos = history['photos'][30:]
        for old in old_photos:
            old_path = os.path.join(UPLOAD_FOLDER, old['filename'])
            if os.path.exists(old_path):
                os.remove(old_path)
        history['photos'] = history['photos'][:30]
    
    save_history(history)
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
    if request.args.get('json'):
        return jsonify({
            'photos': history['photos'],
            'responses': history['responses']
        })
    return render_template_string(ADMIN_HTML)

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
        "admin": "/admin"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
