from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# Rota principal (teste)
@app.route("/")
def home():
    return "API de Captação Online"

# Health check (Render)
@app.route("/healthz")
def healthz():
    return "ok"

# Rota que recebe os dados do Google Forms
@app.route("/captacao", methods=["POST"])
def captacao():
    # Força leitura do JSON (Google Apps Script)
    dados = request.get_json(force=True, silent=True)

    print("===================================")
    print("DADOS RECEBIDOS EM:", datetime.now())
    print(dados)
    print("RAW DATA:", request.data)
    print("===================================")

    if not dados:
        return jsonify({
            "status": "erro",
            "mensagem": "JSON vazio ou inválido"
        }), 400

    return jsonify({
        "status": "sucesso",
        "mensagem": "Captação recebida com sucesso",
        "dados": dados
    }), 200


if __name__ == "__main__":
    # Porta obrigatória do Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
