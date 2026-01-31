import streamlit as st
import pdfplumber
import re
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

st.title("🤖 OFX Transforms Final")

# --- 1. ABA SUSPENSA COM INSTRUÇÕES ---
with st.expander("📖 INSTRUÇÕES:"):
    st.info("Siga a ordem abaixo para gerar seu arquivo corretamente:")
    st.write("""
        1. **Selecione o Banco:** Escolha o banco na lista.
        2. **Selecione o Ano:** Selecione o ano desejado no seletor.
        3. **Suba o PDF:** Arraste o arquivo para o campo de upload e o robô irá transformar seu arquivo em OFX.
        
        *O robô ignora saldos automáticos, mas mantém aplicações e resgates.*
    """)

# --- 2. SELETORES (BANCO E ANO) ---
col1, col2 = st.columns(2)
with col1:
    banco_sel = st.selectbox("1º Passo: Selecione o Banco", ["Santander", "Sicoob", "Itau", "BB", "Caixa", "Inter", "Nubank", "Outro"])
with col2:
    # Ordem dos anos atualizada conforme solicitado
    ano_extrato = st.selectbox("2º Passo: Selecione o Ano", ["2024", "2025", "2026", "2027", "2028", "2029", "2030"], index=1) # index=1 deixa o 2025 pré-selecionado

# --- 3. UPLOAD DO ARQUIVO ---
arquivo_pdf = st.file_uploader("3º Passo: Arraste seu PDF aqui", type="pdf")

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
                        
                        if e_negativo:
                            valor_final = f"-{valor_final}"
                        
                        desc = linha.replace(m_data.group(0), '').replace(m_valor.group(0), '').strip()
                        transacoes.append({'v': valor_final, 'd': desc[:32], 'data': m_data.group(0)})

    if transacoes:
        st.success(f"✅ Robô concluiu a leitura de {len(transacoes)} itens!")
        
        with st.expander("🔍 Conferir itens capturados"):
            st.table(transacoes)

        mes_num = transacoes[0]['data'][3:5]
        meses_nome = {"01":"Janeiro","02":"Fevereiro","03":"Marco","04":"Abril","05":"Maio","06":"Junho",
                      "07":"Julho","08":"Agosto","09":"Setembro","10":"Outubro","11":"Novembro","12":"Dezembro"}
        nome_mes = meses_nome.get(mes_num, "Mes")
        nome_arquivo = f"Extrato_{banco_sel}_{nome_mes}_{ano_extrato}.ofx"

        dt_agora = datetime.now().strftime('%Y%m%d%H%M%S')
        ofx = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n"
        ofx += "<OFX>\n<SIGNONMSGSRSV1>\n<SONRS>\n<STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>\n"
        ofx += f"<DTSERVER>{dt_agora}</DTSERVER>\n<LANGUAGE>POR</LANGUAGE>\n</SONRS>\n</SIGNONMSGSRSV1>\n"
        ofx += "<BANKMSGSRSV1>\n<STMTTRNRS>\n<STMTRS>\n<CURDEF>BRL</CURDEF>\n"
        ofx += "<BANKACCTFROM>\n<BANKID>9999</BANKID>\n<ACCTID>000000</ACCTID>\n<ACCTTYPE>CHECKING</ACCTTYPE>\n</BANKACCTFROM>\n<BANKTRANLIST>\n"
        
        for i, t in enumerate(transacoes):
            dt_posted = f"{ano_extrato}{t['data'][3:5]}{t['data'][0:2]}120000"
            ofx += f"<STMTTRN>\n<TRNTYPE>OTHER</TRNTYPE>\n<DTPOSTED>{dt_posted}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n<FITID>{dt_agora}{i}</FITID>\n<MEMO>{t['d']}</MEMO>\n</STMTTRN>\n"

        ofx += "</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        st.download_button(label=f"📥 Baixar Arquivo: {nome_arquivo}", data=ofx, file_name=nome_arquivo)
