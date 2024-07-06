from flask import Flask, request, jsonify, send_file
from datetime import datetime
from flask_cors import CORS
import base64
import io
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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

# Função para enviar email
def enviar_email(responsible, vm_name, code_name, location, log_content, filename):
    try:
        sender_email = "smtp@treeinova.com.br"
        sender_password = "M3c%mec#46"
        recipient_email = responsible

        # Configurar a mensagem
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Alerta de Erro - {vm_name}"

        body = (f"Olá,\n\n"
                f"Foi detectado um erro na seguinte máquina virtual: {location}\n\n"
                f"Empresa: {vm_name}\n"
                f"Código: {code_name}\n"
                f"Em anexo, segue o log do erro.\n\n"
                f"Atenciosamente,\n"
                f"HeartBeat - Sistema de Monitoramento")

        msg.attach(MIMEText(body, 'plain'))

        # Anexar o arquivo de log
        if log_content:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(log_content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)

        # Enviar o email
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
        
        logging.info(f"Email enviado para {responsible} sobre erro na VM {vm_name}")

    except Exception as e:
        logging.error(f"Falha ao enviar email: {e}")

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
    responsible = request.form.get('responsible')
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
        "responsible": responsible,
        "file": filename,
        "log": log_content
    }

    logging.info(f"Heartbeat registrado: {heartbeats[code_name]}")

    # Enviar email se o estado for "❌ Erro"
    if state == "❌ Erro":
        enviar_email(responsible, vm_name, code_name, location, base64.b64decode(log_content.encode('utf-8')), filename)

    return jsonify({"status": "success", "timestamp": timestamp}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify(heartbeats), 200

@app.route('/download/<vm_name>', methods=['GET'])
def download(vm_name):
    for code_name, info in heartbeats.items():
        if info["vm_name"] == vm_name:
            if info["file"]:
                log_content = base64.b64decode(info["log"].encode('utf-8'))
                return send_file(io.BytesIO(log_content), as_attachment=True, download_name=info["file"], mimetype='application/octet-stream')
    return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado"}), 404

@app.route('/view_file/<vm_name>', methods=['GET'])
def view_file(vm_name):
    for code_name, info in heartbeats.items():
        if info["vm_name"] == vm_name:
            if info["file"]:
                log_content = base64.b64decode(info["log"].encode('utf-8')).decode('utf-8')
                return jsonify({"Conteudo": log_content})
    return jsonify({"status": "erro", "mensagem": "Arquivo não encontrado"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
