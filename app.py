from flask import Flask, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import io
import os
import re

app = Flask(__name__)

@app.route("/")
def home():
    return "API PDF OK"

@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.get_json(force=True, silent=True) or {}
    buffer = io.BytesIO()
    gerar_pdf(buffer, dados)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="captacao.pdf",
        mimetype="application/pdf"
    )

# ================= UTILIDADES =================

def formatar_valor(valor):
    try:
        v = float(re.sub(r"[^\d,\.]", "", str(valor)).replace(",", "."))
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

def eh_valor(campo):
    chaves = ["PREÇO", "VALOR", "IPTU", "CONDOMÍNIO", "COMISSÃO", "ENTRADA"]
    return any(c in campo.upper() for c in chaves)

def normalizar_bool(valor):
    if str(valor).strip().upper() in ["SIM", "S", "TRUE", "1"]:
        return True
    if str(valor).strip().upper() in ["NÃO", "NAO", "N", "FALSE", "0"]:
        return False
    return None

# ================= CAPA =================

def desenhar_capa(c, largura, altura, dados, logo_path):
    azul = HexColor("#0A3D62")
    cinza = HexColor("#555555")

    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(0, 0, largura, altura, fill=1)

    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            largura / 2 - 90,
            altura - 180,
            width=180,
            height=65,
            preserveAspectRatio=True,
            mask="auto"
        )

    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(azul)
    c.drawCentredString(largura / 2, altura - 280, "FICHA DE CAPTAÇÃO DE IMÓVEL")

    c.setLineWidth(2)
    c.line(largura / 2 - 180, altura - 305, largura / 2 + 180, altura - 305)

    y = altura - 360
    infos = [
        ("PROPRIETÁRIO", dados.get("NOME DO PROPRIETÁRIO/EMPRESA", "—")),
        ("CORRETOR", dados.get("CORRETOR CAPTADOR", "—")),
        ("CÓDIGO DO IMÓVEL", dados.get("CÓD DO IMÓVEL", "—")),
        ("DATA", datetime.now().strftime("%d/%m/%Y")),
    ]

    for t, v in infos:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cinza)
        c.drawCentredString(largura / 2, y, t)

        c.setFont("Helvetica", 14)
        c.drawCentredString(largura / 2, y - 22, v)
        y -= 70

# ================= PDF =================

