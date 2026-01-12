from flask import Flask, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import io
import os

app = Flask(__name__)


@app.route("/")
def home():
    return "API de Captação Online"


@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.get_json(force=True, silent=True)

    if not dados:
        return {"erro": "JSON vazio"}, 400

    buffer = io.BytesIO()

    gerar_pdf(buffer, dados)

    buffer.seek(0)

    nome_arquivo = f"captacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/pdf"
    )


def gerar_pdf(buffer, dados):
    c = canvas.Canvas(buffer, pagesize=A4)
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
