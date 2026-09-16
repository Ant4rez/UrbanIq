"""
UrbanIQ | Centro de Operações Urbanas — Painel Analítico
PBL Fase 5 | Desafio 10 | Grupo DataGuy | Thiago Fiel de Oliveira, RM 570088

Dashboard interativo do 3º Desafio: comunica as descobertas da análise
estatística para as áreas operacional, tática e estratégica da gestão pública.

Execução local:
    streamlit run app_urbaniq.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ===========================================================================
# IDENTIDADE VISUAL
# Paleta validada em seis critérios: banda de luminosidade, croma mínimo,
# separação para protanopia, deuteranopia e tritanopia, piso de visão normal
# e contraste sobre o fundo.
# ===========================================================================
OURO, ROXO, TERRACOTA = "#A07400", "#7B3FA5", "#CC3B14"
AZUL, OLIVA = "#3160C8", "#5E8A00"
PAPEL, TINTA, SUAVE = "#F6F3EC", "#2E2A26", "#6E655B"
CATEGORICA = [OURO, ROXO, TERRACOTA, AZUL, OLIVA]

LAYOUT_BASE = dict(
    paper_bgcolor=PAPEL,
    plot_bgcolor=PAPEL,
    font=dict(color=TINTA, size=13),
    margin=dict(l=10, r=10, t=50, b=10),
    xaxis=dict(gridcolor="#E2DCD0", zerolinecolor="#E2DCD0"),
    yaxis=dict(gridcolor="#E2DCD0", zerolinecolor="#E2DCD0"),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

st.set_page_config(
    page_title="UrbanIQ | Centro de Operações Urbanas",
    page_icon="🏙",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
      .stApp {{ background-color: {PAPEL}; }}
      h1, h2, h3 {{ color: {TINTA}; }}
      [data-testid="stMetricValue"] {{ color: {TINTA}; font-size: 1.8rem; }}
      [data-testid="stMetricLabel"] {{ color: {SUAVE}; }}
      .bloco-achado {{
          background: #FFFFFF; border-left: 5px solid {TERRACOTA};
          padding: 14px 18px; border-radius: 4px; margin: 8px 0 18px 0;
      }}
      .bloco-ok {{
          background: #FFFFFF; border-left: 5px solid {OLIVA};
          padding: 14px 18px; border-radius: 4px; margin: 8px 0 18px 0;
      }}
      .bloco-recomendacao {{
          background: #FFFFFF; border-left: 5px solid {OURO};
          padding: 16px 20px; border-radius: 4px; margin: 10px 0;
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

ARQUIVO_AJUSTADO = "cidade_alfa_ocorrencias_ajustado.xlsx"
ARQUIVO_BRUTO = "cidade_alfa_ocorrencias_urbanas.xlsx"
LIMITE_DATA = pd.Timestamp("2026-09-30 23:59:59")


# ===========================================================================
# CARGA E PREPARAÇÃO
# ===========================================================================
def localizar(nome):
    """Procura o arquivo na pasta do app, na raiz e em fase5-analitica/dados."""
    aqui = Path(__file__).parent
    candidatos = [
        aqui / nome,
        aqui / ".." / "dados" / nome,
        aqui / ".." / ".." / "fase5-analitica" / "dados" / nome,
        Path.cwd() / nome,
        Path.cwd() / "fase5-analitica" / "dados" / nome,
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho
    return None


def preparar(df):
    """Aplica as 9 etapas de limpeza do 1º Desafio.

    Usada só quando o arquivo já tratado não está disponível, para que o
    dashboard funcione mesmo publicado com apenas a base bruta no repositório.
    """
    df = df.drop_duplicates().copy()

    df["fonte_dado"] = (df["fonte_dado"].str.strip().str.upper()
                        .str.replace(" ", "_", regex=False))
    df["bairro"] = df["bairro"].fillna("Não Informado")

    df.loc[df["score_prioridade"] > 100, "score_prioridade"] = np.nan
    invalida = ~df["satisfacao_cidadao"].isin([1, 2, 3, 4, 5]) & df["satisfacao_cidadao"].notna()
    df.loc[invalida, "satisfacao_cidadao"] = np.nan
    df.loc[df["tempo_resposta_min"] < 0, "tempo_resposta_min"] = np.nan

    invertida = df["dt_encerramento"] < df["dt_abertura"]
    df.loc[invertida, ["dt_encerramento", "tempo_resolucao_horas"]] = np.nan
    df.loc[invertida, "sla_cumprido"] = "NAO APURADO"

    df = df[df["dt_abertura"] <= LIMITE_DATA]
    df.loc[df["custo_operacional_reais"] > 1_000_000, "custo_operacional_reais"] = np.nan
    return df


@st.cache_data(show_spinner="Carregando a base de ocorrências...")
def carregar():
    """Carrega a base tratada; se não existir, trata a bruta na hora."""
    caminho = localizar(ARQUIVO_AJUSTADO)
    tratado_na_hora = False

    if caminho is None:
        caminho = localizar(ARQUIVO_BRUTO)
        tratado_na_hora = True

    if caminho is None:
        return None, None

    df = pd.read_excel(caminho)
    for coluna in ["dt_abertura", "dt_despacho", "dt_chegada_equipe", "dt_encerramento"]:
        df[coluna] = pd.to_datetime(df[coluna], errors="coerce")

    if tratado_na_hora:
        df = preparar(df)

    # Atributos derivados (engenharia de atributos da Parte 1)
    df["lag_despacho_min"] = (
        (df["dt_despacho"] - df["dt_abertura"]).dt.total_seconds() / 60).round(1)
    df["razao_sla"] = (df["tempo_resolucao_horas"] / df["sla_horas_previsto"]).round(3)
    df["mes_ano"] = df["dt_abertura"].dt.to_period("M").astype(str)

    return df, caminho.name


dados, nome_arquivo = carregar()

if dados is None:
    st.error(
        f"Não encontrei `{ARQUIVO_AJUSTADO}` nem `{ARQUIVO_BRUTO}`.\n\n"
        "Coloque um dos dois na mesma pasta do app ou em `fase5-analitica/dados/`."
    )
    st.stop()


# ===========================================================================
# FILTROS (sidebar)
# ===========================================================================
PADRAO = {
    "regioes": sorted(dados["regiao"].unique()),
    "categorias": sorted(dados["categoria"].unique()),
    "fontes": sorted(dados["fonte_dado"].unique()),
}

for chave, valor in PADRAO.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


def limpar_filtros():
    """Devolve todos os filtros ao estado inicial."""
    for chave, valor in PADRAO.items():
        st.session_state[chave] = valor


with st.sidebar:
    st.markdown(f"### 🏙 UrbanIQ")
    st.caption("Centro de Operações Urbanas · cidade Alfa")
    st.divider()

    st.subheader("Filtros")

    data_min = dados["dt_abertura"].min().date()
    data_max = dados["dt_abertura"].max().date()
    periodo = st.date_input(
        "Período de abertura",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max,
    )

    st.multiselect("Região", PADRAO["regioes"], key="regioes")
    st.multiselect("Categoria", PADRAO["categorias"], key="categorias")
    st.multiselect("Canal de origem", PADRAO["fontes"], key="fontes")

    st.button("Limpar filtros", on_click=limpar_filtros, width="stretch")

    st.divider()
    st.caption(f"Fonte: `{nome_arquivo}`")
    st.caption("Grupo DataGuy · RM 570088")

# Aplicação dos filtros
filtro = (
    dados["regiao"].isin(st.session_state["regioes"])
    & dados["categoria"].isin(st.session_state["categorias"])
    & dados["fonte_dado"].isin(st.session_state["fontes"])
)
if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
    filtro &= dados["dt_abertura"].dt.date.between(periodo[0], periodo[1])

df = dados[filtro]

if df.empty:
    st.warning("Nenhuma ocorrência atende aos filtros selecionados.")
    st.stop()


# ===========================================================================
# CABEÇALHO E KPIs
# ===========================================================================
st.title("Centro de Operações Urbanas")
st.markdown(
    "#### O investimento em sensores inteligentes chega até o cidadão?"
)
st.caption(
    f"{len(df):,} ocorrências selecionadas de {len(dados):,} · "
    f"{df['dt_abertura'].min():%b/%Y} a {df['dt_abertura'].max():%b/%Y}".replace(",", ".")
)

finalizadas = df[df["sla_cumprido"].isin(["SIM", "NAO"])]
pct_sla = (finalizadas["sla_cumprido"] == "SIM").mean() * 100 if len(finalizadas) else 0
em_aberto = (~df["status_ocorrencia"].isin(["RESOLVIDO", "ENCERRADO"])).sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Ocorrências", f"{len(df):,}".replace(",", "."))
k2.metric("Dentro do SLA", f"{pct_sla:.1f}%")
k3.metric("Resposta média", f"{df['tempo_resposta_min'].mean():.0f} min")
k4.metric("Resolução mediana", f"{df['tempo_resolucao_horas'].median():.0f} h")
k5.metric("Em aberto", f"{em_aberto:,}".replace(",", "."))

st.divider()


# ===========================================================================
# ABAS: OS QUATRO ELOS DA CADEIA
# ===========================================================================
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "1 · Detecção",
    "2 · Despacho",
    "3 · Execução",
    "4 · Percepção",
    "Recomendações",
])


# --------------------------------------------------------------------- ELO 1
with aba1:
    st.subheader("Elo 1 · Detecção")
    st.write(
        "Sensores IoT e câmeras detectam ocorrências mais rápido que os canais "
        "humanos? Este elo mede o tempo entre a abertura e a chegada da equipe."
    )

    automatica = df.loc[df.tipo_fonte == "AUTOMATICA", "tempo_resposta_min"].dropna()
    cidadao = df.loc[df.tipo_fonte == "CIDADAO", "tempo_resposta_min"].dropna()

    c1, c2, c3 = st.columns(3)
    c1.metric("Fonte automática", f"{automatica.mean():.0f} min" if len(automatica) else "—")
    c2.metric("Canal do cidadão", f"{cidadao.mean():.0f} min" if len(cidadao) else "—")
    if len(automatica) and len(cidadao):
        ganho = (1 - automatica.mean() / cidadao.mean()) * 100
        c3.metric("Ganho do sensor", f"{ganho:.0f}%", delta=f"{cidadao.mean() - automatica.mean():.0f} min")

    esquerda, direita = st.columns([3, 2])

    with esquerda:
        por_canal = (df.groupby("fonte_dado")
                       .agg(media=("tempo_resposta_min", "mean"),
                            tipo=("tipo_fonte", "first"),
                            n=("id_ocorrencia", "size"))
                       .sort_values("media").reset_index())
        fig = px.bar(
            por_canal, x="media", y="fonte_dado", orientation="h",
            color="tipo", color_discrete_map={"AUTOMATICA": AZUL, "CIDADAO": TERRACOTA},
            labels={"media": "tempo médio de resposta (min)", "fonte_dado": "",
                    "tipo": "natureza"},
            title="Tempo até a equipe chegar, por canal de origem",
            hover_data={"n": True, "media": ":.0f"},
        )
        fig.update_layout(**LAYOUT_BASE, height=380, bargap=0.35)
        st.plotly_chart(fig, width="stretch")

    with direita:
        fig = px.box(
            df.dropna(subset=["tempo_resposta_min"]),
            x="tipo_fonte", y="tempo_resposta_min", color="tipo_fonte",
            color_discrete_map={"AUTOMATICA": AZUL, "CIDADAO": TERRACOTA},
            labels={"tipo_fonte": "", "tempo_resposta_min": "minutos"},
            title="Dispersão do tempo de resposta", points=False,
        )
        fig.update_layout(**LAYOUT_BASE, height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch")

    st.markdown(
        '<div class="bloco-ok"><b>Elo 1 funciona.</b> A detecção automática chega ao '
        'local em aproximadamente metade do tempo do canal humano. O teste t confirma '
        'a diferença com p praticamente zero e tamanho de efeito grande.</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- ELO 2
with aba2:
    st.subheader("Elo 2 · Despacho")
    st.write(
        "O UrbanIQ calcula um score de prioridade de 0 a 100 para cada ocorrência. "
        "A central usa esse score para decidir quem é acionado primeiro?"
    )

    elo2 = df.dropna(subset=["score_prioridade", "lag_despacho_min"])

    if len(elo2) > 30:
        correlacao = elo2["score_prioridade"].corr(elo2["lag_despacho_min"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Correlação score x despacho", f"{correlacao:+.3f}")
        c2.metric("Variância explicada", f"{correlacao ** 2 * 100:.2f}%")
        c3.metric("Despacho mediano", f"{elo2['lag_despacho_min'].median():.0f} min")

        esquerda, direita = st.columns([3, 2])

        with esquerda:
            amostra = elo2.sample(n=min(2500, len(elo2)), random_state=570088)
            fig = px.scatter(
                amostra, x="score_prioridade", y="lag_despacho_min",
                opacity=0.28, color_discrete_sequence=[ROXO],
                labels={"score_prioridade": "score de prioridade (0 a 100)",
                        "lag_despacho_min": "minutos até o acionamento"},
                title="Prioridade alta não é despachada antes",
            )

            # Reta de tendência por mínimos quadrados, calculada com numpy.
            # Evita o trendline="ols" do plotly, que exige statsmodels e quebra
            # o app em qualquer ambiente onde essa biblioteca não esteja instalada.
            inclinacao, intercepto = np.polyfit(
                amostra["score_prioridade"], amostra["lag_despacho_min"], 1)
            linha_x = np.linspace(amostra["score_prioridade"].min(),
                                  amostra["score_prioridade"].max(), 100)
            fig.add_trace(go.Scatter(
                x=linha_x, y=inclinacao * linha_x + intercepto,
                mode="lines", line=dict(color=TERRACOTA, width=2.5),
                name=f"tendência (r = {correlacao:+.3f})",
                hovertemplate="tendência<extra></extra>",
            ))
            fig.update_layout(showlegend=False)
            fig.update_layout(**LAYOUT_BASE, height=400)
            fig.update_yaxes(range=[0, elo2["lag_despacho_min"].quantile(0.99)])
            st.plotly_chart(fig, width="stretch")

        with direita:
            faixas = pd.cut(elo2["score_prioridade"], [0, 25, 50, 75, 100],
                            labels=["0-25\nbaixa", "26-50\nmédia",
                                    "51-75\nalta", "76-100\ncrítica"])
            por_faixa = (elo2.groupby(faixas, observed=True)["lag_despacho_min"]
                             .median().reset_index())
            por_faixa.columns = ["faixa", "mediana"]
            fig = px.bar(
                por_faixa, x="faixa", y="mediana",
                color_discrete_sequence=[SUAVE],
                labels={"faixa": "faixa de prioridade", "mediana": "despacho mediano (min)"},
                title="A fila ignora a prioridade",
            )
            fig.update_layout(**LAYOUT_BASE, height=400, bargap=0.4)
            st.plotly_chart(fig, width="stretch")

    if len(finalizadas):
        por_fonte = (finalizadas.groupby("tipo_fonte")["sla_cumprido"]
                     .apply(lambda s: (s == "SIM").mean() * 100).reset_index())
        por_fonte.columns = ["tipo_fonte", "pct_sla"]
        fig = px.bar(
            por_fonte, x="tipo_fonte", y="pct_sla",
            color="tipo_fonte", color_discrete_map={"AUTOMATICA": AZUL, "CIDADAO": TERRACOTA},
            labels={"tipo_fonte": "", "pct_sla": "% dentro do SLA"},
            title="O ganho da detecção não se converte em prazo cumprido",
            text_auto=".1f",
        )
        fig.update_layout(**LAYOUT_BASE, height=300, showlegend=False, bargap=0.55)
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, width="stretch")

    st.markdown(
        '<div class="bloco-achado"><b>A cadeia quebra aqui.</b> O score de prioridade '
        'não tem relação detectável com o tempo de despacho, e a fonte do dado não tem '
        'associação com o cumprimento do SLA. A central atende por ordem de chegada, e '
        'os minutos ganhos pelo sensor evaporam nesta etapa.</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- ELO 3
with aba3:
    st.subheader("Elo 3 · Execução")
    st.write(
        "A execução funciona, mas funciona igual para todos os bairros? "
        "Este elo mede a desigualdade territorial do serviço público."
    )

    if len(finalizadas):
        painel = (finalizadas.groupby("regiao")
                  .agg(ocorrencias=("id_ocorrencia", "size"),
                       resolucao_h=("tempo_resolucao_horas", "median"),
                       satisfacao=("satisfacao_cidadao", "mean"))
                  .join((finalizadas.groupby("regiao")["sla_cumprido"]
                         .apply(lambda s: (s == "SIM").mean() * 100)).rename("pct_sla"))
                  .sort_values("pct_sla", ascending=False).reset_index())

        media_cidade = (finalizadas["sla_cumprido"] == "SIM").mean() * 100
        amplitude = painel["pct_sla"].max() - painel["pct_sla"].min()

        c1, c2, c3 = st.columns(3)
        c1.metric("Melhor região", painel.iloc[0]["regiao"], f"{painel.iloc[0]['pct_sla']:.1f}%")
        c2.metric("Pior região", painel.iloc[-1]["regiao"], f"{painel.iloc[-1]['pct_sla']:.1f}%",
                  delta_color="inverse")
        c3.metric("Amplitude", f"{amplitude:.1f} p.p.")

        esquerda, direita = st.columns(2)

        with esquerda:
            cores = [TERRACOTA if v < media_cidade - 8 else OLIVA if v > media_cidade + 8
                     else SUAVE for v in painel["pct_sla"]]
            fig = go.Figure(go.Bar(
                x=painel["pct_sla"], y=painel["regiao"], orientation="h",
                marker_color=cores, text=[f"{v:.1f}%" for v in painel["pct_sla"]],
                textposition="outside",
            ))
            fig.add_vline(x=media_cidade, line_dash="dash", line_color=TINTA,
                          annotation_text=f"média {media_cidade:.1f}%")
            fig.update_layout(**LAYOUT_BASE, height=380, bargap=0.4,
                              title="Prazo cumprido por região",
                              xaxis_title="% dentro do SLA")
            fig.update_xaxes(range=[0, 108])
            st.plotly_chart(fig, width="stretch")

        with direita:
            fig = px.scatter(
                painel, x="pct_sla", y="satisfacao", text="regiao",
                size="ocorrencias", color_discrete_sequence=[OURO],
                labels={"pct_sla": "% dentro do SLA", "satisfacao": "satisfação média (1 a 5)"},
                title="Onde o prazo é cumprido, o cidadão avalia melhor",
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(**LAYOUT_BASE, height=380)
            st.plotly_chart(fig, width="stretch")

    st.markdown("##### Distribuição geográfica das ocorrências")
    mapa = df.dropna(subset=["latitude", "longitude"]).copy()
    if len(mapa):
        st.map(mapa.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]],
               size=20, color="#A0740088")

    st.markdown(
        '<div class="bloco-achado"><b>A execução é desigual.</b> A ANOVA e o '
        'Kruskal-Wallis concordam que as regiões diferem, e a diferença entre a melhor '
        'e a pior é grande demais para ser variação operacional. Duas pessoas com o '
        'mesmo problema recebem serviços de qualidade diferente conforme onde moram.</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------- ELO 4
with aba4:
    st.subheader("Elo 4 · Percepção do cidadão")
    st.write(
        "O que determina a nota do cidadão: o tempo absoluto de atendimento "
        "ou a promessa de prazo cumprida?"
    )

    avaliadas = df.dropna(subset=["satisfacao_cidadao"])

    if len(avaliadas) > 30:
        comparativo = []
        for variavel, rotulo in [
            ("razao_sla", "Razão do SLA (promessa)"),
            ("tempo_resposta_min", "Tempo de resposta"),
            ("tempo_resolucao_horas", "Tempo de resolução"),
            ("lag_despacho_min", "Tempo até o despacho"),
            ("custo_operacional_reais", "Custo operacional"),
        ]:
            par = avaliadas[[variavel, "satisfacao_cidadao"]].dropna()
            if len(par) > 30:
                comparativo.append({"variavel": rotulo,
                                    "r": par[variavel].corr(par["satisfacao_cidadao"])})
        comparativo = pd.DataFrame(comparativo).sort_values("r")

        c1, c2 = st.columns(2)
        c1.metric("Satisfação média", f"{avaliadas['satisfacao_cidadao'].mean():.2f}")
        if len(comparativo):
            campea = comparativo.iloc[0]
            c2.metric("Maior influência", campea["variavel"], f"r = {campea['r']:+.3f}")

        esquerda, direita = st.columns(2)

        with esquerda:
            fig = px.bar(
                comparativo, x="r", y="variavel", orientation="h",
                color_discrete_sequence=[TERRACOTA],
                labels={"r": "correlação com a satisfação", "variavel": ""},
                title="O que mais pesa na nota do cidadão",
                text_auto=".3f",
            )
            fig.update_layout(**LAYOUT_BASE, height=380, bargap=0.4)
            st.plotly_chart(fig, width="stretch")

        with direita:
            faixas = pd.cut(avaliadas["razao_sla"], bins=10)
            curva = (avaliadas.groupby(faixas, observed=True)
                     .agg(satisfacao=("satisfacao_cidadao", "mean"),
                          n=("id_ocorrencia", "size")).reset_index())
            curva["razao"] = [i.mid for i in curva["razao_sla"]]
            fig = px.scatter(
                curva, x="razao", y="satisfacao", size="n",
                color_discrete_sequence=[OURO],
                labels={"razao": "razão do SLA (1,0 = prazo cumprido no limite)",
                        "satisfacao": "satisfação média"},
                title="A satisfação cai quando o prazo estoura",
            )
            fig.add_vline(x=1.0, line_dash="dash", line_color=SUAVE,
                          annotation_text="prazo prometido")
            fig.update_layout(**LAYOUT_BASE, height=380)
            st.plotly_chart(fig, width="stretch")

    st.markdown("##### Evolução mensal")
    mensal = (df.groupby("mes_ano")
              .agg(ocorrencias=("id_ocorrencia", "size"),
                   satisfacao=("satisfacao_cidadao", "mean")).reset_index())
    fig = go.Figure()
    fig.add_bar(x=mensal["mes_ano"], y=mensal["ocorrencias"], name="ocorrências",
                marker_color=AZUL, opacity=0.35)
    fig.update_layout(**LAYOUT_BASE, height=300,
                      title="Volume mensal de ocorrências",
                      xaxis_title="mês", yaxis_title="ocorrências")
    st.plotly_chart(fig, width="stretch")

    st.markdown(
        '<div class="bloco-achado"><b>O cidadão pune a promessa quebrada.</b> '
        'A razão do SLA correlaciona mais forte com a satisfação do que o tempo '
        'absoluto. Resolver em 60 h com prazo de 72 satisfaz mais que resolver em '
        '8 h com prazo de 6.</div>',
        unsafe_allow_html=True,
    )


# ------------------------------------------------------------ RECOMENDAÇÕES
with aba5:
    st.subheader("Recomendações para a gestão pública")
    st.write(
        "Cada recomendação abaixo é sustentada por um resultado estatístico da análise."
    )

    recomendacoes = [
        ("1. Ordenar a fila de despacho pelo score de prioridade",
         "Hoje a central atende por ordem de chegada. A correlação entre o score e o "
         "tempo de despacho é praticamente nula, o que significa que o motor de "
         "priorização é calculado e ignorado. É uma mudança de software, não de orçamento.",
         "Elo 2 · correlação não significativa"),
        ("2. Medir o SLA a partir da detecção, não do registro",
         "O sensor entrega quase metade do tempo de resposta, mas isso não aparece no "
         "indicador porque o SLA é contado a partir da resolução. Sem corrigir a métrica, "
         "o investimento em IoT nunca se justifica nos números.",
         "Elo 2 · V de Cramér próximo de zero"),
        ("3. Realocar equipes para as regiões com pior desempenho",
         "A diferença de cumprimento de SLA entre a melhor e a pior região é estrutural, "
         "não ruído. A ANOVA e o Kruskal-Wallis confirmam que as regiões diferem de forma "
         "estatisticamente significativa.",
         "Elo 3 · ANOVA com p praticamente zero"),
        ("4. Renegociar os prazos prometidos por categoria",
         "O cidadão reage mais à promessa quebrada do que à demora em si. Prazos realistas "
         "e cumpridos geram mais satisfação que prazos curtos e estourados.",
         "Elo 4 · razão do SLA supera o tempo absoluto"),
        ("5. Dimensionar a operação para a demanda real",
         "A taxa de chegada supera a capacidade instalada, e por isso o backlog cresce de "
         "forma contínua. O modelo de filas indica o número mínimo de equipes para "
         "estabilizar, e o ponto a partir do qual contratar deixa de compensar.",
         "Cálculo · limite e derivada da função de espera"),
    ]

    for titulo, texto, base in recomendacoes:
        st.markdown(
            f'<div class="bloco-recomendacao">'
            f'<b style="font-size:1.05rem">{titulo}</b><br>'
            f'<span style="color:{SUAVE}">{texto}</span><br>'
            f'<span style="color:{OURO}; font-size:0.85rem">Base: {base}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()
    st.caption(
        "UrbanIQ · PBL Fase 5 · Desafio 10 — Centro de Operações Urbanas · "
        "Grupo DataGuy · Thiago Fiel de Oliveira, RM 570088"
    )
