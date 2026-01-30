import streamlit as st

# 1. Configuração da Página (O nome que aparece na aba do navegador)
st.set_page_config(page_title="OFX Transforms", page_icon="🏦", layout="wide")

# 2. A "Tinta" do Fundo (Muda a cor da parede)
st.markdown("""
    <style>
    .stApp {
        background-color: #F0F8FF; /* Um azul clarinho bem calmo */
    }
    .stHeader {
        background-color: rgba(0,0,0,0);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. O Título Novo
st.title("🏦 OFX Transforms")
st.write("Transforme seus arquivos de forma simples e rápida.")

# 4. Organizando em Colunas (Para não ficar tudo espalhado)
col1, col2 = st.columns([1, 2])

with col1:
    banco = st.selectbox("Escolha o seu Banco:", ["Santander", "Itaú", "Bradesco", "Outros"])

with col2:
    arquivo = st.file_uploader("Arraste seu arquivo OFX aqui", type=["ofx", "pdf"])

import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

# Configuração da aba do navegador
st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

# Visual minimalista com botão verde
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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("🤖 OFX Transforms")

# Layout simples
col1, col2 = st.columns([1, 2])

with col1:
    banco = st.selectbox("Banco:", [
        "Santander", "Sicoob", "Itaú", "BB", "Caixa", 
        "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
    ])

with col2:
    arquivo_pdf = st.file_uploader("", type="pdf")

if arquivo_pdf:
    # Animação Transformers (Rápida e Pequena)
    progresso = st.empty()
    frames = ["📄", "⚙️", "🤖", "💸", "✨", "✅"]
    
    for frame in frames:
        progresso.markdown(f"<h3 style='text-align: center;'>{frame}</h3>", unsafe_allow_html=True)
        time.sleep(0.15)
    
    progresso.empty() 

    # Processamento dos dados
    transacoes = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    if m_data and m_valor:
                        # Converte para o padrão americano do OFX
                        v = m_valor.group(1).replace('.', '').replace(',', '.')
                        d = linha.replace(m_data.group(1), '').replace(m_valor.group(1), '').strip()
                        transacoes.append({'v': v, 'd': d})

    if transacoes:
        st.success(f"🤖 Transformação concluída! {len(transacoes)} itens.")
        
        # Estrutura do arquivo OFX
        dt = datetime.now().strftime('%Y%m%d')
        ofx = f"OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>\n"
        for t in transacoes:
            ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{dt}</DTPOSTED><TRNAMT>{t['v']}</TRNAMT><MEMO>{t['d'][:32]}</MEMO></STMTTRN>\n"
        ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        st.download_button(
            label="Baixar OFX",
            data=ofx,
            file_name=f"extrato_{banco.lower()}.ofx",
            mime="application/x-ofx"
        )