def gerar_pdf(buffer, dados):
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "logo.png")

    desenhar_capa(c, largura, altura, dados, logo_path)
    c.showPage()

    margem_x = 40
    largura_util = largura - (margem_x * 2)

    azul = HexColor("#0A3D62")
    cinza = HexColor("#555555")
    preto = HexColor("#000000")
    verde = HexColor("#1B5E20")
    vermelho = HexColor("#B71C1C")

    def cabecalho():
        if os.path.exists(logo_path):
            c.drawImage(logo_path, margem_x, altura - 80, width=120, height=45)
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2 + 30, altura - 55, "FICHA DE CAPTAÇÃO DE IMÓVEL")

    def rodape():
        c.setFont("Helvetica", 8)
        c.setFillColor(cinza)
        c.drawRightString(largura - margem_x, 30, f"Página {c.getPageNumber()}")

    y = altura - 130
    cabecalho()

    LARG_COL = (largura_util - 20) / 2

    def nova_pagina():
        nonlocal y
        rodape()
        c.showPage()
        cabecalho()
        y = altura - 130

    def texto_quebrado(texto, largura_max):
        return simpleSplit(str(texto), "Helvetica", 10, largura_max)

    def desenhar_badge(x, y, texto, cor):
        c.setFillColor(cor)
        c.roundRect(x, y - 14, 50, 16, 6, fill=1)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + 25, y - 11, texto)

    def desenhar_secao(titulo, campos):
        nonlocal y

        altura_real = 30 + len(campos) * 55
        if y - altura_real < 80:
            nova_pagina()

        c.setStrokeColor(azul)
        c.rect(margem_x, y - altura_real, largura_util, altura_real)

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(azul)
        c.drawString(margem_x + 10, y - 20, titulo)

        y_cursor = y - 40
        coluna = 0

        for campo in campos:
            valor = dados.get(campo, "—")
            x = margem_x + (LARG_COL + 20 if coluna else 0)

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(preto)
            c.drawString(x + 10, y_cursor, campo)

            bool_val = normalizar_bool(valor)
            if bool_val is not None:
                desenhar_badge(
                    x + 10,
                    y_cursor - 6,
                    "SIM" if bool_val else "NÃO",
                    verde if bool_val else vermelho
                )
            else:
                if eh_valor(campo):
                    valor = formatar_valor(valor)

                linhas = texto_quebrado(valor, LARG_COL - 20)
                c.setFont("Helvetica", 10)
                y_texto = y_cursor - 14
                for linha in linhas:
                    c.drawString(x + 10, y_texto, linha)
                    y_texto -= 12

            if coluna:
                y_cursor -= 60
                coluna = 0
            else:
                coluna = 1

        y -= altura_real + 20

    # === SEÇÕES ===
    secoes = {
        "CORRETOR": [
            "CORRETOR CAPTADOR",
        ],
        "CÓDIGO DO IMÓVEL": [
            "CÓD DO IMÓVEL",
        ],

        "DADOS DO PROPRIETÁRIO": [
            "NOME DO PROPRIETÁRIO/EMPRESA",
            "CPF/CNPJ",
            "DATA DE NASCIMENTO",
            "NOME DO CÔNJUGE",
            "E-MAIL",
            "TELEFONE",
        ],

        "DADOS DO IMÓVEL DO PROPRIETÁRIO": [
            "ENDEREÇO DA CASA DO PROPRIETÁRIO",
            "NÚMERO DA CASA DO PROPRIETÁRIO",
            "BAIRRO DA CASA DO PROPRIETÁRIO",
            "CIDADE DA CASA DO PROPRIETÁRIO",
            "ESTADO DA CASA DO PROPRIETÁRIO",
            "CEP DA CASA DO PROPRIETÁRIO",
            "COMPLEMENTO",
        ],

        "DADOS DO IMÓVEL CAPTADO": [
            "ENDEREÇO DO IMÓVEL (CAPTADO)",
            "NÚMERO DO IMÓVEL (CAPTADO)",
            "BAIRRO DO IMÓVEL (CAPTADO)",
            "CIDADE DO IMÓVEL (CAPTADO)",
            "CEP DO IMÓVEL (CAPTADO)",
            "ESTADO DO IMÓVEL (CAPTADO)",
            "COMPLEMENTO DO IMÓVEL (CAPTADO)",
        ],

        "CARACTERÍSTICAS GERAIS": [
            "SITUAÇAÕ DO IMÓVEL",
            "TIPO DO IMÓVEL",
            "NOME DA CONSTRUTORA",
            "IDADE DO IMÓVEL",
            "POSIÇÃO DO IMÓVEL",
            "TOPOGRAFIA",
            "PRAZO DE ENTREGA",
        ],

        "VALORES": [
            "PREÇO DO IMÓVEL (CAPTADO)",
            "PREÇO DO CONDOMÍNIO ",
            "PREÇO DO IPTU",
            "ACEITA PERMUTA?",
        ],

        "DISTRIBUIÇÃO DO IMÓVEL": [
            "QUANTIDADE DE QUARTO?",
            "QUANTIDADE DE SUÍTE?",
            "QUANTIDADE DE SALA?",
            "QUANTIDADE DE BANHEIRO?",
            "TEM VARANDA?",
            "TEM GARAGEM?",
            "CABE QUANTOS CARROS?",
            "A GARAGEM É COBERTA ?",
        ],

        "PRÉDIO / FACHADA": [
            "TIPO DE FACHADA?",
            "PAVIMENTOS",
            "TOTAL DE UNIDADES",
            "UNIDADES POR ANDAR",

        ],

        "SITUAÇÃO DO IMÓVEL": [
            "O IMÓVEL ESTÁ?",
            "SE OCUPADO, QUEM RESIDE?",
        ],

        "INFORMAÇÃO DA ÁREA DO IMÓVEL": [
            "ÁREA ÚTIL TOTAL DO IMÓVEL",
            "ÁREA LOTE / TERRENO",
            "ÁREA CONSTRUÍDA",
            "ÁREA DE FRENTE",
            "ÁREA DE FUNDO",
            "ÁREA LATERAL  - ESQUERDA",
            "ÁREA LATERAL - DIREITA",
        ],

        "DESCRIÇÃO COMPLEMENTAR": [
            "FAÇA UMA DESCRIÇÃO DETALHADA DO IMÓVEL",
            "VISTORIA",
        ],

        "CONDIÇÕES DE PAGAMENTO": [
            "O IMÓVEL TERÁ UMA ENTRADA?",
            "QUAL SERÁ O VALOR DA ENTRADA?",
            "QUAL A CONDIÇÃO DE PAGAMENTO?",
        ],

        "CARTÃO DE CRÉDITO": [
            "QUANTIDADE DE PARCELAS",
            "QUAL A DATA DO VENCIMENTO DA PARCELA",
            "QUAL O VALOR A SER PAGO POR PARCELA",
        ],

        "DOCUMENTAÇÃO DO IMÓVEL": [
            "IMÓVEL QUITADO",
            "O IMÓVEL POSSUI TODA DOCUMENTAÇÃO?",
            "QUAIS AS DOCUMENTAÇÕES QUE O IMÓVEL POSSUI?",
            "LOCAL DAS CHAVES",
        ],

        "CONDIÇÕES COMERCIAIS": [
            "POSSUI EXCLUSIVIDADE",
            "PRAZO DE EXCLUSIVDADE",
            "OPORTUNIDADE",
            "COMISSÃO DA IMOBILIÁRIA / CORRETOR? (%)",
        ],

        "ANEXOS": [
            "COLOQUE AS FOTOS DO IMÓVEL - PART 1",
            "COLOQUE AS FOTOS DO IMÓVEL - PART 2",
            "COLOQUE OS DOCUMENTOS DO IMÓVEL",
        ],

        "AUTORIZAÇÃO": [
            " Declaro que as informações prestadas são verdadeiras e autorizo a divulgação do"
            " imóvel para fins de venda/locação.",
        ],
    }

    for titulo, campos in secoes.items():
        desenhar_secao(titulo, campos)

    rodape()
    c.save()
