import streamlit as st
import pdfplumber
import re
from datetime import datetime

# Configuração da página com visual limpo
st.set_page_config(page_title="Conversor OFX", page_icon="🏦")

# CSS para um botão verde, pequeno e minimalista
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745;
        color: white;
        border-radius: 4px;
        border: none;
        padding: 6px 16px;
        font-size: 14px;
        font-weight: 500;
        transition: 0.3s;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #218838;
    }
    /* Esconde o menu padrão do Streamlit para ficar mais limpo */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Conversor OFX")

# Seleção do banco e upload em uma linha
col1, col2 = st.columns([1, 2])

with col1:
    banco = st.selectbox("Banco:", [
        "Santander", "Sicoob", "Itaú", "BB", "Caixa", 
        "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
    ])

with col2:
    arquivo_pdf = st.file_uploader("", type="pdf")

def parse_ofx(transacoes):
    dt = datetime.now().strftime('%Y%m%d')
    ofx = f"OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>\n"
    for t in transacoes:
        ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{dt}</DTPOSTED><TRNAMT>{t['v']}</TRNAMT><MEMO>{t['d'][:32]}</MEMO></STMTTRN>\n"
    ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
    return ofx

if arquivo_pdf:
    transacoes = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    if m_data and m_valor:
                        v = m_valor.group(1).replace('.', '').replace(',', '.')
                        d = linha.replace(m_data.group(1), '').replace(m_valor.group(1), '').strip()
                        transacoes.append({'v': v, 'd': d})

    if transacoes:
        st.success(f"{len(transacoes)} itens identificados.")
        
        # Botão discreto de download
        st.download_button(
            label="Baixar OFX",
            data=parse_ofx(transacoes),
            file_name=f"extrato_{banco.lower()}.ofx",
            mime="application/x-ofx"
        )
