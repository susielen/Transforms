import streamlit as st
import pdfplumber
import re
import time
from datetime import datetime

st.set_page_config(page_title="OFX Transforms", page_icon="🤖")

st.title("🤖 OFX Transforms (Filtro Inteligente)")

banco_selecionado = st.selectbox("Banco:", ["Santander", "Sicoob", "Itaú", "BB", "Caixa", "Inter", "Nubank", "Outro"])
arquivo_pdf = st.file_uploader("Arraste seu PDF Consolidado aqui", type="pdf")

if arquivo_pdf:
    transacoes = []
    
    # Palavras que indicam que a linha NÃO é uma transação (lixo do extrato)
    palavras_proibidas = ["SALDO", "RESUMO", "TOTAL", "DEMONSTRATIVO", "TARIFAS PAGAS"]
    # Palavras que DEVEM ser mantidas (exceções)
    palavras_permitidas = ["APLICAÇÃO", "RESGATE", "RENDIMENTO", "RENDIMENTOS"]

    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                for linha in texto.split('\n'):
                    linha_up = linha.upper()
                    
                    # 1. Verifica se a linha tem palavra proibida, mas ignora se tiver uma permitida
                    deve_pular = False
                    for prob in palavras_proibidas:
                        if prob in linha_up:
                            deve_pular = True
                            # Se na mesma linha proibida tiver uma permitida, a gente salva!
                            for perm in palavras_permitidas:
                                if perm in linha_up:
                                    deve_pular = False
                                    break
                            break
                    
                    if deve_pular:
                        continue

                    # 2. Busca Data e Valor
                    m_data = re.search(r'(\d{2}/\d{2})', linha)
                    m_valor = re.search(r'(-?\s?\d?\.?\d+,\d{2}\s?-?|D|C)', linha)
                    
                    if m_data and m_valor:
                        valor_str = m_valor.group(0).strip()
                        # Lógica do Sinal (D ou - é negativo)
                        e_negativo = '-' in valor_str or 'D' in linha_up or 'DEBITO' in linha_up
                        
                        apenas_numeros = re.sub(r'[^\d,]', '', valor_str)
                        valor_final = apenas_numeros.replace(',', '.')
                        
                        if e_negativo:
                            valor_final = f"-{valor_final}"
                        
                        desc = linha.replace(m_data.group(0), '').replace(m_valor.group(0), '').strip()
                        transacoes.append({'v': valor_final, 'd': desc[:32], 'data': m_data.group(0)})

    if transacoes:
        st.success(f"✅ Concluído! {len(transacoes)} itens encontrados (incluindo aplicações e resgates).")

        # ESTRUTURA OFX (IDÊNTICO AO BANCO)
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
            
            ofx += "<STMTTRN>\n"
            ofx += "<TRNTYPE>OTHER</TRNTYPE>\n"
            ofx += f"<DTPOSTED>{dt_posted}</DTPOSTED>\n"
            ofx += f"<TRNAMT>{t['v']}</TRNAMT>\n"
            ofx += f"<FITID>{dt_agora}{i}</FITID>\n"
            ofx += f"<MEMO>{t['d']}</MEMO>\n"
            ofx += "</STMTTRN>\n"

        ofx += "</BANKTRANLIST>\n</STMTRS>\n</STMTTRNRS>\n</BANKMSGSRSV1>\n</OFX>"

        st.download_button(label="📥 Baixar OFX Consolidado", data=ofx, file_name="extrato_limpo.ofx")
