import math

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src.data_loader import load_data

st.set_page_config(
    page_title="Recarga de veículos elétricos",
    layout="wide",
)

st.title("Avaliação de correlação entre variáveis quantitativas do EV Charging Dataset")

df = load_data()

# Variáveis quantitativas do estudo (mesma lista VARS_QUANT do notebook de EDA)
VARS_QUANT = ["hora_conexao", "duracao_carga_h", "energia_kwh"]
NOMES = {
    "hora_conexao": "Hora de conexão (h)",
    "duracao_carga_h": "Duração da carga (h)",
    "energia_kwh": "Energia entregue (kWh)",
}

# Classe usada para colorir a distribuição: período do dia da conexão (ordem cronológica)
CLASSE = "periodo_dia"
ORDEM_PERIODO = ["Madrugada", "Manhã", "Tarde", "Noite"]

# Sidebar: filtros (variáveis + intervalo)
with st.sidebar:
    st.header("Filtros")

    variaveis = st.multiselect(
        "Variáveis quantitativas",
        options=VARS_QUANT,
        default=VARS_QUANT,
        format_func=NOMES.get,
        help="Selecione as variáveis quantitativas que deseja analisar no dashboard.",
    )

    separar_por_classe = st.toggle(
        "Distinguir por período do dia",
        value=False,
        help="Colore a distribuição pelo período do dia da conexão (Madrugada, Manhã, Tarde ou Noite).",
    )

    # Um slider de intervalo para cada variável selecionada (limites arredondados para fora, passo de 0,1)
    intervalos = {}
    for var in variaveis:
        minimo = math.floor(df[var].min() * 10) / 10
        maximo = math.ceil(df[var].max() * 10) / 10
        intervalos[var] = st.slider(
            f"Intervalo de {NOMES[var][0].lower()}{NOMES[var][1:]}",  # minúscula só na 1ª letra (mantém o "kWh")
            min_value=minimo,
            max_value=maximo,
            value=(minimo, maximo),
            step=0.1,
            format="%.1f",
            key=f"intervalo_{var}",
        )

# Mantém só as sessões dentro de todos os intervalos escolhidos
df_filtrado = df
for var, (inicio, fim) in intervalos.items():
    df_filtrado = df_filtrado[df_filtrado[var].between(inicio, fim)]

st.caption(f"{len(df_filtrado):,} de {len(df):,} sessões dentro dos intervalos escolhidos.".replace(",", "."))

# Dashboard 1: correlação (heatmap) à esquerda, distribuição (histograma) à direita
col_correlacao, col_distribuicao = st.columns([1, 1.5])

# Cor do histograma sem classe: mesmo vermelho de destaque do tema (.streamlit/config.toml)
COR_HISTOGRAMA = "#c1121f"
# Uma cor por período, na ordem categórica fixa da paleta de referência (azul, laranja, aqua, amarelo)
CORES_PERIODO = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
CORES_CLASSE = alt.Scale(domain=ORDEM_PERIODO, range=CORES_PERIODO)

# Legenda das classes em texto, para caber no espaço livre da grade de histogramas
LEGENDA_CLASSE = "**Período do dia**  \n" + "  \n".join(
    f":color[■]{{foreground=\"{cor}\"}} {periodo}" for periodo, cor in zip(ORDEM_PERIODO, CORES_PERIODO)
)


def numero_br(expressao, formato):
    """Expressão Vega que formata um número no padrão brasileiro (1.234,5), trocando ponto e vírgula."""
    return f"replace(replace(replace(format({expressao}, '{formato}'), ',', '_'), '.', ','), '_', '.')"


def contar_por_faixa(dados, var, n_faixas=20):
    """Conta as sessões por faixa de `var` (e por período, se pedido) em pandas.

    Com 100 mil sessões, mandar as linhas cruas para o Altair pesaria o navegador:
    só as contagens por faixa vão para o gráfico.
    """
    bordas = np.histogram_bin_edges(dados[var], bins=n_faixas)
    faixa = pd.cut(dados[var], bins=bordas, include_lowest=True, labels=False).rename("faixa")
    grupos = [faixa, dados[CLASSE]] if separar_por_classe else [faixa]
    contagem = dados.groupby(grupos).size().rename("sessoes").reset_index()
    contagem["inicio"] = bordas[contagem["faixa"]]
    contagem["fim"] = bordas[contagem["faixa"] + 1]
    # Textos prontos para o tooltip, já no padrão brasileiro
    contagem["faixa_texto"] = [f"{a:.1f} a {b:.1f}".replace(".", ",") for a, b in zip(contagem["inicio"], contagem["fim"])]
    contagem["sessoes_texto"] = contagem["sessoes"].map(lambda n: f"{n:,}".replace(",", "."))
    return contagem


