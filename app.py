import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime

st.set_page_config(page_title="Conversor Multi-Bancos", page_icon="🏦")

st.title("🏦 Conversor de Extratos")

# 1. Aqui é onde você adiciona novos nomes na lista!
lista_de_bancos = [
    "Santander", "Sicoob", "Itaú", "Banco do Brasil", "Caixa", 
    "Inter", "Mercado Pago", "Sicredi", "XP", "Nubank", 
    "OUTRO BANCO (Tentar todos)" 
]

banco_escolhido = st.selectbox("Selecione o seu banco:", lista_de_bancos)

arquivo_pdf = st.file_uploader(f"Suba o PDF aqui", type="pdf")

if arquivo_pdf is not None:
    transacoes = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    # A mágica que caça data e valor (funciona para quase todos)
                    tem_data = re.search(r'(\d{2}/\d{2})', linha)
                    tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', linha)
                    
                    if tem_data and tem_valor:
                        # Arruma o valor para o formato que o banco gosta
                        v = tem_valor.group(1).replace('.', '').replace(',', '.')
                        d = linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                        transacoes.append({'valor': v, 'desc': d})

    if transacoes:
        st.success(f"Encontrei {len(transacoes)} lançamentos! 🥳")
        st.balloons()
        
        # Montando o arquivo OFX
        data_ofx = datetime.now().strftime('%Y%m%d')
        ofx_body = f"""OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nENCODING:USASCII\nCHARSET:1252\n<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>"""
        
        for t in transacoes:
            ofx_body += f"<STMTTRN><TRNTYPE>OTHER</TRNTYPE><DTPOSTED>{data_ofx}</DTPOSTED><TRNAMT>{t['valor']}</TRNAMT><MEMO>{t['desc'][:32]}</MEMO></STMTTRN>"
        
        ofx_body += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        st.download_button(
            label=f"📥 Baixar OFX ({banco_escolhido})",
            data=ofx_body,
            file_name=f"extrato_{banco_escolhido.lower()}.ofx"
        )
    else:
        st.error("Não achei nada... Verifique se o PDF não é uma foto!")

# Nosso combinado sobre as cores das trocas (crédito/débito)
st.divider()
st.info("💡 Lembrete de 5 anos: Para o fornecedor, o crédito é positivo e o débito negativo; e para o cliente o crédito é negativo e o débito positivo.")
