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

    return send_file(buffer, as_attachment=True,
                     download_name="captacao.pdf",
                     mimetype="application/pdf")

# =====================================================
# CONFIGURAÇÕES
# =====================================================

CAMPOS_BOOLEANOS = {
    "ACEITA PERMUTA?",
    "TEM VARANDA?",
    "TEM GARAGEM?",
    "A GARAGEM É COBERTA ?",
    "IMÓVEL QUITADO",
    "O IMÓVEL POSSUI TODA DOCUMENTAÇÃO?",
    "POSSUI EXCLUSIVIDADE",
}

def formatar_valor(valor):
    try:
        v = float(str(valor).replace(".", "").replace(",", "."))
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return valor

def texto_quebrado(texto, largura):
    return simpleSplit(str(texto), "Helvetica", 10, largura)

def desenhar_badge(c, x, y, texto, cor):
    c.setFillColor(cor)
    c.roundRect(x, y, 36, 14, 5, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + 18, y + 4, texto)

# =====================================================
# CAPA
# =====================================================

def desenhar_capa(c, largura, altura, dados, logo_path):
    azul = HexColor("#0A3D62")
    preto = HexColor("#000000")

    if os.path.exists(logo_path):
        c.drawImage(logo_path, largura/2 - 80, altura - 170,
                    width=160, height=55, mask="auto")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(azul)
    c.drawCentredString(largura/2, altura - 260,
                         "FICHA DE CAPTAÇÃO DE IMÓVEL")

    infos = [
        ("PROPRIETÁRIO", dados.get("NOME DO PROPRIETÁRIO/EMPRESA", "—")),
        ("CORRETOR", dados.get("CORRETOR CAPTADOR", "—")),
        ("CÓDIGO DO IMÓVEL", dados.get("CÓD DO IMÓVEL", "—")),
        ("DATA", datetime.now().strftime("%d/%m/%Y")),
    ]

    y = altura - 340
    for titulo, valor in infos:
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(preto)
        c.drawCentredString(largura/2, y, titulo)

        c.setFont("Helvetica", 14)
        c.setFillColor(azul)
        c.drawCentredString(largura/2, y - 20, valor)

        y -= 60

# =====================================================
# PDF PRINCIPAL
# =====================================================

def gerar_pdf(buffer, dados):
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "logo.png")

    desenhar_capa(c, largura, altura, dados, logo_path)
    c.showPage()

    margem_x = 40
    largura_util = largura - margem_x * 2
    coluna_larg = (largura_util - 20) / 2

    azul = HexColor("#0A3D62")
    cinza = HexColor("#666666")
    preto = HexColor("#000000")
    verde = HexColor("#2E7D32")
    vermelho = HexColor("#C62828")

    def cabecalho():
        if os.path.exists(logo_path):
            c.drawImage(logo_path, margem_x, altura - 75,
                        width=110, height=38, mask="auto")

        c.setFont("Helvetica-Bold", 15)
        c.setFillColor(azul)
        c.drawCentredString(largura/2 + 30, altura - 55,
                             "FICHA DE CAPTAÇÃO DE IMÓVEL")
        c.line(margem_x, altura - 90, largura - margem_x, altura - 90)

    def rodape():
        c.setFont("Helvetica", 8)
        c.setFillColor(cinza)
        c.drawRightString(largura - margem_x, 30,
                           f"Página {c.getPageNumber()}")

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

        altura = 30
        for campo in campos:
            linhas = texto_quebrado(dados.get(campo, "—"), coluna_larg - 20)
            altura += max(26, len(linhas) * 11 + 8)

        if y - altura < 100:
            nova_pagina()

        c.setFillColor(azul)
        c.rect(margem_x, y - 28, largura_util, 24, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(HexColor("#FFFFFF"))
        c.drawCentredString(margem_x + largura_util/2, y - 20, titulo)

        y_cursor = y - 45
        col = 0

        for campo in campos:
            valor = dados.get(campo, "—")
            x = margem_x + (coluna_larg + 20 if col else 0)

            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(cinza)
            c.drawString(x + 8, y_cursor, campo)

            c.setFont("Helvetica", 10)
            c.setFillColor(preto)

            if campo in CAMPOS_BOOLEANOS:
                badge_cor = verde if str(valor).lower() == "sim" else vermelho
                desenhar_badge(c, x + 8, y_cursor - 16,
                               "SIM" if str(valor).lower() == "sim" else "NÃO",
                               badge_cor)
                h = 28
            else:
                if "PREÇO" in campo or "VALOR" in campo:
                    valor = formatar_valor(valor)

                y_txt = y_cursor - 14
                for linha in texto_quebrado(valor, coluna_larg - 20):
                    c.drawString(x + 8, y_txt, linha)
                    y_txt -= 12
                h = abs(y_txt - y_cursor)

            if col:
                y_cursor -= max(32, h + 6)
                col = 0
            else:
                col = 1

        y -= altura + 4

    # =====================================================
    # SEÇÕES
    # =====================================================

    secoes = {
        "CORRETOR": [
            "CORRETOR CAPTADOR",
        ],
        "CÓDIGO DO IMÓVEL": [
            "CÓD DO IMÓVEL",
        ],

        "DADOS DO PROPRIETÁRIO": [
            "NOME DO PROPRIETÁRIO/EMPRESA",
            "CPF / CNPJ",
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

    for t, cpos in secoes.items():
        desenhar_secao(t, cpos)

    # =====================================================
    # ASSINATURAS PREMIUM (PÁGINA EXCLUSIVA)
    # =====================================================

    nova_pagina()

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(preto)
    c.drawCentredString(
        largura / 2,
        altura - 140,
        "ASSINATURAS"
    )

    # Linha decorativa
    c.setLineWidth(1)
    c.line(
        largura / 2 - 120,
        altura - 150,
        largura / 2 + 120,
        altura - 150
    )

    y_ass = altura - 260

    # Configurações dos blocos
    larg_bloco = 220
    altura_linha = 50

    blocos = [
        ("PROPRIETÁRIO / CLIENTE", dados.get("NOME DO PROPRIETÁRIO/EMPRESA", "")),
        ("CORRETOR RESPONSÁVEL", dados.get("CORRETOR CAPTADOR", "")),
        ("IMOBILIÁRIA", "ASSINATURA INSTITUCIONAL"),
    ]

    x_positions = [
        margem_x,
        largura / 2 - larg_bloco / 2,
        largura - margem_x - larg_bloco
    ]

    for i, (titulo, nome) in enumerate(blocos):
        x = x_positions[i]

        # Linha de assinatura (dupla)
        c.setLineWidth(1)
        c.line(x, y_ass, x + larg_bloco, y_ass)
        c.setLineWidth(0.5)
        c.line(x, y_ass - 3, x + larg_bloco, y_ass - 3)

        # Nome
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(
            x + larg_bloco / 2,
            y_ass - 18,
            nome if nome else " "
        )

        # Cargo
        c.setFont("Helvetica", 9)
        c.setFillColor(cinza)
        c.drawCentredString(
            x + larg_bloco / 2,
            y_ass - 32,
            titulo
        )

    # Local e data (rodapé elegante)
    c.setFont("Helvetica", 9)
    c.setFillColor(cinza)
    c.drawString(
        margem_x,
        80,
        f"Documento gerado em {datetime.now().strftime('%d/%m/%Y')}"
    )
    rodape()
    c.save()