with col_correlacao:
    st.subheader("Correlação (Spearman)")

    if len(variaveis) < 2:
        st.warning("Selecione pelo menos 2 variáveis para calcular a correlação.")
    elif len(df_filtrado) < 30:
        st.warning("Poucas sessões nos intervalos escolhidos para calcular a correlação.")
    else:
        # Matriz de correlação de Spearman das variáveis selecionadas, em formato longo (uma linha por célula)
        corr = (
            df_filtrado[variaveis]
            .rename(columns=NOMES)
            .corr(method="spearman")
            .rename_axis(index="var_y", columns="var_x")
            .stack()
            .rename("correlacao")
            .reset_index()
        )
        # Só o triângulo inferior, sem a diagonal (sempre 1): a matriz é simétrica, o resto é repetição
        nomes = [NOMES[var] for var in variaveis]
        ordem = {nome: i for i, nome in enumerate(nomes)}
        corr = corr[corr["var_y"].map(ordem) > corr["var_x"].map(ordem)]
        corr["correlacao_texto"] = corr["correlacao"].map(lambda r: f"{r:.2f}".replace(".", ","))

        base = alt.Chart(corr).encode(
            x=alt.X(
                "var_x:N",
                title=None,
                sort=nomes[:-1],  # a última variável só aparece nas linhas
                # Quebra o nome antes da unidade ("Hora de conexão" / "(h)") para os rótulos não se encostarem
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=13,
                    labelLimit=200,
                    labelExpr="split(replace(datum.label, ' (', '|('), '|')",
                ),
            ),
            y=alt.Y(
                "var_y:N",
                title=None,
                sort=nomes[1:],  # a primeira só nas colunas
                axis=alt.Axis(labelFontSize=13, labelLimit=200),
            ),
        )
        heatmap = base.mark_rect().encode(
            color=alt.Color(
                "correlacao:Q",
                title="Spearman",
                scale=alt.Scale(scheme="redblue", domain=[-1, 1], reverse=True),
                legend=alt.Legend(titleFontSize=14, labelFontSize=13, labelExpr=numero_br("datum.value", ".1f")),
            ),
            tooltip=[
                alt.Tooltip("var_x", title="Variável"),
                alt.Tooltip("var_y", title="Variável"),
                alt.Tooltip("correlacao_texto:N", title="Spearman"),
            ],
        )
        valores = base.mark_text(fontSize=16).encode(
            text=alt.Text("correlacao_texto:N"),
            color=alt.condition(
                "abs(datum.correlacao) > 0.5", alt.value("white"), alt.value("black")
            ),
        )

        st.altair_chart(
            (heatmap + valores).properties(height=380),
            width="stretch",
            alt="Mapa de calor (triângulo inferior, sem a diagonal) da correlação de Spearman entre as variáveis quantitativas selecionadas",
        )

with col_distribuicao:
    st.subheader("Distribuição")

    if not variaveis:
        st.warning("Selecione pelo menos 1 variável para ver a distribuição.")
    elif df_filtrado.empty:
        st.warning("Nenhuma sessão dentro dos intervalos escolhidos.")
    else:
        # Com número par de variáveis não sobra espaço na grade: a legenda vai acima dela
        if separar_por_classe and len(variaveis) % 2 == 0:
            st.markdown(LEGENDA_CLASSE)

        # Um histograma por variável selecionada, em grade de 2 colunas (cada um com a sua escala)
        for inicio in range(0, len(variaveis), 2):
            colunas = st.columns(2)
            for coluna, var in zip(colunas, variaveis[inicio : inicio + 2]):
                tooltip_faixa = [
                    alt.Tooltip("faixa_texto:N", title=NOMES[var]),
                    alt.Tooltip("sessoes_texto:N", title="Sessões"),
                ]
                histograma = (
                    alt.Chart(contar_por_faixa(df_filtrado, var))
                    .mark_bar()
                    .encode(
                        x=alt.X(
                            "inicio:Q",
                            bin="binned",
                            title=NOMES[var],
                            axis=alt.Axis(labelExpr=numero_br("datum.value", "~g")),
                        ),
                        x2="fim:Q",
                        y=alt.Y(
                            "sessoes:Q",
                            title="Sessões",
                            axis=alt.Axis(labelExpr=numero_br("datum.value", ",d")),
                        ),
                        tooltip=tooltip_faixa,
                    )
                    .properties(height=200)
                )
                if separar_por_classe:
                    histograma = histograma.encode(
                        color=alt.Color(f"{CLASSE}:N", title="Período do dia", scale=CORES_CLASSE, legend=None),
                        # Empilha na ordem cronológica, de baixo para cima
                        order=alt.Order("ordem_periodo:Q"),
                        tooltip=[alt.Tooltip(f"{CLASSE}:N", title="Período")] + tooltip_faixa,
                    ).transform_calculate(
                        ordem_periodo=f"indexof({ORDEM_PERIODO}, datum.{CLASSE})"
                    )
                else:
                    histograma = histograma.mark_bar(color=COR_HISTOGRAMA)

                with coluna:
                    st.altair_chart(histograma, width="stretch", alt=f"Histograma da variável {NOMES[var]}")

            # Número ímpar de variáveis: a legenda ocupa o espaço que sobrou na última linha
            if separar_por_classe and len(colunas) == 2 and len(variaveis[inicio : inicio + 2]) == 1:
                colunas[1].markdown(LEGENDA_CLASSE)

# TODO: Dashboard 2 — KPIs (Aula 22)
