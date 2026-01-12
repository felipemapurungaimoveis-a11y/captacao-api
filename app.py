from flask import Flask, request, jsonify
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdfs")

if not os.path.exists(PDF_DIR):
    os.makedirs(PDF_DIR)


@app.route("/")
def home():
    return "API de Captação Online"


@app.route("/healthz")
def healthz():
    return "ok"


@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.get_json(force=True, silent=True)

    print("===================================")
    print("DADOS RECEBIDOS:", dados)
    print("===================================")

    if not dados:
        return jsonify({"status": "erro", "mensagem": "JSON vazio"}), 400

    # Nome do arquivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"captacao_{timestamp}.pdf"
    caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)

    gerar_pdf(caminho_pdf, dados)

    return jsonify({
        "status": "sucesso",
        "arquivo": nome_arquivo
    }), 200


def gerar_pdf(caminho, dados):
    c = canvas.Canvas(caminho, pagesize=A4)
    largura, altura = A4

    y = altura - 50

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "FICHA DE CAPTAÇÃO DE IMÓVEL")
    y -= 40

    c.setFont("Helvetica", 11)

    for campo, valor in dados.items():
        texto = f"{campo}: {valor}"
        c.drawString(50, y, texto)
        y -= 20

        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = altura - 50

    c.save()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
