from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
from flask_cors import CORS
import base64

app = Flask(__name__)
CORS(app)  # Permite CORS de qualquer origem

# Dicionário para armazenar o último heartbeat e estado de cada VM
heartbeats = {}

# Senha esperada
SENHA_ESPERADA = "sua_senha_secreta"

# Status válidos
STATUS_VALIDOS = [
    "🚀 Iniciando",
    "⚙️ Executando",
    "📨 Enviando e-mails",
    "✅ Finalizando",
    "⚠️ Alerta",
    "❌ Erro",
    "⌛ Aguardando Inicio"
]

@app.route('/')
def index():
    return "Servidor Flask está rodando!"

@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    print("Recebendo solicitação de heartbeat")
    
    # Verificar a senha
    senha = request.form.get('senha')
    if senha != SENHA_ESPERADA:
        print("Senha inválida:", senha)
        return jsonify({"status": "erro", "mensagem": "Credenciais inválidas"}), 401

    # Verificar status válido
    state = request.form.get('state', 'Unknown')
    if state not in STATUS_VALIDOS:
        print("Status inválido:", state)
        return jsonify({"status": "erro", "mensagem": "Status inválido"}), 400

    vm_name = request.form.get('vm_name')
    code_name = request.form.get('code_name')
    location = request.form.get('location')
    timestamp = datetime.now()

    # Processar arquivo
    arquivo = request.files.get('arquivo')
    filename = None
    log_content = ""
    if arquivo:
        filename = f"{vm_name}_{arquivo.filename}"
        log_content = base64.b64encode(arquivo.read()).decode('utf-8')

    heartbeats[code_name] = {
        "code_name": vm_name,
        "location": location,
        "timestamp": timestamp,
        "state": state,
        "file": filename,
        "log": log_content
    }

    print("Heartbeat registrado:", heartbeats[code_name])
    return jsonify({"status": "success", "timestamp": timestamp}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify(heartbeats), 200

@app.route('/view', methods=['GET'])
def view():
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Status das VMs</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Status das VMs</h1>
        <table>
            <tr>
                <th>VM</th>
                <th>Código</th>
                <th>Local</th>
                <th>Timestamp</th>
                <th>Status</th>
                <th>Arquivo</th>
                <th>Log</th>
            </tr>
            {% for vm_name, info in heartbeats.items() %}
            <tr>
                <td>{{ vm_name }}</td>
                <td>{{ info.code_name }}</td>
                <td>{{ info.location }}</td>
                <td>{{ info.timestamp }}</td>
                <td>{{ info.state }}</td>
                <td>
                    {% if info.file %}
                        <a href="/download/{{ vm_name }}">Download</a>
                    {% else %}
                        No File
                    {% endif %}
                </td>
                <td>{{ info.log }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(template, heartbeats=heartbeats)

@app.route('/download/<vm_name>', methods=['GET'])
def download(vm_name):
    if vm_name in heartbeats:
        info = heartbeats[vm_name]
        if info["file"]:
            log_content = base64.b64decode(info["log"].encode('utf-8'))
            return log_content, 200, {
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename={info["file"]}'
            }
    return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado"}), 404

@app.route('/view_file/<vm_name>', methods=['GET'])
def view_file(vm_name):
    if vm_name in heartbeats:
        info = heartbeats[vm_name]
        if info["file"]:
            log_content = base64.b64decode(info["log"].encode('utf-8')).decode('utf-8')
            return jsonify({"Conteudo": log_content})
    return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
