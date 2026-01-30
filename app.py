import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Conversor OFX", page_icon="🏦")

# Estilo para o botão pequeno e elegante
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 5px 15px;
        font-size: 14px;
        font-weight: 500;
        transition: 0.2s;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #218838;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Conversor de Extratos")

# --- NOVO: Manual de Ajuda ---
with st.expander("❓ Como usar este conversor?"):
    st.write("""
    1. **Escolha o Banco:** Selecione o nome do seu banco na lista abaixo.
    2. **Suba o Arquivo:** Clique em 'Suba o PDF' e escolha o arquivo do seu extrato.
    3. **Confira:** O programa vai ler o arquivo e dizer quantos itens encontrou.
    4. **Baixe:** Clique no botão verde para salvar o arquivo OFX no seu computador.
    """)
    st.info("Dica: Se o seu banco não estiver na lista, escolha a opção 'Outro'.")

# Lista de bancos
lista_de_bancos = [
    "Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", 
    "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"
]

banco_escolhido = st.selectbox("Banco:", lista_de_bancos)
arquivo_pdf = st.file_uploader("Suba o PDF:", type="pdf")

if arquivo_pdf is not None:
    transacoes = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    if tem_data and tem_valor:
                        # Limpeza do valor para o padrão OFX
                        v = tem_valor.group(1).replace('.', '').replace(',', '.')
                        d = linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                        transacoes.append({'valor': v, 'desc': d})

    if transacoes:
        st.write(f"Encontrado: {len(transacoes)} itens.")
        
        # Gerador do conteúdo OFX
        data_ofx = datetime.now().strftime('%Y%m%d')
        ofx_body = f"OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>"
        for t in transacoes:
            ofx_body += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_ofx}</DTPOSTED><TRNAMT>{t['valor']}</TRNAMT><MEMO>{t['desc'][:32]}</MEMO></STMTTRN>"
        ofx_body += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        st.download_button(
            label="Baixar OFX",
            data=ofx_body,
            file_name=f"extrato_{banco_escolhido.lower()}.ofx"
        )
    else:
        st.warning("Não encontrei transações. O arquivo pode ser uma imagem.")

st.divider()
# Regras personalizadas
st.caption("Regra: Para o fornecedor o crédito é positivo e o débito negativo; para o cliente o crédito é negativo e o débito positivo.")
