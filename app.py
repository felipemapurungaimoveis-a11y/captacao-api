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

# =========================================================
# CORES
# =========================================================
azul = HexColor("#0A3D62")
cinza = HexColor("#555555")
preto = HexColor("#000000")
verde = HexColor("#2E7D32")
vermelho = HexColor("#C62828")

# =========================================================
# FORMATADORES
# =========================================================
def eh_valor(campo):
    campo = campo.upper()
    return any(p in campo for p in ["PREÇO", "VALOR", "COMISSÃO", "IPTU", "CONDOMÍNIO"])

def formatar_valor(valor):
    try:
        v = float(str(valor).replace(".", "").replace(",", "."))
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def campo_booleano(campo):
    campo = campo.upper()
    return any(p in campo for p in ["ACEITA", "POSSUI", "TEM", "É", "ESTÁ"])

def normalizar_bool(valor):
    if isinstance(valor, str):
        v = valor.strip().lower()
        if v in ["sim", "s", "true", "1"]:
            return True
        if v in ["não", "nao", "n", "false", "0"]:
            return False
    return None

def desenhar_badge(c, x, y, texto, cor):
    largura = 42
    c.setFillColor(cor)
    c.roundRect(x, y, largura, 16, 8, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawCentredString(x + largura / 2, y + 4, texto)

# =========================================================
# PDF
# =========================================================
def gerar_pdf(buffer, dados):
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "logo.png")

    margem_x = 40
    largura_util = largura - (margem_x * 2)
    LARG_COL = (largura_util - 20) / 2

    # ================= CAPA =================
    if os.path.exists(logo_path):
        c.drawImage(
            logo_path,
            largura / 2 - 90,
            altura - 170,
            width=180,
            height=65,
            preserveAspectRatio=True
        )

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(azul)
    c.drawCentredString(largura / 2, altura - 260, "FICHA DE CAPTAÇÃO DE IMÓVEL")

    c.setFont("Helvetica", 14)
    y_info = altura - 330

    infos = [
        ("PROPRIETÁRIO", dados.get("NOME DO PROPRIETÁRIO/EMPRESA", "—")),
        ("CORRETOR", dados.get("CORRETOR CAPTADOR", "—")),
        ("CÓDIGO DO IMÓVEL", dados.get("CÓD DO IMÓVEL", "—")),
        ("DATA", datetime.now().strftime("%d/%m/%Y")),
    ]

    for titulo, valor in infos:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(cinza)
        c.drawCentredString(largura / 2, y_info, titulo)

        c.setFont("Helvetica", 15)
        c.setFillColor(preto)
        c.drawCentredString(largura / 2, y_info - 22, str(valor))
        y_info -= 70

    c.showPage()

    # ================= CABEÇALHO =================
    def cabecalho():
        if os.path.exists(logo_path):
            c.drawImage(
                logo_path,
                margem_x,
                altura - 80,
                width=120,
                height=45,
                preserveAspectRatio=True
            )

        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2, altura - 55, "FICHA DE CAPTAÇÃO DE IMÓVEL")

    def rodape():
        c.setFont("Helvetica", 8)
        c.setFillColor(cinza)
        c.drawRightString(largura - margem_x, 30, f"Página {c.getPageNumber()}")

    y = altura - 120
    cabecalho()

    def nova_pagina():
        nonlocal y
        rodape()
        c.showPage()
        cabecalho()
        y = altura - 120

    def texto_quebrado(texto, largura_max):
        return simpleSplit(str(texto), "Helvetica", 10, largura_max)

    CORES_SECAO = {
        "VALORES": HexColor("#B71C1C"),
        "DESCRIÇÃO COMPLEMENTAR": HexColor("#37474F"),
    }

    def desenhar_secao(titulo, campos):
        nonlocal y
        cor = CORES_SECAO.get(titulo, azul)

        altura_real = 40 + len(campos) * 45
        if y - altura_real < 120:
            nova_pagina()

        c.setStrokeColor(cor)
        c.setLineWidth(1.4)
        c.rect(margem_x, y - altura_real, largura_util, altura_real)

        c.setFillColor(cor)
        c.rect(margem_x, y - 32, largura_util, 28, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(HexColor("#FFFFFF"))
        c.drawCentredString(margem_x + largura_util / 2, y - 22, titulo)

        y_cursor = y - 50
        coluna = 0

        for campo in campos:
            valor = dados.get(campo, "—")
            x = margem_x + (LARG_COL + 20 if coluna else 0)

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(preto)
            c.drawString(x + 10, y_cursor, campo)

            if campo_booleano(campo):
                bool_val = normalizar_bool(valor)
                if bool_val is not None:
                    desenhar_badge(
                        c,
                        x + 10,
                        y_cursor - 16,
                        "SIM" if bool_val else "NÃO",
                        verde if bool_val else vermelho
                    )
                else:
                    c.drawString(x + 10, y_cursor - 14, str(valor))
            else:
                if eh_valor(campo):
                    valor = formatar_valor(valor)

                linhas = texto_quebrado(valor, LARG_COL - 20)
                y_texto = y_cursor - 14
                for linha in linhas:
                    c.drawString(x + 10, y_texto, linha)
                    y_texto -= 12

            coluna = 1 - coluna
            if coluna == 0:
                y_cursor -= 50

        y -= altura_real + 30

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
            " Declaro que as informações prestadas são verdadeiras e autorizo "
            "a divulgação do imóvel para fins de venda/locação.",
        ],
    }

    for titulo, campos in secoes.items():
        desenhar_secao(titulo, campos)

    # ================= ASSINATURAS (PREMIUM) =================
    nova_pagina()

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(largura / 2, altura - 120, "ASSINATURAS")

    y_ass = altura - 220
    largura_linha = 220

    for nome in ["CLIENTE / PROPRIETÁRIO", "CORRETOR", "IMOBILIÁRIA"]:
        x = (largura - largura_linha) / 2
        c.line(x, y_ass, x + largura_linha, y_ass)
        c.setFont("Helvetica", 10)
        c.drawCentredString(largura / 2, y_ass - 18, nome)
        y_ass -= 90

    rodape()
    c.save()
