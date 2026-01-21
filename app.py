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


# ===================== PDF =====================

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

    # ---------- CABEÇALHO ----------
    def desenhar_cabecalho():
        if os.path.exists(logo_path):
            c.drawImage(
                logo_path,
                margem_x,
                altura - 80,
                width=150,
                height=55,
                preserveAspectRatio=True,
                mask="auto"
            )

        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2 + 40, altura - 60, "FICHA DE CAPTAÇÃO DE IMÓVEL")

        c.setLineWidth(1)
        c.line(margem_x, altura - 90, largura - margem_x, altura - 90)

        c.setFont("Helvetica", 9)
        c.setFillColor(cinza)
        c.drawRightString(
            largura - margem_x,
            altura - 105,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        )

    # ---------- RODAPÉ ----------
    def desenhar_rodape():
        c.setFont("Helvetica", 8)
        c.setFillColor(HexColor("#777777"))
        c.drawRightString(largura - 40, 30, f"Página {c.getPageNumber()}")

    desenhar_cabecalho()
    y = altura - 130

    # ---------- NOVA PÁGINA ----------
    def nova_pagina():
        nonlocal y
        desenhar_rodape()
        c.showPage()
        desenhar_cabecalho()
        y = altura - 130

    # ---------- TEXTO LONGO ----------
    def desenhar_texto_longo(c, texto, x, y, largura_max, altura_pagina, margem_inferior):
        linhas = simpleSplit(texto, "Helvetica", 10, largura_max)
        for linha in linhas:
            if y < margem_inferior:
                nova_pagina()
                y = altura - 150
            c.drawString(x, y, linha)
            y -= 12
        return y - 6

# ===== SEÇÕES =====
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
            "imóvel para fins de venda/locação.",
        ],
}
    LARGURA_TEXTO = largura_util - 190

    def desenhar_secao(titulo, campos):
        nonlocal y

        altura_real = 30
        for campo in campos:
            valor = str(dados.get(campo, "—"))
            linhas = simpleSplit(valor, "Helvetica", 10, LARGURA_TEXTO)
            altura_real += 18 + (len(linhas) * 12)

        if y - altura_real < 80:
            nova_pagina()

        c.setStrokeColor(azul)
        c.setLineWidth(1)
        c.rect(margem_x, y - altura_real, largura_util, altura_real)

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(azul)
        c.drawString(margem_x + 10, y - 20, titulo)

        y_cursor = y - 38

        for campo in campos:
            valor = str(dados.get(campo, "—"))

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(preto)
            c.drawString(margem_x + 10, y_cursor, campo)

            x_valor = margem_x + 170

            c.setFont("Helvetica", 10)
            y_cursor = desenhar_texto_longo(
                c,
                valor,
                x_valor,
                y_cursor,
                LARGURA_TEXTO,
                altura,
                60
            )

        y -= altura_real + 15

    # ---------- DESENHAR PDF ----------
    for titulo, campos in secoes.items():
        desenhar_secao(titulo, campos)

    desenhar_rodape()
    c.save()
