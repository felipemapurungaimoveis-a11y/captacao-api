from flask import Flask, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import io
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "API de Captação Online OK"

@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.get_json()

    if not dados:
        return {"erro": "Nenhum dado recebido"}, 400

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

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "logo.png")

    azul = HexColor("#0A3D62")
    cinza = HexColor("#444444")
    preto = HexColor("#000000")

    margem_x = 40
    largura_util = largura - (margem_x * 2)

    def cabecalho():
        nonlocal y
        y = altura - 50

        if os.path.exists(logo_path):
            c.drawImage(logo_path, margem_x, y - 40, width=120, height=40, mask="auto")

        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2, y, "FICHA DE CAPTAÇÃO DE IMÓVEL")

        c.setLineWidth(1)
        c.line(margem_x, y - 15, largura - margem_x, y - 15)

        c.setFont("Helvetica", 9)
        c.setFillColor(cinza)
        c.drawRightString(
            largura - margem_x,
            y - 30,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        )

        y -= 80

    cabecalho()

    secoes = {
        "DADOS DO PROPRIETÁRIO": [
            "Nome do Proprietário",
            "CPF/CNPJ",
            "Data de Nascimento",
            "Nome do Cônjuge",
            "E-mail do Proprietário",
            "Telefone do Proprietário",
        ],
        "DADOS DO IMÓVEL DO PROPRIETÁRIO": [
            "Endereço do Proprietário",
            "Nº da casa do Proprietário",
            "Bairro da casa do Proprietário",
            "Cidade da casa do proprietário",
            "Estado da casa do proprietário",
            "CEP da cada do Proprietário",
            "Complemento",
        ],
        "DADOS DO IMÓVEL CAPTADO": [
            "Endereço do Imóvel (CAPTADO)",
            "Nº do Imóvel (CAPTADO)",
            "Bairro do Imóvel (CAPTADO)",
            "Cidade do Imóvel (CAPTADO)",
            "CEP do Imóvel (CAPTADO)",
            "Estado do Imóvel (CAPTADO)",
            "Complemento do Imóvel (CAPTADO)",
        ],
        "CARACTERÍSTICAS GERAIS": [
            "Situação do Imóvel",
            "Tipo do Imóvel",
            "Nome da Construtora",
            "Idade do Imóvel",
            "Posição do Imóvel",
            "Topografia",
            "Prazo de Entrega",
        ],
        "VALORES": [
            "Preço do Imóvel (CAPTADO)",
            "Preço do Condomínio",
            "Preço do IPTU",
            "Aceita Permuta?",
        ],
        "DISTRIBUIÇÃO DO IMÓVEL": [
            "Quantidade de Quarto?",
            "Quantidade de Suíte?",
            "Quantidade de Sala?",
            "Quantidade de Banheiro?",
            "Tem Varanda?",
            "Tem Garagem?",
            "Cabe quantos carros?",
            "A garagem é coberta?",
        ],
        "DESCRIÇÃO COMPLEMENTAR": [
            "Faça uma descrição detalhada do Imóvel",
            "Vistoria",
        ],
    }

    def nova_pagina():
        c.showPage()
        cabecalho()

    for titulo, campos in secoes.items():
        altura_secao = 18 + (len(campos) * 26)

        if y - altura_secao < 80:
            nova_pagina()

        c.setStrokeColor(azul)
        c.rect(margem_x, y - altura_secao, largura_util, altura_secao)

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(azul)
        c.drawString(margem_x + 10, y - 15, titulo)

        y_cursor = y - 35

        for campo in campos:
            valor = str(dados.get(campo, "—"))

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(preto)
            c.drawString(margem_x + 10, y_cursor, campo)

            linhas = simpleSplit(valor, "Helvetica", 10, largura_util - 170)

            c.setFont("Helvetica", 10)
            x_valor = margem_x + 160
            for linha in linhas:
                c.drawString(x_valor, y_cursor, linha)
                y_cursor -= 12

            y_cursor -= 6

        y -= altura_secao + 15

    c.save()
