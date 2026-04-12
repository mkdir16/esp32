from flask import Flask, request, jsonify, render_template_string, send_from_directory
import os
from datetime import datetime

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

latest_photos = {}
latest_responses = {}

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>ESP32-CAM Админка</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; padding: 20px; background: #f0f0f0; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        img { max-width: 100%; border: 2px solid #333; border-radius: 5px; }
        .camera { margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-radius: 8px; }
        input[type=text] { width: 70%; padding: 10px; margin: 10px 0; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        .response { color: green; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ESP32-CAM Админ-панель</h1>
        {% for cam_id, photo in photos.items() %}
        <div class="camera">
            <h2>Камера: {{ cam_id }}</h2>
            <img src="/uploads/{{ photo }}">
            <form onsubmit="sendResponse('{{ cam_id }}', event)">
                <input type="text" id="response_{{ cam_id }}" placeholder="Введите ответ...">
                <button type="submit">Отправить</button>
            </form>
            <div class="response" id="response_display_{{ cam_id }}">
                {% if responses.get(cam_id) %}
                Ответ: {{ responses[cam_id] }}
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>
    <script>
        function sendResponse(camId, event) {
            event.preventDefault();
            const response = document.getElementById('response_' + camId).value;
            fetch('/send_response', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cam_id: camId, response: response })
            }).then(() => location.reload());
        }
        setInterval(() => location.reload(), 3000);
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
    
    latest_photos[cam_id] = filename
    latest_responses[cam_id] = None
    return jsonify({"status": "ok", "filename": filename})

@app.route('/get_response', methods=['GET'])
def get_response():
    cam_id = request.args.get('cam', 'unknown')
    if cam_id in latest_responses and latest_responses[cam_id]:
        return jsonify({"response": latest_responses[cam_id]})
    return jsonify({"response": ""})

@app.route('/send_response', methods=['POST'])
def send_response():
    data = request.json
    cam_id = data.get('cam_id')
    response = data.get('response')
    if cam_id and response:
        latest_responses[cam_id] = response
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

@app.route('/admin')
def admin():
    return render_template_string(ADMIN_HTML, photos=latest_photos, responses=latest_responses)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)