import streamlit as st
import pandas as pd
import pdfplumber
import re
import io
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Central de Extratos do Gê", page_icon="🏦")

# Estilo para os botões ficarem verdes e elegantes
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
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏦 Central de Extratos")

# 1. Escolha do Robô
tipo_robo = st.radio(
    "Qual robô você quer usar agora?",
    ["Robô OFX (Para Bancos)", "Robô Excel (Para o Sistema)"],
    horizontal=True
)

# 2. Seleção do Banco
lista_bancos = ["Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", "Outro"]
banco = st.selectbox("Selecione o Banco:", lista_bancos)

arquivo_pdf = st.file_uploader("Suba o PDF aqui:", type="pdf")

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
                        data = tem_data.group(1)
                        valor_str = tem_valor.group(1)
                        valor_num = float(valor_str.replace('.', '').replace(',', '.'))
                        
                        # Regra do Cliente: Inverte o sinal para o Excel
                        valor_ajustado = valor_num * -1
                        desc = linha.replace(data, '').replace(valor_str, '').strip()
                        
                        transacoes.append({
                            "Data": data,
                            "Historico": desc[:50],
                            "Documento": "0",
                            "Valor": valor_num, # Original para OFX
                            "Valor_Ajustado": valor_ajustado # Invertido para Excel
                        })

    if transacoes:
        st.success(f"Encontrei {len(transacoes)} lançamentos!")

        if tipo_robo == "Robô OFX (Para Bancos)":
            # Lógica do Robô 1: Gerar OFX
            data_ofx = datetime.now().strftime('%Y%m%d')
            ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>"
            for t in transacoes:
                ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_ofx}</DTPOSTED><TRNAMT>{t['Valor']}</TRNAMT><MEMO>{t['Historico']}</MEMO></STMTTRN>"
            ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
            
            st.download_button("📥 Baixar Arquivo OFX", ofx, f"extrato_{banco.lower()}.ofx")

        else:
            # Lógica do Robô 2: Gerar Excel para Sistema
            df = pd.DataFrame(transacoes)[["Data", "Historico", "Documento", "Valor_Ajustado"]]
            df.columns = ["Data", "Historico", "Documento", "Valor"]
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.download_button("📥 Baixar Planilha Excel", output.getvalue(), f"extrato_sistema_{banco.lower()}.xlsx")
    else:
        st.error("Não encontrei dados. Verifique o arquivo.")

st.divider()
st.caption("Regra: Para o cliente o crédito é negativo e o débito positivo.")
