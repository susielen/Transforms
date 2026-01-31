import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

# Configuração da aba do navegador
st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

# Estilo visual
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
    </style>
""", unsafe_allow_html=True)

st.title("🤖 OFX Transforms (Padrão Domínio)")

col1, col2 = st.columns([1, 2])

with col1:
    banco_selecionado = st.selectbox("Banco:", [
        "Santander", "Sicoob", "Itaú", "BB", "Caixa", 
        "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
    ])

with col2:
    arquivo_pdf = st.file_uploader("", type="pdf")

if arquivo_pdf:
    # Animação
    progresso = st.empty()
    for frame in ["📄", "⚙️", "🤖", "✨", "✅"]:
        progresso.markdown(f"<h3 style='text-align: center;'>{frame}</h3>", unsafe_allow_html=True)
        time.sleep(0.1)
    progresso.empty() 

    transacoes = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    if m_data and m_valor:
                        # Limpa o valor para o padrão americano (1000.00)
                        v = m_valor.group(1).replace('.', '').replace(',', '.')
                        # Pega o texto da descrição
                        d = linha.replace(m_data.group(1), '').replace(m_valor.group(1), '').strip()
                        transacoes.append({'v': v, 'd': d})

    if transacoes:
        st.success(f"🤖 Transformação concluída! {len(transacoes)} itens encontrados.")

        # --- CONSTRUÇÃO DO OFX PADRÃO BANCO/DOMÍNIO ---
        dt_agora = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 1. Cabeçalho SGML (Obrigatório para o Domínio)
        ofx = "OFXHEADER:100\n"
        ofx += "DATA:OFXSGML\n"
        ofx += "VERSION:102\n"
        ofx += "SECURITY:NONE\n"
        ofx += "ENCODING:USASCII\n"
        ofx += "CHARSET:1252\n"
        ofx += "COMPRESSION:NONE\n"
        ofx += "OLDFILEUID:NONE\n"
        ofx += "NEWFILEUID:NONE\n\n"
        
        # 2. Abertura das tags
        ofx += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>\n"
        ofx += f"<DTSERVER>{dt_agora}</DTSERVER>\n<LANGUAGE>POR</LANGUAGE>\n</SONRS>\n</SIGNONMSGSRSV1>\n"
        ofx += "<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL</CURDEF>\n"
        
        # 3. Dados da conta (Essencial para o sistema não rejeitar)
        ofx += "<BANKACCTFROM>\n<BANKID>0000</BANKID>\n<ACCTID>000000</ACCTID>\n<ACCTTYPE>CHECKING</ACCTTYPE>\n</BANKACCTFROM>\n"
        ofx += "<BANKTRANLIST>\n"
        ofx += f"<DTSTART>{dt_agora}</DTSTART>\n<DTEND>{dt_agora}</DTEND>\n"

        # 4. As transações (Corrigidas)
        for i, t in enumerate(transacoes):
            ofx += "<STMTTRN>\n"
            ofx += "<TRNTYPE>OTHER</TRNTYPE>\n"
            ofx += f"<DTPOSTED>{datetime.now().strftime('%Y%m%d')}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n"
            ofx += f"<FITID>{dt_agora}{i}</FITID>\n" # ID único para cada linha
            ofx += f"<CHECKNUM>{i}</CHECKNUM>\n"
            ofx += f"<MEMO>{t['d'][:32]}</MEMO>\n" # Descrição curta
            ofx += "</STMTTRN>\n"

        # 5. Fechamento de tudo
        ofx += "</BANKTRANLIST>\n<LEDGERBAL>\n<BALAMT>0.00</BALAMT>\n<DTASOF>"+datetime.now().strftime('%Y%m%d')+"</DTASOF>\n</LEDGERBAL>\n"
        ofx += "</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        st.download_button(
            label="📥 Baixar Arquivo OFX para o Domínio",
            data=ofx,
            file_name=f"extrato_{banco_selecionado.lower()}.ofx",
            mime="text/plain" # Usar text/plain às vezes ajuda na compatibilidade
        )
