from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "API de Captação Online", 200

@app.route("/healthz")
def health():
    return "ok", 200

@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.json
    print("Dados recebidos:", dados)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

