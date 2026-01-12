from flask import Flask, request, jsonify
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import os
import os
TOKEN = os.getenv("API_TOKEN")

app = Flask(__name__)
os.makedirs("pdfs", exist_ok=True)

@app.route("/captacao", methods=["POST"])
def receber_captacao():
    dados = request.json

    codigo = dados.get("Código do imóvel", "SEM_CODIGO")
    nome_pdf = f"pdfs/CAPTACAO_{codigo}.pdf"

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(nome_pdf, pagesize=A4)
    elementos = []

    elementos.append(Paragraph("<b>FICHA DE CAPTAÇÃO DE IMÓVEL</b>", styles["Title"]))
    elementos.append(Paragraph(f"Proprietário: {dados.get('Nome / Empresa','')}", styles["Normal"]))
    elementos.append(Paragraph(f"Telefone: {dados.get('Telefone celular / WhatsApp','')}", styles["Normal"]))
    elementos.append(Paragraph(f"Tipo do imóvel: {dados.get('Tipo do imóvel','')}", styles["Normal"]))
    elementos.append(Paragraph(f"Valor: {dados.get('Valor de venda (R$)','')}", styles["Normal"]))

    doc.build(elementos)

    return jsonify({"status": "PDF gerado", "arquivo": nome_pdf})

if __name__ == "__main__":
    app.run(port=5000)
