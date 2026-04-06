import streamlit as st
import pdfplumber
import pandas as pd

st.set_page_config(page_title="Calculadora de Ponto - Hector", page_icon="⏱️")

st.title("⏱️ Calculadora de Ponto")
st.markdown("Arraste seu arquivo PDF abaixo para calcular o saldo.")

# Upload do arquivo
arquivo_pdf = st.file_uploader("Escolha o PDF do ponto", type="pdf")

def para_min(texto):
    try:
        # Tenta converter o formato HH:MM para minutos totais
        h, mt = map(int, texto.split(':'))
        return h * 60 + mt
    except:
        return 0

if arquivo_pdf:
    dados_finais = []
    with pdfplumber.open(arquivo_pdf) as pdf:
        # Extrai a tabela da primeira página
        tela = pdf.pages[0].extract_table()
        
        if tela:
            for linha in tela[1:]:
                # linha[0] = Data, linha[1] = Marcações, linha[2] = Motivo/Justificativa
                data_raw = str(linha[0]).strip().replace('\n', ' ')
                marcacoes = str(linha[1]) if linha[1] else ""
                motivo = str(linha[2]) if linha[2] else ""
                m = marcacoes.split()
                
                # Só processa se houver entrada/saída (2 batidas) ou dia completo (4 batidas)
                if len(m) not in [2, 4]: continue

                min_trabalhados = 0
                if len(m) == 4:
                    # (Saída Final - Entrada Inicial) - (Retorno Almoço - Saída Almoço)
                    min_trabalhados = (para_min(m[3]) - para_min(m[0])) - (para_min(m[2]) - para_min(m[1]))
                elif len(m) == 2:
                    # Regra para dias abonados ou meio período
                    if "Abonadas" in motivo:
                        min_trabalhados = 480 # Ajustado para 8h redondas
                    else:
                        min_trabalhados = para_min(m[1]) - para_min(m[0])

                # Regra de tolerância de 15 minutos (simétrica)
                # Horas extras: contabilizadas apenas se trabalhou MAIS de 8h15 (saldo > +15min)
                # Horas negativas: contabilizadas apenas se trabalhou MENOS de 7h45 (saldo < -15min)
                saldo_dia = min_trabalhados - 480
                if -15 <= saldo_dia <= 15:
                    saldo_dia = 0
                dados_finais.append({"Data": data_raw[:10], "Saldo": saldo_dia})

            # Cria o DataFrame e calcula o total
            df = pd.DataFrame(dados_finais)
            
            total_min = df['Saldo'].sum()
            
            h, m = divmod(abs(int(total_min)), 60)
            sinal = "+" if total_min >= 0 else "-"

            # Exibição dos resultados
            st.divider()
            st.subheader(f"RELATÓRIO FINAL")
            st.metric("SALDO TOTAL", f"{sinal}{h:02d}:{m:02d}")
            
            # Formata a tabela para exibição
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Não foi possível ler a tabela deste PDF. Verifique o formato.")