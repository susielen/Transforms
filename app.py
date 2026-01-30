import streamlit as st
import pandas as pd
import pdfplumber
import re
from datetime import datetime

st.set_page_config(page_title="Conversor Universal OFX", page_icon="🌍")

st.title("🌍 Conversor Universal de PDF para OFX")
st.write("Este robozinho tenta ler extratos de qualquer banco!")

arquivo_pdf = st.file_uploader("Arraste o PDF de qualquer banco aqui", type="pdf")

if arquivo_pdf is not None:
    todas_as_linhas = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            # O 'extract_words' lê palavra por palavra, não importa onde elas estejam
            palavras = pagina.extract_words()
            
            # Vamos agrupar as palavras que estão na mesma linha (mesmo 'top')
            linhas_agrupadas = {}
            for p in palavras:
                y = p['top']
                # Arredondamos o 'top' para agrupar palavras que estão na mesma altura
                y_key = round(y)
                if y_key not in linhas_agrupadas:
                    linhas_agrupadas[y_key] = []
                linhas_agrupadas[y_key].append(p['text'])
            
            for k in sorted(linhas_agrupadas.keys()):
                todas_as_linhas.append(linhas_agrupadas[k])

    if todas_as_linhas:
        st.success("Consegui ler o papel! Agora vou procurar o dinheiro e as datas... 🔍")
        
        # Cabeçalho do OFX
        ofx_final = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS><CURDEF>BRL</CURDEF><BANKTRANLIST>
"""
        
        contagem = 0
        for linha in todas_as_linhas:
            texto_linha = " ".join(linha)
            
            # 🕵️ PROCURA POR DATAS (ex: 10/01 ou 10/01/2026)
            tem_data = re.search(r'(\d{2}/\d{2}(/\d{2,4})?)', texto_linha)
            
            # 🕵️ PROCURA POR VALORES (ex: 1.200,50 ou 50,00)
            # Ele busca números que tenham uma vírgula antes dos últimos dois dígitos
            tem_valor = re.search(r'(-?\d?\.?\d+,\d{2})', texto_linha)

            if tem_data and tem_valor:
                data_limpa = datetime.now().strftime('%Y%m%d') # Usa hoje se não achar o ano
                valor_ofx = tem_valor.group(1).replace('.', '').replace(',', '.')
                descricao = texto_linha.replace(tem_data.group(1), '').replace(tem_valor.group(1), '').strip()
                
                ofx_final += f"""<STMTTRN>
<TRNTYPE>OTHER</TRNTYPE>
<DTPOSTED>{data_hoje}</DTPOSTED>
<TRNAMT>{valor_ofx}</TRNAMT>
<MEMO>{descricao[:32]}</MEMO>
</STMTTRN>
"""
                contagem += 1

        ofx_final += "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"
        
        if contagem > 0:
            st.write(f"Encontrei **{contagem}** trocas de dinheiro!")
            st.download_button("📥 Baixar meu arquivo OFX", ofx_final, "extrato_universal.ofx")
        else:
            st.warning("Li o arquivo, mas não consegui identificar o que é data e o que é valor. 🧐")
            
        st.info("Lembrete: Para você, o Crédito é negativo (-) e o Débito é positivo (+).")
