import streamlit as st
import pandas as pd
import pdfplumber
import re
import io
from datetime import datetime

st.set_page_config(page_title="Central de Extratos do Gê", page_icon="🏦")

# Estilo dos botões
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

tipo_robo = st.radio(
    "Qual robô você quer usar agora?",
    ["Robô OFX (Para Bancos)", "Robô Excel (Débito/Crédito)"],
    horizontal=True
)

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
                        # Converte para número puro
                        v_num = float(valor_str.replace('.', '').replace(',', '.'))
                        desc = linha.replace(data, '').replace(valor_str, '').strip()
                        
                        # Lógica de separação para o Excel
                        debito = abs(v_num) if v_num < 0 else 0
                        credito = v_num if v_num > 0 else 0
                        
                        transacoes.append({
                            "Data": data,
                            "Historico": desc[:50],
                            "Documento": "0",
                            "Valor_Original": v_num,
                            "Debito": debito,
                            "Credito": credito
                        })

    if transacoes:
        st.success(f"Encontrei {len(transacoes)} lançamentos!")

        if tipo_robo == "Robô OFX (Para Bancos)":
            data_ofx = datetime.now().strftime('%Y%m%d')
            ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>"
            for t in transacoes:
                ofx += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_ofx}</DTPOSTED><TRNAMT>{t['Valor_Original']}</TRNAMT><MEMO>{t['Historico']}</MEMO></STMTTRN>"
            ofx += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
            st.download_button("📥 Baixar Arquivo OFX", ofx, f"extrato_{banco.lower()}.ofx")

        else:
            # Organiza as colunas exatamente como no modelo 
            df = pd.DataFrame(transacoes)[["Data", "Historico", "Documento", "Debito", "Credito"]]
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            
            st.write("### Prévia da Planilha:")
            st.dataframe(df.head())
            
            st.download_button("📥 Baixar Excel (Débito/Crédito)", output.getvalue(), f"modelo_sistema_{banco.lower()}.xlsx")
    else:
        st.error("Nenhum dado encontrado.")

st.divider()
st.caption("Regra: Débito (Saída) e Crédito (Entrada) separados em colunas.")
