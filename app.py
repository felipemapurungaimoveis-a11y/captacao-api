from flask import Flask, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit, ImageReader
from datetime import datetime
import io
import os
import qrcode

app = Flask(__name__)

# =========================================================
# ROTAS
# =========================================================

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

    nome = dados.get("NOME DO PROPRIETÁRIO/EMPRESA", "SEM_PROPRIETARIO")
    corretor = dados.get("CORRETOR CAPTADOR", "SEM_CORRETOR")

    nome_arquivo = (
        f"CAPTACAO - {nome} - {corretor} - "
        f"{datetime.now().strftime('%d-%m-%Y')}.pdf"
    )

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nome_arquivo,
        mimetype="application/pdf"
    )


# =========================================================
# PDF
# =========================================================

def gerar_pdf(buffer, dados):
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(BASE_DIR, "logo.png")

    azul = HexColor("#0A3D62")
    preto = HexColor("#000000")
    cinza = HexColor("#666666")
    verde = HexColor("#2E7D32")
    vermelho = HexColor("#C62828")

    margem_x = 40
    largura_util = largura - (margem_x * 2)
    y = altura - 130

    # =====================================================
    # CABEÇALHO / RODAPÉ
    # =====================================================

    def cabecalho():
        if os.path.exists(logo_path):
            c.drawImage(
                logo_path, margem_x, altura - 80,
                width=150, height=55,
                preserveAspectRatio=True, mask="auto"
            )

        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2 + 40, altura - 60,
                            "FICHA DE CAPTAÇÃO DE IMÓVEL")

        c.setLineWidth(1)
        c.line(margem_x, altura - 90, largura - margem_x, altura - 90)

        c.setFont("Helvetica", 9)
        c.setFillColor(cinza)
        c.drawRightString(
            largura - margem_x, altura - 105,
            datetime.now().strftime("%d/%m/%Y %H:%M")
        )

    def rodape():
        c.setFont("Helvetica", 8)
        c.setFillColor(cinza)
        c.drawRightString(largura - 40, 30, f"Página {c.getPageNumber()}")

    def nova_pagina():
        nonlocal y
        rodape()
        c.showPage()
        cabecalho()
        y = altura - 130

    # =====================================================
    # CAPA
    # =====================================================

    def capa():
        if os.path.exists(logo_path):
            c.drawImage(
                logo_path,
                largura / 2 - 120,
                altura - 200,
                width=240,
                height=90,
                preserveAspectRatio=True,
                mask="auto"
            )

        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(azul)
        c.drawCentredString(largura / 2, altura - 300,
                            "FICHA DE CAPTAÇÃO DE IMÓVEL")

        c.setFont("Helvetica", 14)
        c.setFillColor(preto)

        c.drawCentredString(
            largura / 2, altura - 360,
            f"Proprietário: {dados.get('NOME DO PROPRIETÁRIO/EMPRESA', '—')}"
        )

        c.drawCentredString(
            largura / 2, altura - 390,
            f"Corretor: {dados.get('CORRETOR CAPTADOR', '—')}"
        )

        c.drawCentredString(
            largura / 2, altura - 420,
            f"Código do Imóvel: {dados.get('CÓD DO IMÓVEL', '—')}"
        )

        c.setFont("Helvetica", 10)
        c.setFillColor(cinza)
        c.drawCentredString(
            largura / 2, 100,
            f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )

        c.showPage()

    # =====================================================
    # FORMATADORES
    # =====================================================

    def moeda(valor):
        try:
            valor = str(valor).replace(".", "").replace(",", ".")
            n = float(valor)
            return f"R$ {n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return valor

    def sim_nao(valor, x, y):
        v = valor.upper()
        if v == "SIM":
            c.setFillColor(verde)
            c.drawString(x, y, "✔ SIM")
        elif v in ["NÃO", "NAO"]:
            c.setFillColor(vermelho)
            c.drawString(x, y, "✖ NÃO")
        else:
            c.setFillColor(preto)
            c.drawString(x, y, valor)
        c.setFillColor(preto)
        return y - 14

    # =====================================================
    # SEÇÕES (2 COLUNAS)
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

    col_x = [margem_x, margem_x + largura_util / 2]
    largura_col = (largura_util / 2) - 20

    def secao(titulo, campos):
        nonlocal y

        c.setFont("Helvetica-Bold", 13)
        c.setFillColor(azul)

        if y < 140:
            nova_pagina()

        c.drawString(margem_x, y, titulo)
        y -= 20

        col = 0
        y_base = y

        for campo in campos:
            valor = str(dados.get(campo, "—"))

            if "PREÇO" in campo or "VALOR" in campo:
                valor = moeda(valor)

            c.setFont("Helvetica-Bold", 9)
            c.drawString(col_x[col], y, campo)
            y -= 12

            c.setFont("Helvetica", 10)

            if valor.upper() in ["SIM", "NÃO", "NAO"]:
                y = sim_nao(valor, col_x[col], y)
            else:
                linhas = simpleSplit(valor, "Helvetica", 10, largura_col)
                for l in linhas:
                    c.drawString(col_x[col], y, l)
                    y -= 12

            if col == 0:
                col = 1
                y = y_base
            else:
                col = 0
                y_base = min(y, y_base) - 18
                y = y_base

            if y < 80:
                nova_pagina()

    # =====================================================
    # FOTOS
    # =====================================================

    def fotos():
        fotos = dados.get("COLOQUE AS FOTOS DO IMÓVEL - PART 1", [])
        if not isinstance(fotos, list):
            return

        margem = 40
        img_w = (largura - margem * 3) / 2
        img_h = 180

        x_pos = [margem, margem * 2 + img_w]
        y_img = altura - 100
        col = 0

        for url in fotos:
            try:
                img = ImageReader(url)
                c.drawImage(img, x_pos[col], y_img - img_h,
                            width=img_w, height=img_h,
                            preserveAspectRatio=True, mask="auto")

                col += 1
                if col > 1:
                    col = 0
                    y_img -= img_h + 20

                if y_img < 200:
                    c.showPage()
                    y_img = altura - 100
            except:
                pass

        c.showPage()

    # =====================================================
    # QR CODE
    # =====================================================

    def qrcode_imovel():
        valor = dados.get("LINK DO IMÓVEL") or dados.get("CÓD DO IMÓVEL")
        if not valor:
            return

        qr = qrcode.make(valor)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        buf.seek(0)

        c.drawImage(
            ImageReader(buf),
            largura / 2 - 60,
            80,
            width=120,
            height=120
        )

        c.setFont("Helvetica", 9)
        c.drawCentredString(largura / 2, 60,
                            "Escaneie para acessar o imóvel")

    # =====================================================
    # EXECUÇÃO
    # =====================================================

    capa()
    cabecalho()

    for titulo, campos in secoes.items():
        secao(titulo, campos)

    fotos()
    qrcode_imovel()
    rodape()
    c.save()
