import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

st.title("🤖 OFX Transforms (Organizador)")

# Lista de meses para o nome do arquivo
MESES = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Marco", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro"
}

banco_selecionado = st.selectbox("Banco:", ["Santander", "Sicoob", "Itau", "BB", "Caixa", "Inter", "Nubank", "Outro"])
arquivo_pdf = st.file_uploader("Arraste seu PDF aqui", type="pdf")

if arquivo_pdf:
    transacoes = []
    palavras_proibidas = ["SALDO", "RESUMO", "TOTAL", "DEMONSTRATIVO"]
    palavras_permitidas = ["APLICACAO", "RESGATE", "RENDIMENTO"]

    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    linha_up = linha.upper()
                    
                    deve_pular = False
                    for prob in palavras_proibidas:
                        if prob in linha_up:
                            deve_pular = True
                            for perm in palavras_permitidas:
                                if perm in linha_up:
                                    deve_pular = False
                                    break
                            break
                    
                    if deve_pular: continue

                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\s?\d?\.?\d+,\d{2}\s?-?|D|C)', linha)
                    
                    if m_data and m_valor:
                        valor_str = m_valor.group(0).strip()
                        e_negativo = '-' in valor_str or 'D' in linha_up
                        apenas_numeros = re.sub(r'[^\d,]', '', valor_str)
                        valor_final = apenas_numeros.replace(',', '.')
                        if e_negativo: valor_final = f"-{valor_final}"
                        
                        desc = linha.replace(m_data.group(0), '').replace(valor_str, '').strip()
                        transacoes.append({'v': valor_final, 'd': desc[:32], 'data': m_data.group(0)})

    if transacoes:
        # Descobre o mês da primeira transação para nomear o arquivo
        mes_num = transacoes[0]['data'][3:5]
        nome_mes = MESES.get(mes_num, "Mes_Desconhecido")
        nome_final_arquivo = f"Extrato_{banco_selecionado}_{nome_mes}.ofx"

        st.success(f"✅ {len(transacoes)} itens encontrados para o mês de {nome_mes}!")
        
        # Mostra uma prévia das primeiras 5 linhas para conferência
        with st.expander("Ver prévia das transações"):
            st.table(transacoes[:10])

        # MONTAGEM DO OFX
        dt_agora = datetime.now().strftime('%Y%m%d%H%M%S')
        data_ofx = datetime.now().strftime('%Y%m%d')
        
        ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n"
        ofx += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>\n"
        ofx += f"<DTSERVER>{dt_agora}</DTSERVER>\n<LANGUAGE>POR</LANGUAGE>\n</SONRS>\n</SIGNONMSGSRSV1>\n"
        ofx += "<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL</CURDEF>\n"
        ofx += "<BANKACCTFROM>\n<BANKID>9999</BANKID>\n<ACCTID>000000</ACCTID>\n<ACCTTYPE>CHECKING</ACCTTYPE>\n</BANKACCTFROM>\n"
        ofx += "<BANKTRANLIST>\n"
        
        for i, t in enumerate(transacoes):
            ano = datetime.now().year
            dt_posted = f"{ano}{t['data'][3:5]}{t['data'][0:2]}120000"
            ofx += f"<STMTTRN>\n<TRNTYPE>OTHER</TRNTYPE>\n<DTPOSTED>{dt_posted}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n<FITID>{dt_agora}{i}</FITID>\n<MEMO>{t['d']}</MEMO>\n</STMTTRN>\n"

        ofx += "</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        st.download_button(
            label=f"📥 Baixar {nome_final_arquivo}", 
            data=ofx, 
            file_name=nome_final_arquivo
        )
