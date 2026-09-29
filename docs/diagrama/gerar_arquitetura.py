"""
UrbanIQ: arquitetura do pipeline de dados construído no PBL FIAP (Fases 1 a 5).

Fontes da verdade (lidas antes de desenhar):
  fase2-modelagem/relacional/ddl/*.sql ....... Oracle 21c, 15 tabelas, 17 FKs, 14 sequences, 7 índices
  fase3-ingestao/entregaveis/entrega-fase3.pdf  Databricks CE: catálogo urbaniq, schemas bronze/prata/ouro,
                                                volume arquivos_raw, 10 CSVs, Delta tb_cidadao, CRUD em SQL;
                                                prata e ouro criadas sem dados
  dashboards/powerbi/ ......................... gerador Python (seed 42, 1.000 chamados) + .pbix (lê CSV)
  qualidade-dados/ ............................ diagnóstico: 245 verificações contra a DDL, 15 reprovadas
  fase4-preparacao/ ........................... SQL JOIN 4 tabelas ALFA_* -> pandas (Colab) -> JSON ->
                                                Redis Cloud (RedisJSON) -> Folium (27 pontos)
  fase5-analitica/ ............................ massa 10.180 x 29 (seed 570088) -> limpeza (9.980) ->
                                                testes estatísticos -> Streamlit + notebook
  README (Stack) .............................. MongoDB, Redis (cache), Kafka marcados como "projetados"

Grade (1x): canvas 1920 x 1218
  cabeçalho y 0-110 | faixa A (chamados) y 130-500 | faixa B (Fase 4) y 520-720
  faixa C (Fase 5) y 740-940 | faixa projetada y 960-1098 | rodapé y 1118-1205
  Corredor da seta CSVs -> Power BI: y = 452, abaixo do card Databricks (termina em 422).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from diagram_kit import Diagram, PALETTE as P


HERE = pathlib.Path(__file__).resolve().parent
BLANK = str(HERE / "blank.png")
def oracle_logo(card_box, icon_size):
    """Wordmark da Oracle na proporção original, centralizado na área do ícone do card."""
    import base64
    x, y, w, h = card_box
    lw = 118; lh = lw * 88 / 600
    b64 = base64.b64encode((HERE / "oracle_wordmark.png").read_bytes()).decode()
    cy = y + 12 + icon_size / 2
    d.out.append(f'<image x="{x + w/2 - lw/2}" y="{cy - lh/2}" width="{lw}" height="{lh}" href="data:image/png;base64,{b64}"/>')

d = Diagram(1920, 1218)
GRAY = P["light"]

def planned(cx, y, w, icon, title, lines, isz=36):
    """Card de componente projetado e não implementado: borda tracejada, ícone esmaecido."""
    h = isz + 34 + 16 * len(lines) + 8
    x = cx - w / 2
    d.rect(x, y, w, h, fill="#FAFAFA", stroke="#B8C0C2", sw=1.2, dash="5 4")
    d.out.append(f'<g opacity="0.45">')
    d.icon(icon, cx - isz / 2, y + 10, isz)
    d.out.append("</g>")
    d.text(cx, y + isz + 27, title, 14, "#6B7478", True, maxw=w - 10)
    for i, l in enumerate(lines):
        d.text(cx, y + isz + 44 + 16 * i, l, 11.5, "#879196", maxw=w - 10)
    d.boxes.append((title, x, y, w, h))
    return (x, y, w, h)

def note(x, y, w, h, title, lines, color):
    d.rect(x, y, w, h, fill="#FFFFFF", stroke=color, sw=1.2, rx=10)
    d.rect(x, y, 6, h, fill=color, stroke=color, rx=3)
    d.text(x + 20, y + 28, title, 14, color, True, anchor="start", maxw=w - 30)
    for i, l in enumerate(lines):
        d.text(x + 20, y + 50 + 19 * i, l, 13, P["gray"], anchor="start", maxw=w - 30)

d.header("UrbanIQ", "Pipeline de dados do PBL FIAP: o que foi construído nas Fases 1 a 5",
         "Oracle  ·  Databricks  ·  Python  ·  Redis  ·  Power BI  ·  Streamlit  ·  https://github.com/Ant4rez/UrbanIq",
         chip="PBL FIAP · Tecnólogo em Ciência de Dados · 2026")

# ---------------- Faixa A: plataforma de chamados ----------------
d.group(40, 130, 1840, 370, "Plataforma de chamados urbanos  ·  Fases 2 e 3 + dashboard", "#1E3A5F", "#F4F7FB")
ora = d.card(150, 185, 200, BLANK, "Modelo relacional", ["DDL Oracle 21c · 3FN", "15 tabelas · 17 FKs", "14 sequences · 7 índices", "5 regras de negócio"], P["database"], icon_size=40)
oracle_logo(ora, 40)
gen = d.card(390, 185, 200, "python", "Gerador de dados", ["Python · random.seed(42)", "1.000 chamados sintéticos", "dez/2024 a jan/2026", "score 0-100 por subcategoria"], "#3776AB", icon_size=40)
csv = d.card(630, 185, 200, "programming/flowchart/multiple-documents.png", "Arquivos CSV", ["10 tabelas de dimensão", "tb_chamado_v3 (fato)", "prefixo T_URB_"], P["dark"], icon_size=40)
d.arrow([(gen[0] + gen[2], 262), (csv[0], 262)], "#3776AB", label="gera", label_at=(gen[0] + gen[2] + 6, 254), label_color="#3776AB")

# Databricks
DX, DY, DW, DH = 770, 160, 670, 262
d.rect(DX, DY, DW, DH, fill="#FFFFFF", stroke="#FF3621", sw=1.4, rx=12, shadow=True)
d.icon("databricks", DX + 16, DY + 12, 42)
d.text(DX + 70, DY + 32, "Databricks Community Edition  ·  catálogo urbaniq", 17, "#E0301E", True, anchor="start")
d.text(DX + 70, DY + 52, "Arquitetura medalhão: 3 schemas criados; a camada Bronze recebeu os dados em Delta Lake", 12.5, P["gray"], anchor="start", maxw=DW - 90)
st = d.stage_row(DX + 16, DY + 76, [
    ("B", "Bronze", "#B5651D", ["volume arquivos_raw", "10 CSVs carregados", "tabela Delta tb_cidadao", "SELECT · INSERT · UPDATE", "DELETE em SQL"]),
    ("P", "Prata", "#9AA5AB", ["schema criado", "sem dados ainda", "ETL: previsto", "", ""]),
    ("O", "Ouro", "#9AA5AB", ["schema criado", "sem dados ainda", "KPIs e score: previstos", "", ""]),
], width=205, gap=12, height=166)
d.arrow([(csv[0] + csv[2], 300), (DX + 16, 300)], "#B5651D", label="upload", label_at=(csv[0] + csv[2] + 4, 292), label_color="#B5651D")

pbi = d.card(1560, 185, 210, "onprem/analytics/powerbi.png", "Dashboard Power BI", ["7 páginas · star schema", "12 tabelas · 16 medidas DAX", "mapa georreferenciado", "Cidade Score (0-100)"], "#B8860B", icon_size=40)
d.arrow([(690, csv[1] + csv[3]), (690, 452), (1560, 452), (1560, pbi[1] + pbi[3])], "#B8860B", label="importa os CSVs", label_at=(1180, 447), label_color="#B8860B")

qd = d.card(390, 348, 200, "python", "Diagnóstico de qualidade", ["245 verificações", "CSVs × regras da DDL", "15 achados documentados"], P["security"], icon_size=34)
d.arrow([(150, ora[1] + ora[3]), (150, 410), (qd[0], 410)], P["database"], label="regras", label_at=(158, 402))
d.arrow([(575, csv[1] + csv[3]), (575, 410), (qd[0] + qd[2], 410)], P["dark"], label="dados", label_at=(518, 402), label_anchor="middle")

d.text(1780, 175, "", 12)

# ---------------- Faixa B: Fase 4 ----------------
d.group(40, 520, 1840, 200, "Fase 4  ·  exploração e NoSQL (avaliação de pontos turísticos por bairro)", "#7A3E9D", "#FAF6FC")
B_Y = 560
b1 = d.card(170, B_Y, 220, BLANK, "Oracle (base FIAP)", ["tabelas ALFA_*", "SQL: JOIN de 4 tabelas", "filtro de itens ativos"], P["database"], icon_size=36)
oracle_logo(b1, 36)
b2 = d.card(470, B_Y, 220, "python", "Análise exploratória", ["pandas · Google Colab", "limpeza de notas", "ranking por bairro"], "#3776AB", icon_size=36)
b3 = d.card(770, B_Y, 220, "onprem/inmemory/redis.png", "Redis Cloud", ["RedisJSON · chave única", "27 pontos com coordenadas", "carga via Redis Insight"], "#D82C20", icon_size=36)
b4 = d.card(1070, B_Y, 220, "client", "Mapa interativo", ["Folium · mapa.html", "cor pelo ranking", "do bairro"], P["dark"], icon_size=36)
for a, b, lab in [(b1, b2, "resultado"), (b2, b3, "JSON"), (b3, b4, "lê a chave")]:
    y = a[1] + 60
    d.arrow([(a[0] + a[2], y), (b[0], y)], P["gray"], label=lab, label_at=((a[0] + a[2] + b[0]) / 2, y - 8), label_anchor="middle", label_color=P["gray"])
note(1230, 560, 630, 132, "Pergunta de negócio (Q2)", ["Determinados bairros da cidade Alfa concentram", "as avaliações mais altas dos pontos turísticos?", "SQL traz as linhas; a agregação é feita em Python."], "#7A3E9D")

# ---------------- Faixa C: Fase 5 ----------------
d.group(40, 740, 1840, 200, "Fase 5  ·  inteligência analítica e estatística (sensores chegam até o cidadão?)", "#01A88D", "#F2FBF9")
C_Y = 780
c1 = d.card(170, C_Y, 220, "python", "Massa sintética", ["10.180 ocorrências × 29 col.", "seed 570088", "9 tipos de inconsistência"], "#3776AB", icon_size=36)
c2 = d.card(470, C_Y, 220, "python", "Preparação (pandas)", ["9 etapas de limpeza", "9.980 registros", "perda de 1,96%"], "#3776AB", icon_size=36)
c3 = d.card(770, C_Y, 220, "python", "Inferência estatística", ["Welch · qui-quadrado", "ANOVA · Kruskal-Wallis", "correlação e regressão"], P["ml"], icon_size=36)
c4 = d.card(1070, C_Y, 220, "client", "Painel Streamlit (ao vivo)", ["urbaniq.streamlit.app", "filtros, 5 KPIs, aba por elo", "+ notebook reprodutível"], "#E0301E", icon_size=36)
for a, b, lab in [(c1, c2, "limpa"), (c2, c3, "testa"), (c3, c4, "publica")]:
    y = a[1] + 60
    d.arrow([(a[0] + a[2], y), (b[0], y)], P["gray"], label=lab, label_at=((a[0] + a[2] + b[0]) / 2, y - 8), label_anchor="middle", label_color=P["gray"])
note(1230, 780, 630, 132, "Achado central", ["O score de prioridade não tem relação detectável", "com o tempo até o despacho: a central atende por", "ordem de chegada e o motor de priorização é ignorado."], "#01A88D")

# ---------------- Faixa projetada ----------------
d.group(40, 960, 1840, 146, "Arquitetura-alvo projetada nas Fases 2 e 3  ·  ainda não implementada", "#879196", "#FFFFFF", dash="3 4")
items = [("aws/general/mobile-client.png", "App e Portal", ["abertura de chamados"]),
         ("aws/iot/iot-sensor.png", "Sensores IoT", ["eventos urbanos"]),
         ("aws/iot/iot-camera.png", "Câmeras HD", ["evidência visual"]),
         ("onprem/queue/kafka.png", "Event stream", ["Kafka / Redis Streams"]),
         ("onprem/database/mongodb.png", "MongoDB", ["geoespacial 2dsphere"]),
         ("onprem/inmemory/redis.png", "Redis", ["cache de score (TTL)"]),
         ("onprem/analytics/databricks.png", "Score por ML", ["na camada Ouro"]),
         ("onprem/client/users.png", "Portal de transparência", ["status para o cidadão"])]
W8, G8 = 205, 21
x0 = 40 + (1840 - (8 * W8 + 7 * G8)) / 2
for i, (ic, t, ls) in enumerate(items):
    planned(x0 + W8 / 2 + i * (W8 + G8), 1000, W8, ic, t, ls)

# ---------------- Rodapé ----------------
d.stats_box(40, 1118, 1250, "Números verificáveis no repositório",
            "15 tabelas Oracle  ·  1.000 chamados sintéticos  ·  7 páginas no Power BI  ·  245 verificações de qualidade  ·  10.180 ocorrências na Fase 5")
lx = 1320
d.arrow([(lx, 1144), (lx + 34, 1144)], P["gray"])
d.text(lx + 42, 1148, "fluxo de dados implementado", 13, P["gray"], anchor="start")
d.rect(lx, 1161, 34, 18, fill="#FAFAFA", stroke="#B8C0C2", sw=1.2, rx=4, dash="5 4")
d.text(lx + 42, 1175, "componente projetado, não implementado", 13, P["gray"], anchor="start")
d.text(1880, 1203, "Projeto acadêmico · dados sintéticos da cidade fictícia Alfa · Thiago Fiel de Oliveira", 12.5, P["light"], anchor="end")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else str(HERE.parent / "assets" / "arquitetura-pipeline.png")
    for w in d.save(out):
        print("WARNING:", w)
    print("ok", out)
