import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

# Interface bonita
st.markdown("""
    <style>
    div.stDownloadButton > button:first-child {
        background-color: #28a745; color: white; border-radius: 4px; border: none; padding: 6px 16px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 OFX Transforms (Estilo OFX Fácil)")

banco_selecionado = st.selectbox("Banco:", ["Santander", "Sicoob", "Itaú", "BB", "Caixa", "Inter", "Nubank", "Outro"])
arquivo_pdf = st.file_uploader("Arraste seu PDF aqui", type="pdf")

if arquivo_pdf:
    transacoes = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    # 1. Procura a data (DD/MM)
                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    # 2. Procura o valor (pode ter sinal na frente ou atrás)
                    m_valor = re.search(r'(-?\s?\d?\.?\d+,\d{2}\s?-?|D|C)', linha)
                    
                    if m_data and m_valor:
                        # Limpeza do Valor
                        valor_str = m_valor.group(0).strip()
                        
                        # Se tiver um '-' ou 'D' (débito), vira negativo
                        e_negativo = '-' in valor_str or 'D' in linha.upper()
                        
                        # Limpa tudo que não é número ou vírgula
                        apenas_numeros = re.sub(r'[^\d,]', '', valor_str)
                        valor_final = apenas_numeros.replace(',', '.')
                        
                        if e_negativo:
                            valor_final = f"-{valor_final}"
                        
                        # Descrição (pega o que sobrou da linha)
                        desc = linha.replace(m_data.group(0), '').replace(valor_str, '').strip()
                        transacoes.append({'v': valor_final, 'd': desc[:32], 'data': m_data.group(0)})

    if transacoes:
        st.success(f"✅ {len(transacoes)} transações prontas!")

        # MONTAGEM DO ARQUIVO (IDÊNTICO AO OFX FÁCIL)
        dt_agora = datetime.now().strftime('%Y%m%d%H%M%S')
        data_ofx = datetime.now().strftime('%Y%m%d')
        
        # Cabeçalho Obrigatório Domínio
        ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n"
        ofx += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>\n"
        ofx += f"<DTSERVER>{dt_agora}</DTSERVER>\n<LANGUAGE>POR</LANGUAGE>\n</SONRS>\n</SIGNONMSGSRSV1>\n"
        ofx += "<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL</CURDEF>\n"
        ofx += "<BANKACCTFROM>\n<BANKID>9999</BANKID>\n<ACCTID>000000</ACCTID>\n<ACCTTYPE>CHECKING</ACCTTYPE>\n</BANKACCTFROM>\n"
        ofx += "<BANKTRANLIST>\n"
        ofx += f"<DTSTART>{data_ofx}</DTSTART>\n<DTEND>{data_ofx}</DTEND>\n"

        for i, t in enumerate(transacoes):
            # Ajuste da data: Ano atual + data do PDF
            ano_atual = datetime.now().year
            data_formatada = f"{ano_atual}{t['data'][3:5]}{t['data'][0:2]}120000"
            
            ofx += "<STMTTRN>\n"
            ofx += "<TRNTYPE>OTHER</TRNTYPE>\n"
            ofx += f"<DTPOSTED>{data_formatada}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n"
            ofx += f"<FITID>{dt_agora}{i}</FITID>\n"
            ofx += f"<CHECKNUM>{i}</CHECKNUM>\n"
            ofx += f"<MEMO>{t['d']}</MEMO>\n"
            ofx += "</STMTTRN>\n"

        ofx += "</BANKTRANLIST>\n<LEDGERBAL>\n<BALAMT>0.00</BALAMT>\n<DTASOF>"+data_ofx+"</DTASOF>\n</LEDGERBAL>\n"
        ofx += "</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        st.download_button(label="📥 Baixar OFX para Domínio", data=ofx, file_name="extrato_dominio.ofx", mime="text/plain")
