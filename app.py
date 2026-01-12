from flask import Flask, request, jsonify, send_file
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "pdfs")

os.makedirs(PDF_DIR, exist_ok=True)


@app.route("/")
def home():
    return "API de Captação Online"


@app.route("/healthz")
def healthz():
    return "ok"


@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.get_json(force=True, silent=True)

    if not dados:
        return jsonify({"status": "erro", "mensagem": "JSON vazio"}), 400

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"captacao_{timestamp}.pdf"
    caminho_pdf = os.path.join(PDF_DIR, nome_arquivo)

    gerar_pdf(caminho_pdf, dados)

    return jsonify({
        "status": "sucesso",
        "download": f"/download/{nome_arquivo}"
    })


@app.route("/download/<nome_arquivo>")
def download_pdf(nome_arquivo):
    caminho = os.path.join(PDF_DIR, nome_arquivo)

    if not os.path.exists(caminho):
        return "Arquivo não encontrado", 404

    return send_file(caminho, as_attachment=True)


def gerar_pdf(caminho, dados):
    c = canvas.Canvas(caminho, pagesize=A4)
    largura, altura = A4

    y = altura - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "FICHA DE CAPTAÇÃO DE IMÓVEL")
    y -= 40

    c.setFont("Helvetica", 11)

    for campo, valor in dados.items():
        c.drawString(50, y, f"{campo}: {valor}")
        y -= 20

        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = altura - 50

    c.save()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
