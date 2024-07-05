from flask import Flask, request, jsonify, send_file
from datetime import datetime
from flask_cors import CORS
import base64
import io
import logging

# Configuração do logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Permitir todas as origens

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
    logging.info("Recebendo solicitação de heartbeat")

    # Verificar a senha
    senha = request.form.get('senha')
    if senha != SENHA_ESPERADA:
        logging.warning(f"Senha inválida: {senha}")
        return jsonify({"status": "erro", "mensagem": "Credenciais inválidas"}), 401

    # Verificar status válido
    state = request.form.get('state', 'Unknown')
    if state not in STATUS_VALIDOS:
        logging.warning(f"Status inválido: {state}")
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
        "vm_name": vm_name,
        "location": location,
        "timestamp": timestamp,
        "state": state,
        "file": filename,
        "log": log_content
    }

    logging.info(f"Heartbeat registrado: {heartbeats[code_name]}")
    return jsonify({"status": "success", "timestamp": timestamp}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify(heartbeats), 200

@app.route('/download/<vm_name>', methods=['GET'])
def download(vm_name):
    if vm_name in heartbeats:
        info = heartbeats[vm_name]
        if info["file"]:
            log_content = base64.b64decode(info["log"].encode('utf-8'))
            return send_file(io.BytesIO(log_content), as_attachment=True, download_name=info["file"], mimetype='application/octet-stream')
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
