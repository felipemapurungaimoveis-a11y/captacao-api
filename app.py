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

# ======================================================
# UTILITÁRIOS
# ======================================================

def formatar_valor(valor):
    try:
        valor = float(str(valor).replace(".", "").replace(",", "."))
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

def normalizar_bool(valor):
    if str(valor).strip().lower() in ["sim", "yes", "true", "1"]:
        return True
    if str(valor).strip().lower() in ["não", "nao", "no", "false", "0"]:
        return False
    return None

def eh_valor(campo):
    return any(x in campo.upper() for x in ["PREÇO", "VALOR", "IPTU", "CONDOMÍNIO"])

def desenhar_badge(c, x, y, texto, cor):
    c.setFillColor(cor)
    c.roundRect(x, y, 38, 16, 6, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + 19, y + 5, texto)

def texto_quebrado(texto, largura):
    return simpleSplit(str(texto), "Helvetica", 10, largura)

# ======================================================
# CAPA
# ======================================================

def desenhar_capa(c, largura, altura, dados, logo_path):
    azul = HexColor("#0A3D62")
    cinza = HexColor("#555555")

    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            largura / 2 - 80,
            altura - 180,
            width=160,
            height=60,
            preserveAspectRatio=True,
            mask="auto"
        )

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(azul)
    c.drawCentredString(largura / 2, altura - 280, "FICHA DE CAPTAÇÃO DE IMÓVEL")

    c.setLineWidth(2)
    c.line(largura / 2 - 200, altura - 305, largura / 2 + 200, altura - 305)

    infos = [
        ("PROPRIETÁRIO", dados.get("NOME DO PROPRIETÁRIO/EMPRESA", "—")),
        ("CORRETOR", dados.get("CORRETOR CAPTADOR", "—")),
        ("CÓDIGO DO IMÓVEL", dados.get("CÓD DO IMÓVEL", "—")),
        ("DATA", datetime.now().strftime("%d/%m/%Y")),
    ]

    y = altura - 360
    for titulo, valor in infos:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cinza)
        c.drawCentredString(largura / 2, y, titulo)

        c.setFont("Helvetica", 14)
        c.drawCentredString(largura / 2, y - 22, valor)

        y -= 70

# ======================================================
# PDF PRINCIPAL
# ======================================================

def gerar_pdf(buffer, dados):
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "logo.png")

    desenhar_capa(c, largura, altura, dados, logo_path)
    c.showPage()

    margem_x = 40
    largura_util = largura - margem_x * 2
    LARG_COL = (largura_util - 20) / 2

    azul = HexColor("#0A3D62")
    cinza = HexColor("#666666")
    preto = HexColor("#000000")
    verde = HexColor("#2E7D32")
    vermelho = HexColor("#C62828")

    CORES_SECAO = {
        "CORRETOR": HexColor("#0A3D62"),
        "VALORES": HexColor("#B71C1C"),
        "DESCRIÇÃO COMPLEMENTAR": HexColor("#37474F"),
        "AUTORIZAÇÃO": HexColor("#263238"),
    }

    def cabecalho():
        if os.path.exists(logo_path):
            c.drawImage(logo_path, margem_x, altura - 80, width=110, height=40, mask="auto")

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2 + 30, altura - 55, "FICHA DE CAPTAÇÃO DE IMÓVEL")

        c.line(margem_x, altura - 90, largura - margem_x, altura - 90)

    def rodape():
        c.setFont("Helvetica", 8)
        c.setFillColor(cinza)
        c.drawRightString(largura - margem_x, 30, f"Página {c.getPageNumber()}")

    y = altura - 130
    cabecalho()

    def nova_pagina():
        nonlocal y
        rodape()
        c.showPage()
        cabecalho()
        y = altura - 130

    def desenhar_secao(titulo, campos):
        nonlocal y
        cor = CORES_SECAO.get(titulo, azul)

        altura = 50
        for campo in campos:
            valor = dados.get(campo, "—")
            linhas = texto_quebrado(valor, LARG_COL - 20)
            altura += max(55, len(linhas) * 14)

        if y - altura < 120:
            nova_pagina()

        c.setFillColor(cor)
        c.rect(margem_x, y - 30, largura_util, 26, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(HexColor("#FFFFFF"))
        c.drawCentredString(margem_x + largura_util / 2, y - 22, titulo)

        y_cursor = y - 50
        coluna = 0

        for campo in campos:
            valor = dados.get(campo, "—")
            x = margem_x + (LARG_COL + 20 if coluna else 0)

            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(cinza)
            c.drawString(x + 10, y_cursor, campo.upper())

            c.line(x + 10, y_cursor - 3, x + LARG_COL - 10, y_cursor - 3)

            bool_val = normalizar_bool(valor)

            if bool_val is not None:
                desenhar_badge(
                    c,
                    x + 10,
                    y_cursor - 20,
                    "SIM" if bool_val else "NÃO",
                    verde if bool_val else vermelho
                )
                altura_campo = 40
            else:
                if eh_valor(campo):
                    valor = formatar_valor(valor)

                c.setFont("Helvetica", 10)
                c.setFillColor(preto)
                y_texto = y_cursor - 18
                for linha in texto_quebrado(valor, LARG_COL - 20):
                    c.drawString(x + 10, y_texto, linha)
                    y_texto -= 12

                altura_campo = abs(y_texto - y_cursor)

            if coluna:
                y_cursor -= max(60, altura_campo + 10)
                coluna = 0
            else:
                coluna = 1

        y -= altura + 20

    # ===================== SEÇÕES ======================

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
            " Declaro que as informações prestadas são verdadeiras e autorizo a divulgação do imóvel para fins de venda/locação.",
        ],
    }

    for titulo, campos in secoes.items():
        desenhar_secao(titulo, campos)

    # ===================== ASSINATURAS ======================

    if y < 200:
        nova_pagina()

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura / 2, y - 20, "ASSINATURAS")

    y_ass = y - 80
    linhas = [
        ("PROPRIETÁRIO", margem_x),
        ("CORRETOR", largura / 2 - 80),
        ("IMOBILIÁRIA", largura - margem_x - 200),
    ]

    for titulo, x in linhas:
        c.line(x, y_ass, x + 180, y_ass)
        c.drawCentredString(x + 90, y_ass - 14, titulo)

    rodape()
    c.save()
