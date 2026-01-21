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

        coluna_x = [margem_x + 10, margem_x + largura_util / 2 + 10]
        largura_coluna = (largura_util / 2) - 30

        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(azul)

        if y < 120:
            nova_pagina()

        c.drawString(margem_x + 10, y, titulo)
        y -= 20

        col = 0
        y_inicial = y

        for campo in campos:
            valor = str(dados.get(campo, "—"))

            # Detecta valores monetários
            if "PREÇO" in campo or "VALOR" in campo or "R$" in valor:
                valor = formatar_moeda(valor)

            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(preto)
            c.drawString(coluna_x[col], y, campo)

            y -= 12
            c.setFont("Helvetica", 10)

            # SIM / NÃO
            if valor.upper() in ["SIM", "NÃO", "NAO"]:
                y = desenhar_sim_nao(c, valor, coluna_x[col], y)
            else:
                linhas = simpleSplit(valor, "Helvetica", 10, largura_coluna)
                for linha in linhas:
                    c.drawString(coluna_x[col], y, linha)
                    y -= 12

            # Alterna coluna
            if col == 0:
                col = 1
                y = y_inicial
            else:
                col = 0
                y = min(y, y_inicial) - 18
                y_inicial = y

            if y < 80:
                nova_pagina()
                y -= 20

    def formatar_moeda(valor):
        try:
            valor = str(valor).replace(".", "").replace(",", ".")
            numero = float(valor)
            return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return valor

    def desenhar_sim_nao(c, texto, x, y):
        texto = texto.strip().upper()

        if texto == "SIM":
            c.setFillColor(HexColor("#2E7D32"))
            c.drawString(x, y, "✔ SIM")
            c.setFillColor(HexColor("#000000"))
            return y - 14

        if texto == "NÃO" or texto == "NAO":
            c.setFillColor(HexColor("#C62828"))
            c.drawString(x, y, "✖ NÃO")
            c.setFillColor(HexColor("#000000"))
            return y - 14

        c.drawString(x, y, texto)
        return y - 14

    # ---------- DESENHAR PDF ----------
    for titulo, campos in secoes.items():
        desenhar_secao(titulo, campos)

    desenhar_rodape()
    c.save()
