import streamlit as st
import pandas as pd
import re  # Para verificar padrões como E014* e V094*

# Função para calcular os totais
def calcular_totais(df_csv, df_excel):
    totais_materiais = {}
    contagem_e014 = 0
    contagem_v094 = 0
    unidades_epc_23004_01 = 0  # Inicializar

    for _, row_csv in df_csv.iterrows():
        codigo_montagem = row_csv['Codigo_Montagem']
        contagem = row_csv['Contagem']

        if re.match(r'^E014.*', str(codigo_montagem)):
            contagem_e014 += contagem
        if re.match(r'^V094.*', str(codigo_montagem)):
            contagem_v094 += contagem

        linha_excel = df_excel[df_excel['CODIGO INSTÂNCIA'] == codigo_montagem]

        if not linha_excel.empty:
            linha = linha_excel.iloc[0]
            for i in range(1, 16):
                cod_col = f'CODIGO MONTAGEM {str(i).zfill(2)}'
                qtd_col = f'QUANTIDADE MONTAGEM {str(i).zfill(2)}'

                if pd.notna(linha[cod_col]) and pd.notna(linha[qtd_col]):
                    codigo_material = linha[cod_col]
                    qtd_por_unidade = linha[qtd_col]

                    try:
                        qtd_por_unidade = float(qtd_por_unidade)
                        total = qtd_por_unidade * contagem
                        if codigo_material in totais_materiais:
                            totais_materiais[codigo_material] += total
                        else:
                            totais_materiais[codigo_material] = total
                    except (ValueError, TypeError):
                        continue

    contagem_total_014_094 = contagem_e014 + contagem_v094

    if contagem_total_014_094 >= 25:
        unidades_epc_23004_01 = contagem_total_014_094 // 25
        if 'EPC-23004-01' in totais_materiais:
            totais_materiais['EPC-23004-01'] += unidades_epc_23004_01
        else:
            totais_materiais['EPC-23004-01'] = unidades_epc_23004_01

    return totais_materiais, unidades_epc_23004_01, contagem_total_014_094

# Função para validar códigos
def validar_codigos(df_csv, df_excel):
    codigos_csv = set(df_csv['Codigo_Montagem'])
    codigos_excel = set(df_excel['CODIGO INSTÂNCIA'])

    codigos_nao_encontrados = codigos_csv - codigos_excel
    return list(codigos_nao_encontrados)

# Interface do Streamlit
st.title("Sistema de Validação e Contagem de Materiais")

# Upload dos arquivos
st.header("Carregar Arquivos")
csv_file = st.file_uploader("Carregar arquivo DETALHES TIPICOS - VIA DE CABOS - (csv)", type=['csv'])
excel_file = st.file_uploader("Carregar Banco de Dados - (xlsx)", type=['xlsx'])

if csv_file and excel_file:
    # Ler os arquivos
    df_csv = pd.read_csv(csv_file)
    df_excel = pd.read_excel(excel_file)

    # Converter 'Contagem' para numérico, tratando erros
    df_csv['Contagem'] = pd.to_numeric(df_csv['Contagem'], errors='coerce').fillna(0)
    df_csv = df_csv[df_csv['Contagem'] > 0]
    df_csv = df_csv[df_csv['Codigo_Montagem'].notna()]

    # Exibir os dados carregados
    st.subheader("Dados do CSV")
    st.write(df_csv)

    st.subheader("Dados do Excel (primeiras 5 linhas)")
    st.write(df_excel.head())

    # Validação dos códigos
    st.subheader("Validação dos Códigos de Montagem")
    codigos_nao_encontrados = validar_codigos(df_csv, df_excel)

    if codigos_nao_encontrados:
        df_nao_encontrados = pd.DataFrame(codigos_nao_encontrados, columns=['Códigos Não Encontrados no Excel'])
        st.warning("Os seguintes códigos do CSV não foram encontrados no Excel:")
        st.write(df_nao_encontrados)

        # Opção para baixar os códigos não encontrados
        csv_nao_encontrados = df_nao_encontrados.to_csv(index=False)
        st.download_button(
            label="Baixar Códigos Não Encontrados como CSV",
            data=csv_nao_encontrados,
            file_name="codigos_nao_encontrados.csv",
            mime="text/csv"
        )
    else:
        st.success("Todos os códigos do CSV foram encontrados no Excel!")

    # Calcular os totais
    totais, qtd_epc_adicionado, soma_014_094 = calcular_totais(df_csv, df_excel)

    # Converter os totais em DataFrame para exibição
    df_totais = pd.DataFrame(list(totais.items()), columns=['Código Material', 'Quantidade Total'])
    df_totais['Quantidade Total'] = df_totais['Quantidade Total'].round(2)
    df_totais = df_totais.sort_values('Código Material')

    # Exibir o resumo geral
    st.subheader("Resumo Geral de Materiais")
    st.write(df_totais)

    # Mostrar quantidade de EPC-23004-01 adicionada
    if qtd_epc_adicionado > 0:
        st.info(f"✔ Foram adicionadas **{qtd_epc_adicionado} unidades** do material **EPC-23004-01**, com base na soma total de **{soma_014_094} unidades** dos códigos `E014*` e `V094*`.")
    else:
        st.info("❌ Nenhuma unidade de EPC-23004-01 foi adicionada, pois a soma das contagens de `E014*` e `V094*` foi menor que 25.")

    # Opção para baixar o resultado como CSV
    csv_totais = df_totais.to_csv(index=False)
    st.download_button(
        label="Baixar Resumo como CSV",
        data=csv_totais,
        file_name="resumo_materiais.csv",
        mime="text/csv"
    )

else:
    st.warning("Por favor, carregue ambos os arquivos (CSV e Excel) para prosseguir.")
##funcionando até aqui