"""
UrbanIQ | Fase 5 - Inteligencia Analitica, Estatistica e Tomada de Decisao
Desafio 10 - Centro de Operacoes Urbanas (COU) da cidade Alfa

Gerador da massa de dados sintetica de ocorrencias urbanas.

ESTRATEGIA DE GERACAO (meio-termo):
  - 4 padroes FORTES sao embutidos de proposito, para que os testes estatisticos
    tenham o que detectar e as recomendacoes de gestao tenham base.
  - As demais relacoes ficam soltas (ruido), garantindo que pelo menos uma
    hipotese de negocio NAO se confirme. Analise honesta tem hipotese refutada.
  - Defeitos de qualidade sao plantados de proposito, para que o 1o Desafio
    (preparacao e limpeza) tenha material real de trabalho.

PADROES FORTES EMBUTIDOS:
  P1. Fontes automaticas (Sensor IoT / Camera HD) respondem mais rapido que
      canais humanos (App / Portal / Telefone 156).
  P2. Chuva aumenta o volume e a criticidade de ocorrencias de Drenagem.
  P3. Quanto maior o tempo de resposta, menor a satisfacao do cidadao.
  P4. O cumprimento de SLA e desigual entre as regioes da cidade.

RELACOES DELIBERADAMENTE FRACAS (hipoteses que nao se confirmam):
  N1. score_prioridade x tempo ate o despacho -> o motor de priorizacao existe
      no sistema, mas a operacao nao o respeita no momento do despacho.
  N2. temperatura x volume de ocorrencias.
  N3. custo_operacional x satisfacao do cidadao.

Autor: Thiago Fiel de Oliveira (RM 570088) | Grupo DataGuy
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIGURACAO
# ---------------------------------------------------------------------------
SEMENTE = 570088          # RM como semente: execucao reprodutivel
N_OCORRENCIAS = 10_000
DATA_INICIO = pd.Timestamp("2024-10-01")
DATA_FIM = pd.Timestamp("2026-09-30")
ARQUIVO_SAIDA = "cidade_alfa_ocorrencias_urbanas.xlsx"

rng = np.random.default_rng(SEMENTE)

# ---------------------------------------------------------------------------
# DIMENSOES DA CIDADE ALFA
# ---------------------------------------------------------------------------
# Bairros herdados do exercicio guiado da Fase 5, para manter coerencia de
# universo entre os desafios. Coordenadas na Grande Sao Paulo para o mapa.
BAIRROS = {
    "Parque Central":  {"regiao": "Centro", "lat": -23.5505, "lon": -46.6333, "dens": 12800},
    "Cidade Nova":     {"regiao": "Centro", "lat": -23.5450, "lon": -46.6400, "dens": 11200},
    "Jardim Alfa":     {"regiao": "Norte",  "lat": -23.5050, "lon": -46.6250, "dens": 7400},
    "Vila Verde":      {"regiao": "Norte",  "lat": -23.4980, "lon": -46.6600, "dens": 6100},
    "Horizonte":       {"regiao": "Sul",    "lat": -23.6200, "lon": -46.6400, "dens": 9300},
    "Morada do Sol":   {"regiao": "Sul",    "lat": -23.6450, "lon": -46.6900, "dens": 8200},
    "Nova Esperanca":  {"regiao": "Leste",  "lat": -23.5400, "lon": -46.4900, "dens": 10500},
    "Santa Luzia":     {"regiao": "Leste",  "lat": -23.5550, "lon": -46.4500, "dens": 9800},
    "Boa Vista":       {"regiao": "Oeste",  "lat": -23.5650, "lon": -46.7200, "dens": 5600},
    "Industrial":      {"regiao": "Oeste",  "lat": -23.5800, "lon": -46.7600, "dens": 3100},
}
NOMES_BAIRROS = list(BAIRROS)

# P4: fator de desempenho operacional por regiao. Valor > 1 significa
# atendimento mais lento. Essa desigualdade e o achado territorial da analise.
FATOR_REGIAO = {"Centro": 0.82, "Sul": 0.93, "Oeste": 1.05, "Norte": 1.22, "Leste": 1.35}

# categoria -> (subcategorias, SLA em horas, peso base, equipe, sensivel a chuva)
CATEGORIAS = {
    "Drenagem e Alagamento": (
        ["Boca de lobo entupida", "Alagamento de via", "Galeria pluvial rompida"],
        12, 0.10, "Equipe Drenagem", True),
    "Pavimentacao": (
        ["Buraco na pista", "Calcada danificada", "Sinalizacao horizontal apagada"],
        72, 0.20, "Equipe Infraestrutura Viaria", False),
    "Iluminacao Publica": (
        ["Poste apagado", "Luminaria oscilando", "Fiacao exposta"],
        48, 0.18, "Equipe Iluminacao", False),
    "Residuos Urbanos": (
        ["Descarte irregular", "Coleta nao realizada", "Entulho em via publica"],
        36, 0.16, "Equipe Limpeza Urbana", False),
    "Transito e Mobilidade": (
        ["Semaforo inoperante", "Acidente com bloqueio de via", "Via obstruida"],
        6, 0.12, "Equipe Resposta Rapida", False),
    "Arborizacao": (
        ["Arvore com risco de queda", "Poda necessaria", "Queda de galho"],
        24, 0.09, "Equipe Resposta Rapida", True),
    "Rede de Agua e Esgoto": (
        ["Vazamento em via", "Esgoto a ceu aberto", "Falta de abastecimento"],
        18, 0.09, "Equipe Drenagem", False),
    "Seguranca Urbana": (
        ["Vandalismo em equipamento publico", "Area de risco sem iluminacao",
         "Ocupacao irregular de via"],
        24, 0.06, "Equipe Resposta Rapida", False),
}
NOMES_CATEGORIAS = list(CATEGORIAS)
PESOS_CATEGORIAS = np.array([CATEGORIAS[c][2] for c in NOMES_CATEGORIAS])
PESOS_CATEGORIAS = PESOS_CATEGORIAS / PESOS_CATEGORIAS.sum()

# fonte -> (tipo, peso). O Desafio 10 pede unificacao de fontes: sao 5.
FONTES = {
    "APP_MOBILE":   ("CIDADAO", 0.28),
    "PORTAL_WEB":   ("CIDADAO", 0.17),
    "TELEFONE_156": ("CIDADAO", 0.23),
    "SENSOR_IOT":   ("AUTOMATICA", 0.20),
    "CAMERA_HD":    ("AUTOMATICA", 0.12),
}
NOMES_FONTES = list(FONTES)
PESOS_FONTES = np.array([FONTES[f][1] for f in NOMES_FONTES])


# ---------------------------------------------------------------------------
# 1. SERIE CLIMATICA DIARIA
# ---------------------------------------------------------------------------
def gerar_clima():
    """Serie diaria de temperatura e chuva com sazonalidade do Sudeste.

    Periodo chuvoso de outubro a marco. A chuva alimenta o padrao P2.
    """
    dias = pd.date_range(DATA_INICIO, DATA_FIM, freq="D")
    dia_do_ano = dias.dayofyear.to_numpy()

    # Temperatura: senoide anual com pico em janeiro + ruido diario
    temp_base = 24.0 + 5.0 * np.cos(2 * np.pi * (dia_do_ano - 15) / 365.25)
    temperatura = np.round(temp_base + rng.normal(0, 2.6, len(dias)), 1)

    # Chuva: probabilidade e intensidade sobem no verao
    prob_chuva = 0.22 + 0.30 * np.clip(np.cos(2 * np.pi * (dia_do_ano - 15) / 365.25), 0, None)
    chove = rng.random(len(dias)) < prob_chuva
    intensidade = rng.gamma(shape=1.7, scale=9.5, size=len(dias))
    chuva = np.where(chove, np.round(intensidade, 1), 0.0)

    return pd.DataFrame({"data": dias, "temperatura_c": temperatura, "chuva_mm": chuva})


clima = gerar_clima()

# P2: dias chuvosos concentram mais ocorrencias. O peso do dia cresce com a chuva.
peso_dia = 1.0 + 0.055 * clima["chuva_mm"].to_numpy()
peso_dia = peso_dia / peso_dia.sum()

idx_dias = rng.choice(len(clima), size=N_OCORRENCIAS, p=peso_dia)
idx_dias.sort()

datas_base = clima["data"].to_numpy()[idx_dias]
temperatura = clima["temperatura_c"].to_numpy()[idx_dias]
chuva = clima["chuva_mm"].to_numpy()[idx_dias]

# Hora de abertura: dois picos, manha (08h) e fim de tarde (18h)
turno = rng.random(N_OCORRENCIAS) < 0.45
hora = np.where(turno,
                np.clip(rng.normal(8.5, 2.2, N_OCORRENCIAS), 0, 23.99),
                np.clip(rng.normal(18.0, 2.8, N_OCORRENCIAS), 0, 23.99))
minutos_do_dia = (hora * 60).astype(int)
dt_abertura = pd.to_datetime(datas_base) + pd.to_timedelta(minutos_do_dia, unit="m")


# ---------------------------------------------------------------------------
# 2. CATEGORIA (P2: chuva puxa Drenagem e Arborizacao)
# ---------------------------------------------------------------------------
categorias = np.empty(N_OCORRENCIAS, dtype=object)
for i in range(N_OCORRENCIAS):
    pesos = PESOS_CATEGORIAS.copy()
    if chuva[i] > 0:
        reforco = 1.0 + 0.075 * chuva[i]          # ate ~4x em chuva forte
        for j, cat in enumerate(NOMES_CATEGORIAS):
            if CATEGORIAS[cat][4]:                 # sensivel a chuva
                pesos[j] *= reforco
        pesos = pesos / pesos.sum()
    categorias[i] = rng.choice(NOMES_CATEGORIAS, p=pesos)

subcategorias = np.array([rng.choice(CATEGORIAS[c][0]) for c in categorias], dtype=object)
sla_previsto = np.array([CATEGORIAS[c][1] for c in categorias], dtype=float)
equipes = np.array([CATEGORIAS[c][3] for c in categorias], dtype=object)


# ---------------------------------------------------------------------------
# 3. LOCALIZACAO
# ---------------------------------------------------------------------------
bairros = rng.choice(NOMES_BAIRROS, size=N_OCORRENCIAS)
regioes = np.array([BAIRROS[b]["regiao"] for b in bairros], dtype=object)
densidade = np.array([BAIRROS[b]["dens"] for b in bairros], dtype=int)
latitude = np.round([BAIRROS[b]["lat"] + rng.normal(0, 0.012) for b in bairros], 6)
longitude = np.round([BAIRROS[b]["lon"] + rng.normal(0, 0.012) for b in bairros], 6)


# ---------------------------------------------------------------------------
# 4. FONTE DO DADO (P1)
# ---------------------------------------------------------------------------
fontes = rng.choice(NOMES_FONTES, size=N_OCORRENCIAS, p=PESOS_FONTES)
tipos_fonte = np.array([FONTES[f][0] for f in fontes], dtype=object)
automatica = tipos_fonte == "AUTOMATICA"

# Ponto monitorado: sensores tem ponto fixo, canais humanos nao
id_ponto = np.where(
    automatica,
    [f"POU-{rng.integers(1000, 1400)}" for _ in range(N_OCORRENCIAS)],
    "NAO APLICAVEL")


# ---------------------------------------------------------------------------
# 5. CRITICIDADE E SCORE DE PRIORIDADE
# ---------------------------------------------------------------------------
# Criticidade sobe com chuva nas categorias sensiveis (P2)
criticidade = rng.integers(1, 6, N_OCORRENCIAS).astype(float)
sensivel = np.array([CATEGORIAS[c][4] for c in categorias])
criticidade = np.where(sensivel & (chuva > 15), np.clip(criticidade + 1, 1, 5), criticidade)
criticidade = criticidade.astype(int)

pessoas_afetadas = np.maximum(
    1, (densidade / 1000 * rng.gamma(2.0, 3.0, N_OCORRENCIAS)).astype(int))

# Score 0-100: formula herdada da RN06 do UrbanIQ (criticidade + impacto + urgencia)
score = (criticidade * 12
         + np.clip(pessoas_afetadas, 0, 60) * 0.45
         + (100 / sla_previsto) * 1.8
         + rng.normal(0, 7, N_OCORRENCIAS))
score_prioridade = np.clip(np.round(score), 0, 100).astype(int)


# ---------------------------------------------------------------------------
# 6. TEMPOS (P1 e P4) + N1 (despacho NAO olha o score)
# ---------------------------------------------------------------------------
fator_reg = np.array([FATOR_REGIAO[r] for r in regioes])

# N1: o lag de despacho e praticamente independente do score de prioridade.
# Esse e o achado critico: o motor prioriza, mas a operacao despacha por ordem
# de chegada. A correlacao esperada aqui e quase nula.
lag_despacho_min = np.round(rng.lognormal(mean=3.1, sigma=0.75, size=N_OCORRENCIAS)
                            * fator_reg).astype(int)

# P1: deteccao automatica chega muito mais rapido ao local
base_deslocamento = np.where(
    automatica,
    rng.lognormal(mean=2.95, sigma=0.52, size=N_OCORRENCIAS),   # ~19 min
    rng.lognormal(mean=3.95, sigma=0.62, size=N_OCORRENCIAS))   # ~52 min
deslocamento_min = np.round(base_deslocamento * fator_reg).astype(int)

tempo_resposta_min = lag_despacho_min + deslocamento_min

dt_despacho = dt_abertura + pd.to_timedelta(lag_despacho_min, unit="m")
dt_chegada = dt_despacho + pd.to_timedelta(deslocamento_min, unit="m")

# Tempo de resolucao: proporcional ao SLA da categoria, penalizado pela regiao
fator_exec = rng.lognormal(mean=-0.28, sigma=0.60, size=N_OCORRENCIAS)
tempo_resolucao_h = np.round(sla_previsto * fator_exec * fator_reg, 2)
tempo_resolucao_h = np.maximum(tempo_resolucao_h, 0.5)

# Status: 78% finalizadas
sorteio_status = rng.random(N_OCORRENCIAS)
status = np.where(sorteio_status < 0.62, "ENCERRADO",
         np.where(sorteio_status < 0.78, "RESOLVIDO",
         np.where(sorteio_status < 0.88, "EM_ATENDIMENTO",
         np.where(sorteio_status < 0.95, "EM_ANALISE", "ABERTO"))))
finalizada = np.isin(status, ["ENCERRADO", "RESOLVIDO"])

tempo_resolucao_h = np.where(finalizada, tempo_resolucao_h, np.nan)
dt_encerramento = pd.Series(pd.NaT, index=range(N_OCORRENCIAS))
dt_encerramento[finalizada] = (
    dt_abertura[finalizada] + pd.to_timedelta(tempo_resolucao_h[finalizada], unit="h"))

sla_cumprido = np.where(~finalizada, "EM ABERTO",
                        np.where(tempo_resolucao_h <= sla_previsto, "SIM", "NAO"))


# ---------------------------------------------------------------------------
# 7. SATISFACAO (P3) e CUSTO (N3)
# ---------------------------------------------------------------------------
# P3: satisfacao cai com o tempo de resposta e com o estouro de SLA
razao_sla = np.where(finalizada, tempo_resolucao_h / sla_previsto, np.nan)
nota_bruta = (6.4
              - 0.62 * np.log1p(tempo_resposta_min)
              - 0.55 * np.nan_to_num(razao_sla, nan=0.0)
              + rng.normal(0, 0.62, N_OCORRENCIAS))
satisfacao = np.clip(np.round(nota_bruta), 1, 5)
# Somente finalizadas sao avaliadas, e nem todo cidadao responde
respondeu = finalizada & (rng.random(N_OCORRENCIAS) < 0.72)
satisfacao = np.where(respondeu, satisfacao, np.nan)

# N3: custo operacional sem relacao com satisfacao, so com categoria e duracao
custo = np.round(
    rng.gamma(2.4, 420, N_OCORRENCIAS) * (1 + sla_previsto / 120)
    + np.nan_to_num(tempo_resolucao_h, nan=0.0) * rng.uniform(6, 22, N_OCORRENCIAS), 2)

# Reincidencia: mais provavel em bairros densos
prob_reinc = np.clip(densidade / 26000, 0.05, 0.5)
reincidencia = np.where(rng.random(N_OCORRENCIAS) < prob_reinc, "SIM", "NAO")


# ---------------------------------------------------------------------------
# 8. MONTAGEM DO DATAFRAME
# ---------------------------------------------------------------------------
df = pd.DataFrame({
    "id_ocorrencia": np.arange(1, N_OCORRENCIAS + 1),
    "id_ponto_monitorado": id_ponto,
    "fonte_dado": fontes,
    "tipo_fonte": tipos_fonte,
    "dt_abertura": dt_abertura,
    "dt_despacho": dt_despacho,
    "dt_chegada_equipe": dt_chegada,
    "dt_encerramento": dt_encerramento.values,
    "regiao": regioes,
    "bairro": bairros,
    "densidade_hab_km2": densidade,
    "latitude": latitude,
    "longitude": longitude,
    "categoria": categorias,
    "subcategoria": subcategorias,
    "criticidade_sensor": criticidade,
    "score_prioridade": score_prioridade,
    "sla_horas_previsto": sla_previsto.astype(int),
    "tempo_resposta_min": tempo_resposta_min,
    "tempo_resolucao_horas": np.round(tempo_resolucao_h, 2),
    "sla_cumprido": sla_cumprido,
    "status_ocorrencia": status,
    "equipe_acionada": equipes,
    "qtd_pessoas_afetadas": pessoas_afetadas,
    "custo_operacional_reais": custo,
    "satisfacao_cidadao": satisfacao,
    "reincidencia_30d": reincidencia,
    "temperatura_c": temperatura,
    "chuva_mm": chuva,
}).sort_values("dt_abertura").reset_index(drop=True)

df_limpo_referencia = df.copy()   # guardado so para o relatorio de validacao


# ---------------------------------------------------------------------------
# 9. DEFEITOS PLANTADOS (materia-prima do 1o Desafio)
# ---------------------------------------------------------------------------
def plantar_defeitos(df):
    """Injeta problemas de qualidade realistas e documentados.

    Cada bloco simula uma falha operacional plausivel do mundo real, e nao
    ruido aleatorio sem historia.
    """
    df = df.copy()
    n = len(df)
    relatorio = {}

    # (a) Bairro nao informado: chamado aberto por telefone sem confirmar endereco
    idx = rng.choice(n, 120, replace=False)
    df.loc[idx, "bairro"] = np.nan
    relatorio["bairro nulo"] = 120

    # (b) Satisfacao fora da escala 1-5: falha de integracao da pesquisa
    idx = rng.choice(df.index[df["satisfacao_cidadao"].notna()], 40, replace=False)
    df.loc[idx, "satisfacao_cidadao"] = 9
    relatorio["satisfacao = 9 (fora da escala)"] = 40

    # (c) Satisfacao nula extra: pesquisa nao enviada por erro de sistema
    idx = rng.choice(df.index[df["satisfacao_cidadao"].notna()], 60, replace=False)
    df.loc[idx, "satisfacao_cidadao"] = np.nan
    relatorio["satisfacao nula por falha de envio"] = 60

    # (d) Tempo de resposta negativo: relogio do dispositivo dessincronizado
    idx = rng.choice(n, 30, replace=False)
    df.loc[idx, "tempo_resposta_min"] = -df.loc[idx, "tempo_resposta_min"]
    relatorio["tempo_resposta negativo"] = 30

    # (e) Score sentinela 999: valor default nao tratado na integracao
    idx = rng.choice(n, 50, replace=False)
    df.loc[idx, "score_prioridade"] = 999
    relatorio["score_prioridade = 999"] = 50

    # (f) Encerramento anterior a abertura: data digitada manualmente
    idx = rng.choice(df.index[df["dt_encerramento"].notna()], 25, replace=False)
    df.loc[idx, "dt_encerramento"] = df.loc[idx, "dt_abertura"] - pd.Timedelta(hours=5)
    relatorio["dt_encerramento < dt_abertura"] = 25

    # (g) Data de abertura no futuro: fuso horario mal configurado no sensor
    idx = rng.choice(n, 20, replace=False)
    df.loc[idx, "dt_abertura"] = DATA_FIM + pd.Timedelta(days=400)
    relatorio["dt_abertura no futuro"] = 20

    # (h) Padronizacao de texto: cada canal grava a fonte de um jeito
    idx = rng.choice(n, 300, replace=False)
    variacoes = {"APP_MOBILE": " app_mobile ", "PORTAL_WEB": "Portal Web",
                 "TELEFONE_156": "telefone 156", "SENSOR_IOT": "Sensor_IoT",
                 "CAMERA_HD": " camera hd"}
    df.loc[idx, "fonte_dado"] = df.loc[idx, "fonte_dado"].map(
        lambda v: variacoes.get(v, v))
    relatorio["fonte_dado sem padronizacao"] = 300

    # (i) Outliers absurdos de custo: erro de digitacao em ordem de servico
    idx = rng.choice(n, 3, replace=False)
    df.loc[idx, "custo_operacional_reais"] = 9_999_999.99
    relatorio["custo_operacional absurdo"] = 3

    # (j) Duplicatas exatas: reenvio do lote de integracao
    idx = rng.choice(n, 180, replace=False)
    df = pd.concat([df, df.loc[idx]], ignore_index=True)
    relatorio["linhas duplicadas"] = 180

    return df.sample(frac=1, random_state=SEMENTE).reset_index(drop=True), relatorio


df_bruto, relatorio_defeitos = plantar_defeitos(df)


# ---------------------------------------------------------------------------
# 10. DICIONARIO DE DADOS
# ---------------------------------------------------------------------------
DICIONARIO = [
    ("id_ocorrencia", "Identificador unico da ocorrencia registrada no COU"),
    ("id_ponto_monitorado", "Ponto fixo de monitoramento (apenas fontes automaticas)"),
    ("fonte_dado", "Canal de origem: APP_MOBILE, PORTAL_WEB, TELEFONE_156, SENSOR_IOT, CAMERA_HD"),
    ("tipo_fonte", "CIDADAO (registro humano) ou AUTOMATICA (sensor ou camera)"),
    ("dt_abertura", "Data e hora do registro da ocorrencia"),
    ("dt_despacho", "Data e hora do acionamento da equipe responsavel"),
    ("dt_chegada_equipe", "Data e hora da chegada da equipe ao local"),
    ("dt_encerramento", "Data e hora do encerramento (nulo se ainda em aberto)"),
    ("regiao", "Regiao da cidade Alfa: Centro, Norte, Sul, Leste ou Oeste"),
    ("bairro", "Bairro da ocorrencia"),
    ("densidade_hab_km2", "Densidade populacional do bairro em habitantes por km2"),
    ("latitude", "Latitude do ponto da ocorrencia"),
    ("longitude", "Longitude do ponto da ocorrencia"),
    ("categoria", "Categoria do problema urbano"),
    ("subcategoria", "Detalhamento do problema dentro da categoria"),
    ("criticidade_sensor", "Criticidade avaliada na deteccao, escala de 1 a 5"),
    ("score_prioridade", "Score de priorizacao do UrbanIQ, de 0 a 100 (RN06)"),
    ("sla_horas_previsto", "Prazo de atendimento acordado para a categoria, em horas"),
    ("tempo_resposta_min", "Minutos entre a abertura e a chegada da equipe ao local"),
    ("tempo_resolucao_horas", "Horas entre a abertura e o encerramento da ocorrencia"),
    ("sla_cumprido", "SIM, NAO ou EM ABERTO, conforme o prazo previsto"),
    ("status_ocorrencia", "ABERTO, EM_ANALISE, EM_ATENDIMENTO, RESOLVIDO ou ENCERRADO"),
    ("equipe_acionada", "Equipe operacional responsavel pelo atendimento"),
    ("qtd_pessoas_afetadas", "Estimativa de pessoas impactadas pela ocorrencia"),
    ("custo_operacional_reais", "Custo operacional estimado do atendimento, em reais"),
    ("satisfacao_cidadao", "Avaliacao do cidadao apos o encerramento, escala de 1 a 5"),
    ("reincidencia_30d", "Indica ocorrencia do mesmo tipo no bairro nos ultimos 30 dias"),
    ("temperatura_c", "Temperatura media do dia, em graus Celsius"),
    ("chuva_mm", "Precipitacao acumulada no dia, em milimetros"),
]
df_dicionario = pd.DataFrame(DICIONARIO, columns=["Coluna", "Descricao"])


# ---------------------------------------------------------------------------
# 11. GRAVACAO
# ---------------------------------------------------------------------------
with pd.ExcelWriter(ARQUIVO_SAIDA, engine="openpyxl") as writer:
    df_bruto.to_excel(writer, sheet_name="dados", index=False)
    df_dicionario.to_excel(writer, sheet_name="dicionario_dados", index=False)

print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
print(f"Dimensao final: {df_bruto.shape[0]} linhas x {df_bruto.shape[1]} colunas\n")
print("Defeitos plantados:")
for k, v in relatorio_defeitos.items():
    print(f"  {k:.<42} {v}")
