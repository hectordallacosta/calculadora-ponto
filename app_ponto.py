import streamlit as st
import pdfplumber
import pandas as pd

st.set_page_config(page_title="Calculadora de Ponto - Hector", page_icon="⏱️")

st.title("⏱️ Calculadora de Ponto")
st.markdown("Arraste seu arquivo PDF abaixo para calcular o saldo.")

arquivo_pdf = st.file_uploader("Escolha o PDF do ponto", type="pdf")

def para_min(texto):
    try:
        h, mt = map(int, texto.split(':'))
        return h * 60 + mt
    except:
        return 0

def min_para_hhmm(total):
    h, m = divmod(total, 60)
    return f"{h:02d}:{m:02d}"

if arquivo_pdf:
    with pdfplumber.open(arquivo_pdf) as pdf:
        tela = pdf.pages[0].extract_table()

        if tela:
            # --- SEÇÃO 1: Horário mínimo de saída ---
            st.subheader("🕐 Qual horário posso ir embora?")

            tres_batidas = None
            for linha in tela[1:]:
                marcacoes = str(linha[1]) if linha[1] else ""
                m = marcacoes.split()
                if len(m) == 3:
                    tres_batidas = m
                    break

            if tres_batidas:
                entrada, saida_almoco, retorno_almoco = tres_batidas

                min_entrada = para_min(entrada)
                min_saida_almoco = para_min(saida_almoco)
                min_retorno_almoco = para_min(retorno_almoco)

                min_manha = min_saida_almoco - min_entrada

                saida_min   = min_retorno_almoco + (465 - min_manha)
                saida_8h    = min_retorno_almoco + (480 - min_manha)
                saida_extra = min_retorno_almoco + (495 - min_manha)

                st.caption(f"Batidas detectadas: **{entrada}** | **{saida_almoco}** | **{retorno_almoco}**")
                st.divider()
                c1, c2, c3 = st.columns(3)
                c1.metric("Saída sem desconto (7h45)", min_para_hhmm(saida_min), delta="mínimo")
                c2.metric("Saída para 8h exatas", min_para_hhmm(saida_8h))
                c3.metric("Saída para hora extra (8h15)", min_para_hhmm(saida_extra), delta="+15min extras")
            else:
                st.warning("horario faltante")

            st.divider()

            # --- SEÇÃO 2: Relatório completo ---
            dados_finais = []
            for linha in tela[1:]:
                data_raw = str(linha[0]).strip().replace('\n', ' ')
                marcacoes = str(linha[1]) if linha[1] else ""
                motivo = str(linha[2]) if linha[2] else ""
                m = marcacoes.split()

                if len(m) not in [2, 4]:
                    continue

                if len(m) == 4:
                    min_trabalhados = (para_min(m[3]) - para_min(m[0])) - (para_min(m[2]) - para_min(m[1]))
                else:
                    min_trabalhados = 480 if "Abonadas" in motivo else para_min(m[1]) - para_min(m[0])

                saldo_dia = min_trabalhados - 480
                if -15 <= saldo_dia <= 15:
                    saldo_dia = 0
                dados_finais.append({"Data": data_raw[:10], "Saldo": saldo_dia})

            df = pd.DataFrame(dados_finais)
            total_min = df['Saldo'].sum()
            h, m = divmod(abs(int(total_min)), 60)
            sinal = "+" if total_min >= 0 else "-"

            st.subheader("RELATÓRIO FINAL")
            st.metric("SALDO TOTAL", f"{sinal}{h:02d}:{m:02d}")
            st.dataframe(df, use_container_width=True)

        else:
            st.error("Não foi possível ler a tabela deste PDF. Verifique o formato.")
