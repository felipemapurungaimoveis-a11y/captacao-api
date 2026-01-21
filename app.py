from flask import Flask, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
from datetime import datetime
import io
import os
import qrcode

# ===== GOOGLE DRIVE =====
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ===== CONFIG =====
PASTA_DRIVE_ID = "1Acbxy3rMIUTo1wklCLJMRTfiYWJPqFXf"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
CREDENCIAL = os.path.join(BASE_DIR, "credentials.json")

SCOPES = ["https://www.googleapis.com/auth/drive"]

app = Flask(__name__)

# ===== CORES POR SEÇÃO =====
CORES_SECAO = {
    "CORRETOR": HexColor("#0A3D62"),
    "CÓDIGO DO IMÓVEL": HexColor("#1B5E20"),
    "DADOS DO PROPRIETÁRIO": HexColor("#283593"),
    "DADOS DO IMÓVEL DO PROPRIETÁRIO": HexColor("#4E342E"),
    "DADOS DO IMÓVEL CAPTADO": HexColor("#1565C0"),
    "CARACTERÍSTICAS GERAIS": HexColor("#455A64"),
    "VALORES": HexColor("#B71C1C"),
    "DESCRIÇÃO COMPLEMENTAR": HexColor("#37474F"),
    "AUTORIZAÇÃO": HexColor("#263238"),
}

# ===== DRIVE SERVICE =====
def drive_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENCIAL, scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)

# ===== SALVAR PDF NO DRIVE =====
def salvar_no_drive(caminho, nome):
    service = drive_service()

    media = MediaFileUpload(caminho, mimetype="application/pdf")
    file_metadata = {
        "name": nome,
        "parents": [PASTA_DRIVE_ID]
    }

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    file_id = file.get("id")

    # Tornar público
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return f"https://drive.google.com/file/d/{file_id}/view"

# ===== GERAR PDF =====
def gerar_pdf(buffer, dados, qr_url):
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    margem_x = 40
    largura_util = largura - (margem_x * 2)
    y = altura - 120

    # ===== CABEÇALHO =====
    if os.path.exists(LOGO_PATH):
        c.drawImage(LOGO_PATH, margem_x, altura - 80, width=140, height=50, preserveAspectRatio=True)

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(largura / 2 + 40, altura - 55, "FICHA DE CAPTAÇÃO DE IMÓVEL")

    c.setLineWidth(1)
    c.line(margem_x, altura - 90, largura - margem_x, altura - 90)

    c.setFont("Helvetica", 9)
    c.drawRightString(largura - margem_x, altura - 105,
                      datetime.now().strftime("%d/%m/%Y %H:%M"))

    # ===== QR CODE =====
    qr_img = qrcode.make(qr_url)
    qr_path = os.path.join(BASE_DIR, "qr_temp.png")
    qr_img.save(qr_path)

    c.drawImage(qr_path, largura - 140, 60, width=90, height=90)
    c.setFont("Helvetica", 8)
    c.drawCentredString(largura - 95, 50, "Acesse este imóvel")

    # ===== FUNÇÕES =====
    def nova_pagina():
        nonlocal y
        c.showPage()
        y = altura - 120

    def desenhar_texto(c, texto, x, y, largura_max):
        linhas = simpleSplit(texto, "Helvetica", 10, largura_max)
        for linha in linhas:
            if y < 60:
                nova_pagina()
            c.drawString(x, y, linha)
            y -= 12
        return y - 4

    def desenhar_secao(titulo, campos):
        nonlocal y
        cor = CORES_SECAO.get(titulo, HexColor("#0A3D62"))

        c.setFillColor(cor)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margem_x, y, titulo)
        y -= 18

        for campo in campos:
            valor = str(dados.get(campo, "—"))

            c.setFillColor(HexColor("#000000"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(margem_x, y, campo)

            c.setFont("Helvetica", 10)
            y = desenhar_texto(c, valor, margem_x + 180, y, largura_util - 190)

        y -= 10

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

    for titulo, campos in secoes.items():
        if y < 120:
            nova_pagina()
        desenhar_secao(titulo, campos)

    c.save()

# ===== API =====
@app.route("/captacao", methods=["POST"])
def captacao():
    dados = request.get_json()
    if not dados:
        return {"erro": "Dados vazios"}, 400

    buffer = io.BytesIO()

    nome_pdf = f"CAPTACAO - {dados.get('NOME DO PROPRIETÁRIO/EMPRESA','SEM_NOME')} - {datetime.now().strftime('%d-%m-%Y')}.pdf"
    caminho_temp = os.path.join(BASE_DIR, "temp.pdf")

    gerar_pdf(buffer, dados, "TEMP")
    buffer.seek(0)

    with open(caminho_temp, "wb") as f:
        f.write(buffer.read())

    link_pdf = salvar_no_drive(caminho_temp, nome_pdf)

    buffer_final = io.BytesIO()
    gerar_pdf(buffer_final, dados, link_pdf)
    buffer_final.seek(0)

    os.remove(caminho_temp)
    os.remove(os.path.join(BASE_DIR, "qr_temp.png"))

    return send_file(buffer_final, mimetype="application/pdf")
