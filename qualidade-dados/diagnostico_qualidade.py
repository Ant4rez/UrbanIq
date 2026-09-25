"""
UrbanIQ — Diagnóstico de Qualidade de Dados
===========================================

Audita os dados do repositório contra o modelo físico Oracle (fase 2):

  * fase3-ingestao/data/raw/*.csv           (10 tabelas de cadastro)
  * dashboards/powerbi/dados/tb_chamado_v3.csv (1.000 chamados do dashboard)

As regras estruturais (tipos, tamanhos, NOT NULL, PK, UNIQUE, FK, CHECK) são
lidas diretamente dos scripts DDL — se o DDL mudar, o diagnóstico acompanha.
As regras de negócio (datas, SLA, score, geografia) estão codificadas abaixo.

Saídas (na mesma pasta deste script):
  * achados.csv                    — uma linha por problema encontrado
  * relatorio-qualidade-dados.md   — relatório completo em Markdown

Uso:
    python qualidade-dados/diagnostico_qualidade.py

Determinístico: a "data de corte" é a maior DT_ABERTURA do dataset, não a
data de hoje — rodar duas vezes gera exatamente as mesmas saídas.
"""

import importlib.util
import math
import re
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd

# ============================================================================
# CAMINHOS
# ============================================================================

PASTA = Path(__file__).resolve().parent
ROOT = PASTA.parent

DIR_RAW = ROOT / "fase3-ingestao" / "data" / "raw"
CSV_CHAMADO = ROOT / "dashboards" / "powerbi" / "dados" / "tb_chamado_v3.csv"
GERADOR = ROOT / "dashboards" / "powerbi" / "dados" / "gerar_dados_expandidos.py"
DDLS = [
    ROOT / "fase2-modelagem" / "relacional" / "ddl" / "urbaniq-ddl.sql",
    ROOT / "fase2-modelagem" / "relacional" / "ddl" / "urbaniq-ddl-patch-v2.sql",
]

SAIDA_CSV = PASTA / "achados.csv"
SAIDA_MD = PASTA / "relatorio-qualidade-dados.md"

# ============================================================================
# PARÂMETROS DAS REGRAS DE NEGÓCIO
# ============================================================================

STATUS_FINAIS = {"RESOLVIDO", "ENCERRADO"}
IDADE_MIN, IDADE_MAX = 16, 110
DIST_MAX_BAIRRO_KM = 5.0
BACKLOG_DIAS = 90

UFS = {
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
}
ZONAS = {"Norte", "Sul", "Leste", "Oeste", "Centro"}

# Centroides aproximados dos bairros de São Paulo presentes em tb_bairro
# (referência pública, precisão de ~1 km — suficiente para limiar de 5 km)
CENTROIDE_BAIRRO = {
    "Vila Madalena": (-23.5560, -46.6910),
    "Pinheiros": (-23.5670, -46.7020),
    "Itaquera": (-23.5400, -46.4560),
    "Mooca": (-23.5600, -46.5990),
    "Vila Prudente": (-23.5830, -46.5810),
    "Santana": (-23.5020, -46.6250),
    "Penha": (-23.5270, -46.5430),
    "Campo Belo": (-23.6260, -46.6680),
    "Ipiranga": (-23.5900, -46.6070),
    "Centro Histórico": (-23.5500, -46.6340),
}

ORDEM_SEVERIDADE = {"Alta": 0, "Média": 1, "Baixa": 2}

# ============================================================================
# ESTRUTURA DE RESULTADO
# ============================================================================


@dataclass
class Verificacao:
    dimensao: str
    tabela: str
    coluna: str
    regra: str
    severidade: str
    qtd_afetada: int
    total: int
    exemplo: str
    recomendacao: str

    @property
    def pct(self):
        return round(self.qtd_afetada / self.total * 100, 1) if self.total else 0.0


VERIFICACOES: list[Verificacao] = []


def registrar(dimensao, tabela, coluna, regra, severidade, mascara_ou_qtd,
              total, exemplos=None, recomendacao=""):
    """Registra uma verificação (com ou sem falha). Exemplos: lista/Series."""
    if isinstance(mascara_ou_qtd, pd.Series):
        qtd = int(mascara_ou_qtd.sum())
    else:
        qtd = int(mascara_ou_qtd)
    if exemplos is None:
        exemplos = []
    exemplos = [str(e) for e in list(exemplos)[:3]]
    VERIFICACOES.append(Verificacao(
        dimensao, tabela, coluna, regra, severidade, qtd, int(total),
        " | ".join(exemplos) if qtd else "", recomendacao,
    ))


# ============================================================================
# LEITURA DO DDL
# ============================================================================

RE_COLUNA = re.compile(
    r"^\s+(\w+)\s+(NUMBER|VARCHAR2|CHAR|DATE)(?:\((\d+)(?:,(\d+))?\))?(.*)$"
)


def _blocos_create(sql):
    """Retorna {tabela: corpo} para cada CREATE TABLE, respeitando parênteses."""
    blocos = {}
    for m in re.finditer(r"CREATE TABLE (\w+) \(", sql):
        i, nivel = m.end(), 1
        while nivel:
            nivel += {"(": 1, ")": -1}.get(sql[i], 0)
            i += 1
        blocos[m.group(1)] = sql[m.end():i - 1]
    return blocos


def _constraints(tabela, corpo, modelo):
    t = modelo[tabela]
    for m in re.finditer(r"PRIMARY KEY \(([^)]*)\)", corpo):
        t["pk"] = [c.strip() for c in m.group(1).split(",")]
    for m in re.finditer(r"UNIQUE \(([^)]*)\)", corpo):
        t["unique"].append([c.strip() for c in m.group(1).split(",")])
    for m in re.finditer(r"FOREIGN KEY \((\w+)\)\s*REFERENCES (\w+) \((\w+)\)", corpo):
        t["fk"].append((m.group(1), m.group(2), m.group(3)))
    for m in re.finditer(r"CHECK \((\w+) IN\s*\(([^)]*)\)\)", corpo):
        valores = [v.strip().strip("'") for v in m.group(2).split(",")]
        t["check_in"][m.group(1)] = valores
    for m in re.finditer(r"CHECK \((\w+)\s+BETWEEN\s+(-?\d+)\s+AND\s+(-?\d+)\)", corpo):
        t["check_between"][m.group(1)] = (float(m.group(2)), float(m.group(3)))


def ler_modelo():
    """Monta o modelo físico (DDL original + patch v2) como dicionário."""
    modelo = {}
    for ddl in DDLS:
        sql = ddl.read_text(encoding="utf-8")
        sql = re.sub(r"--[^\n]*", "", sql)  # remove comentários

        for tabela, corpo in _blocos_create(sql).items():
            modelo[tabela] = {"colunas": {}, "pk": [], "unique": [], "fk": [],
                              "check_in": {}, "check_between": {}}
            for linha in corpo.splitlines():
                m = RE_COLUNA.match(linha)
                if m and m.group(1) != "CONSTRAINT":
                    modelo[tabela]["colunas"][m.group(1)] = {
                        "tipo": m.group(2),
                        "p": int(m.group(3)) if m.group(3) else None,
                        "s": int(m.group(4)) if m.group(4) else 0,
                        "not_null": "NOT NULL" in m.group(5),
                    }
            _constraints(tabela, corpo, modelo)

        # ALTER TABLE ... ADD ( colunas )
        for m in re.finditer(r"ALTER TABLE (\w+) ADD \((.*?)\);", sql, re.S):
            for linha in m.group(2).splitlines():
                mc = RE_COLUNA.match(linha)
                if mc:
                    modelo[m.group(1)]["colunas"][mc.group(1)] = {
                        "tipo": mc.group(2),
                        "p": int(mc.group(3)) if mc.group(3) else None,
                        "s": int(mc.group(4)) if mc.group(4) else 0,
                        "not_null": "NOT NULL" in mc.group(5),
                    }
        # ALTER TABLE ... ADD CONSTRAINT ...
        for m in re.finditer(r"ALTER TABLE (\w+)\s+ADD CONSTRAINT (.*?);", sql, re.S):
            _constraints(m.group(1), m.group(2), modelo)
    return modelo


# ============================================================================
# LEITURA DOS DADOS
# ============================================================================


def tabela_ddl(nome_csv):
    """tb_chamado_v3 -> T_URB_CHAMADO ; tb_canal_atendimento -> T_URB_CANAL_ATENDIMENTO"""
    base = re.sub(r"_v\d+$", "", nome_csv)
    return "T_URB_" + base.removeprefix("tb_").upper()


def ler_dados():
    """Lê tudo como texto: preserva o formato bruto (zeros à esquerda, etc.)."""
    dados = {}
    for arq in sorted(DIR_RAW.glob("*.csv")):
        dados[arq.stem] = pd.read_csv(arq, dtype=str, keep_default_na=False).replace("", pd.NA)
    dados["tb_chamado_v3"] = pd.read_csv(CSV_CHAMADO, dtype=str, keep_default_na=False).replace("", pd.NA)
    return dados


def carregar_gerador():
    """Importa as constantes do gerador sintético (main() não é executado)."""
    spec = importlib.util.spec_from_file_location("gerador", GERADOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ============================================================================
# AUXILIARES DE VALIDAÇÃO
# ============================================================================


def cpf_valido(cpf):
    if not isinstance(cpf, str) or not re.fullmatch(r"\d{11}", cpf) or len(set(cpf)) == 1:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        dv = (soma * 10) % 11 % 10
        if dv != int(cpf[n]):
            return False
    return True


def sem_acento(txt):
    return "".join(c for c in unicodedata.normalize("NFKD", txt) if not unicodedata.combining(c))


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def exemplos(df, mascara, colunas, n=3):
    linhas = df.loc[mascara, colunas].head(n)
    return [", ".join(f"{c}={v}" for c, v in zip(colunas, row)) for row in linhas.itertuples(index=False)]


# ============================================================================
# 1. VERIFICAÇÕES ESTRUTURAIS (derivadas do DDL)
# ============================================================================


def verificar_estrutura(dados, modelo):
    for nome, df in dados.items():
        tab = tabela_ddl(nome)
        if tab not in modelo:
            registrar("Consistência entre artefatos", nome, "-", "Tabela existe no DDL",
                      "Alta", 1, 1, [tab], "Criar a tabela no DDL ou remover o CSV.")
            continue
        cols_ddl = modelo[tab]["colunas"]

        # --- colunas CSV x DDL
        extras = [c for c in df.columns if c not in cols_ddl]
        registrar("Consistência entre artefatos", nome, ", ".join(extras) or "-",
                  f"Colunas do CSV existem em {tab}", "Alta", len(extras), len(df.columns), extras,
                  "Coluna sem destino no modelo físico: a carga no Oracle vai descartá-la ou falhar. "
                  "Adicionar a coluna ao DDL (patch v3) ou mapear para a tabela correta.")
        faltando_nn = [c for c, d in cols_ddl.items() if c not in df.columns and d["not_null"]]
        registrar("Consistência entre artefatos", nome, ", ".join(faltando_nn) or "-",
                  f"Colunas NOT NULL de {tab} presentes no CSV", "Alta",
                  len(faltando_nn), len(cols_ddl), faltando_nn,
                  "Incluir a coluna obrigatória na extração.")

        for col, d in cols_ddl.items():
            if col not in df.columns:
                continue
            s = df[col]
            n = len(s)
            presentes = s.notna()

            # --- completude
            if d["not_null"]:
                registrar("Completude", nome, col, "NOT NULL", "Alta", s.isna(), n,
                          exemplos(df, s.isna(), df.columns[:1].tolist()),
                          "Preencher a coluna obrigatória ou revisar a regra NOT NULL.")
            elif s.isna().all():
                registrar("Completude", nome, col, "Coluna opcional 100% vazia", "Baixa",
                          n, n, ["todas as linhas vazias"],
                          "Coluna sem nenhum valor: confirmar se o dado existe na origem ou "
                          "retirá-la do modelo/visuais.")

            # --- tipo e tamanho
            if d["tipo"] == "NUMBER":
                num = pd.to_numeric(s, errors="coerce")
                invalido = presentes & num.isna()
                registrar("Validade", nome, col, f"Valor numérico (NUMBER({d['p']},{d['s']}))",
                          "Alta", invalido, n, s[invalido],
                          "Corrigir valores não numéricos antes da carga.")
                if d["p"]:
                    inteiros = s.str.replace("-", "", regex=False).str.split(".").str[0]
                    decimais = s.str.split(".").str[1].fillna("")
                    estouro = presentes & ((inteiros.str.len() > d["p"] - d["s"]) |
                                           (decimais.str.len() > d["s"]))
                    registrar("Validade", nome, col, f"Precisão cabe em NUMBER({d['p']},{d['s']})",
                              "Alta", estouro, n, s[estouro],
                              "Valor excede a precisão da coluna: ORA-01438 na carga.")
            elif d["tipo"] == "DATE":
                dt = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
                invalido = presentes & dt.isna()
                registrar("Validade", nome, col, "Data no formato AAAA-MM-DD", "Alta",
                          invalido, n, s[invalido], "Padronizar datas em ISO 8601.")
            else:  # VARCHAR2 / CHAR — Oracle mede em BYTES por padrão
                nbytes = s.fillna("").map(lambda v: len(v.encode("utf-8")))
                estouro = nbytes > d["p"]
                registrar("Validade", nome, col, f"Tamanho cabe em {d['tipo']}({d['p']}) (bytes UTF-8)",
                          "Alta", estouro, n, s[estouro],
                          "Aumentar a coluna ou usar semântica CHAR (VARCHAR2(n CHAR)).")
                espacos = presentes & ((s != s.str.strip()) | s.str.contains("  ", regex=False))
                registrar("Validade", nome, col, "Sem espaços extras (início/fim/duplos)", "Baixa",
                          espacos, n, s[espacos].map(repr), "Aplicar trim na ingestão.")

        # --- PK / UNIQUE
        if modelo[tab]["pk"] and all(c in df.columns for c in modelo[tab]["pk"]):
            pk = modelo[tab]["pk"]
            dup = df.duplicated(pk, keep=False)
            registrar("Unicidade", nome, ", ".join(pk), "Chave primária única", "Alta", dup,
                      len(df), exemplos(df, dup, pk), "Remover/renumerar duplicatas.")
        for uk in modelo[tab]["unique"]:
            if all(c in df.columns for c in uk):
                dup = df[uk].notna().all(axis=1) & df.duplicated(uk, keep=False)
                registrar("Unicidade", nome, ", ".join(uk), "Restrição UNIQUE", "Alta", dup,
                          len(df), exemplos(df, dup, uk), "Resolver duplicatas na origem.")

        # --- CHECK
        for col, valores in modelo[tab]["check_in"].items():
            if col in df.columns:
                fora = df[col].notna() & ~df[col].isin(valores)
                registrar("Validade", nome, col, f"CHECK IN ({', '.join(valores)})", "Alta",
                          fora, len(df), df.loc[fora, col], "Mapear para um valor do domínio.")
        for col, (lo, hi) in modelo[tab]["check_between"].items():
            if col in df.columns:
                v = pd.to_numeric(df[col], errors="coerce")
                fora = v.notna() & ((v < lo) | (v > hi))
                registrar("Validade", nome, col, f"CHECK BETWEEN {lo:g} AND {hi:g}", "Alta",
                          fora, len(df), df.loc[fora, col], "Corrigir valor fora da faixa.")


def verificar_integridade(dados, modelo):
    por_tabela = {tabela_ddl(n): n for n in dados}
    referenciados = {}  # (tabela_pai, coluna) -> set de valores usados

    for tab, nome in por_tabela.items():
        if tab not in modelo:
            continue
        df = dados[nome]
        for col, tab_pai, col_pai in modelo[tab]["fk"]:
            if col not in df.columns or tab_pai not in por_tabela:
                continue
            pai = dados[por_tabela[tab_pai]]
            orfao = df[col].notna() & ~df[col].isin(pai[col_pai])
            registrar("Integridade referencial", nome, col,
                      f"FK → {por_tabela[tab_pai]}.{col_pai}", "Alta", orfao, len(df),
                      df.loc[orfao, col], "Criar o registro-pai ou corrigir a referência.")
            referenciados.setdefault((tab_pai, col_pai), set()).update(df[col].dropna())

    # Registros-pai nunca referenciados (cobertura)
    for (tab_pai, col_pai), usados in referenciados.items():
        nome_pai = por_tabela[tab_pai]
        pai = dados[nome_pai]
        sem_uso = ~pai[col_pai].isin(usados)
        rotulo = next((c for c in pai.columns if c.startswith(("NM_", "SG_"))), col_pai)
        registrar("Integridade referencial", nome_pai, col_pai,
                  "Registro-pai referenciado por ao menos um filho", "Baixa", sem_uso, len(pai),
                  pai.loc[sem_uso, rotulo],
                  "Cadastro sem uso: aparece em filtros/slicers do dashboard sem nenhum dado. "
                  "Completar a massa (ex.: logradouros/chamados para essas entidades) ou "
                  "documentar como cadastro de referência.")


# ============================================================================
# 2. VERIFICAÇÕES DE DOMÍNIO / FORMATO
# ============================================================================


def verificar_dominios(dados):
    cid = dados["tb_cidadao"]
    n = len(cid)

    cpf_ruim = ~cid["NR_CPF_CIDADAO"].map(cpf_valido)
    registrar("Validade", "tb_cidadao", "NR_CPF_CIDADAO", "CPF com dígitos verificadores válidos",
              "Média", cpf_ruim, n, cid.loc[cpf_ruim, "NR_CPF_CIDADAO"],
              "O DDL documenta 'CPF deve ser válido'. Gerar CPFs sintéticos com DV correto "
              "(qualquer validação na aplicação/ETL rejeitaria estes). Guardar como CHAR(11) — "
              "NUMBER(11) perde zeros à esquerda (CPFs iniciados por 0).")

    email_ruim = ~cid["DS_EMAIL"].fillna("").str.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
    registrar("Validade", "tb_cidadao", "DS_EMAIL", "E-mail em formato válido", "Média",
              email_ruim, n, cid.loc[email_ruim, "DS_EMAIL"], "Corrigir e-mails malformados.")

    def email_bate(row):
        local = re.sub(r"\d+$", "", str(row.DS_EMAIL).split("@")[0])
        nome = ".".join(sem_acento(str(row.NM_CIDADAO)).lower().split())
        return local == nome
    email_nome = ~cid.apply(email_bate, axis=1)
    registrar("Consistência", "tb_cidadao", "DS_EMAIL", "E-mail derivado do nome sem erro de transliteração",
              "Baixa", email_nome, n, exemplos(cid, email_nome, ["NM_CIDADAO", "DS_EMAIL"]),
              "Transliteração de acentos gerou grafia errada no e-mail (ex.: ú → o). "
              "Usar unicodedata.normalize('NFKD') no gerador.")

    for tab, col in (("tb_cidadao", "NR_TELEFONE"), ("tb_gestor", "NR_TELEFONE")):
        df = dados[tab]
        t = df[col].dropna()
        formato = ~t.str.fullmatch(r"\d{10,11}")
        registrar("Validade", tab, col, "Telefone só com dígitos, 10 ou 11 posições (DDD + número)",
                  "Média", formato, len(df), t[formato], "Padronizar como DDD + número, só dígitos.")
        celular_sem_9 = t.str.fullmatch(r"\d{2}9\d{7}")
        registrar("Validade", tab, col, "Celular com 9º dígito (11 posições)", "Média",
                  celular_sem_9, len(df), t[celular_sem_9],
                  "Número começa com 9 (celular) mas tem só 8 dígitos após o DDD — falta o "
                  "nono dígito, obrigatório desde 2016. Padronizar com o formato de tb_cidadao.")

    nasc = pd.to_datetime(cid["DT_NASCIMENTO"], errors="coerce")
    corte = pd.to_datetime(dados["tb_chamado_v3"]["DT_ABERTURA"]).max()
    idade = (corte - nasc).dt.days / 365.25
    idade_ruim = nasc.notna() & ((idade < IDADE_MIN) | (idade > IDADE_MAX))
    registrar("Consistência", "tb_cidadao", "DT_NASCIMENTO",
              f"Idade plausível ({IDADE_MIN}–{IDADE_MAX} anos na data de corte)", "Média",
              idade_ruim, n, cid.loc[idade_ruim, "DT_NASCIMENTO"], "Revisar data de nascimento.")

    log = dados["tb_logradouro"]
    cep_ruim = ~log["NR_CEP"].fillna("").str.fullmatch(r"\d{8}")
    registrar("Validade", "tb_logradouro", "NR_CEP", "CEP com 8 dígitos", "Média", cep_ruim,
              len(log), exemplos(log, cep_ruim, ["NM_LOGRADOURO", "NR_CEP"]),
              "CEPs da capital paulista começam com 0 (01000-000 a 05999-999; 08xxx-xxx) e o "
              "zero à esquerda foi perdido — o CSV foi exportado de uma coluna numérica. "
              "Trocar NR_CEP de NUMBER(8) para CHAR(8) no DDL e reexportar com zero à esquerda "
              "(ex.: 5422001 → 05422001). Sem isso, qualquer cruzamento com base de CEP (Correios/IBGE) falha.")

    est = dados["tb_estado"]
    uf_ruim = ~est["SG_ESTADO"].isin(UFS)
    registrar("Validade", "tb_estado", "SG_ESTADO", "UF válida", "Média", uf_ruim, len(est),
              est.loc[uf_ruim, "SG_ESTADO"], "Corrigir sigla.")

    bai = dados["tb_bairro"]
    zona_ruim = bai["NM_ZONA_BAIRRO"].notna() & ~bai["NM_ZONA_BAIRRO"].isin(ZONAS)
    registrar("Validade", "tb_bairro", "NM_ZONA_BAIRRO", f"Zona em {sorted(ZONAS)}", "Baixa",
              zona_ruim, len(bai), bai.loc[zona_ruim, "NM_ZONA_BAIRRO"],
              "Padronizar domínio (candidata a CHECK no DDL).")


# ============================================================================
# 3. REGRAS DE NEGÓCIO DO CHAMADO
# ============================================================================


def preparar_chamado(dados):
    c = dados["tb_chamado_v3"].copy()
    for col in ("DT_ABERTURA", "DT_PRAZO_ESTIMADO", "DT_RESOLUCAO"):
        c[col] = pd.to_datetime(c[col], errors="coerce")
    for col in ("NR_SCORE_PRIORIDADE", "NR_LATITUDE", "NR_LONGITUDE"):
        c[col] = pd.to_numeric(c[col], errors="coerce")
    sub = dados["tb_subcategoria"][["ID_SUBCATEGORIA", "ID_CATEGORIA", "NR_PRIORIDADE_BASE"]]
    c = c.merge(sub, on="ID_SUBCATEGORIA", how="left")
    c["NR_PRIORIDADE_BASE"] = pd.to_numeric(c["NR_PRIORIDADE_BASE"])
    geo = (dados["tb_logradouro"][["ID_LOGRADOURO", "ID_BAIRRO"]]
           .merge(dados["tb_bairro"][["ID_BAIRRO", "NM_BAIRRO", "ID_CIDADE"]], on="ID_BAIRRO"))
    c = c.merge(geo, on="ID_LOGRADOURO", how="left")
    c["ORIGEM"] = c["NR_CHAMADO"].astype(int).map(lambda x: "original" if x <= 50 else "sintético")
    return c


def verificar_chamado(c, dados, ger):
    n = len(c)
    corte = c["DT_ABERTURA"].max()
    tab = "tb_chamado_v3"
    ex = lambda m, cols: exemplos(c.assign(**{k: c[k].dt.date for k in c.select_dtypes("datetime")}), m, cols)

    m = c["DT_PRAZO_ESTIMADO"] < c["DT_ABERTURA"]
    registrar("Consistência temporal", tab, "DT_PRAZO_ESTIMADO", "Prazo ≥ abertura", "Alta", m, n,
              ex(m, ["NR_CHAMADO", "DT_ABERTURA", "DT_PRAZO_ESTIMADO"]), "Recalcular prazo.")

    m = c["DT_RESOLUCAO"] < c["DT_ABERTURA"]
    registrar("Consistência temporal", tab, "DT_RESOLUCAO", "Resolução ≥ abertura", "Alta", m, n,
              ex(m, ["NR_CHAMADO", "DT_ABERTURA", "DT_RESOLUCAO"]),
              "Tempo de resolução negativo distorce a média de SLA.")

    final = c["ST_CHAMADO"].isin(STATUS_FINAIS)
    m = ~final & c["DT_RESOLUCAO"].notna()
    registrar("Consistência", tab, "DT_RESOLUCAO", "Resolução só em status RESOLVIDO/ENCERRADO",
              "Alta", m, n, ex(m, ["NR_CHAMADO", "ST_CHAMADO", "DT_RESOLUCAO"]),
              "Limpar DT_RESOLUCAO ou corrigir o status.")
    m = final & c["DT_RESOLUCAO"].isna()
    registrar("Consistência", tab, "DT_RESOLUCAO", "Status RESOLVIDO/ENCERRADO tem data de resolução",
              "Alta", m, n, ex(m, ["NR_CHAMADO", "ST_CHAMADO"]),
              "Chamado finalizado sem data some do cálculo de SLA.")

    m = c["DT_RESOLUCAO"] > corte
    registrar("Consistência temporal", tab, "DT_RESOLUCAO",
              f"Resolução ≤ data de corte do dataset ({corte.date()})", "Média", m, n,
              ex(m, ["NR_CHAMADO", "DT_ABERTURA", "DT_RESOLUCAO"]),
              "O snapshot termina na última abertura, mas há resoluções registradas depois dela "
              "(datas 'do futuro' em relação à extração). No gerador, limitar DT_RESOLUCAO a DATA_MAX "
              "ou manter o chamado em EM_ATENDIMENTO quando a resolução cairia após o corte.")

    vencido = ~final & (c["DT_PRAZO_ESTIMADO"] < corte - pd.Timedelta(days=BACKLOG_DIAS))
    registrar("Plausibilidade", tab, "ST_CHAMADO",
              f"Chamado não finalizado com prazo vencido há > {BACKLOG_DIAS} dias", "Média",
              vencido, n, ex(vencido, ["NR_CHAMADO", "ST_CHAMADO", "DT_ABERTURA"]),
              "O gerador sorteia o status independentemente da data de abertura: chamados de "
              "2024–início de 2025 continuam ABERTO/EM_ANALISE, enquanto a proporção de finalizados "
              "não cresce com a idade. Isso infla o backlog e o % de atraso no dashboard. Tornar a "
              "probabilidade de status final crescente com a idade do chamado.")

    # Score coerente com a prioridade-base da subcategoria (faixas do gerador)
    faixa = c["NR_PRIORIDADE_BASE"].map(ger.FAIXA_SCORE_POR_PRIORIDADE_BASE)
    lo, hi = faixa.str[0], faixa.str[1]
    m = (c["NR_SCORE_PRIORIDADE"] < lo) | (c["NR_SCORE_PRIORIDADE"] > hi)
    registrar("Consistência", tab, "NR_SCORE_PRIORIDADE",
              "Score dentro da faixa esperada para a prioridade-base da subcategoria", "Média", m, n,
              ex(m, ["NR_CHAMADO", "ID_SUBCATEGORIA", "NR_PRIORIDADE_BASE", "NR_SCORE_PRIORIDADE"]),
              "Score incompatível com a criticidade da subcategoria (ex.: pichação com score de "
              "risco imediato). Revisar o score dos chamados originais ou a subcategoria atribuída.")

    # Prazo (SLA) coerente com a prioridade-base
    faixas_prazo = {5: (1, 3), 4: (3, 7), 3: (7, 15), 2: (15, 30), 1: (30, 60)}
    dias = (c["DT_PRAZO_ESTIMADO"] - c["DT_ABERTURA"]).dt.days
    fp = c["NR_PRIORIDADE_BASE"].map(faixas_prazo)
    m = (dias < fp.str[0]) | (dias > fp.str[1])
    registrar("Consistência", tab, "DT_PRAZO_ESTIMADO",
              "Prazo (dias) dentro do SLA da prioridade-base (5→1–3d … 1→30–60d)", "Baixa", m, n,
              ex(m, ["NR_CHAMADO", "NR_PRIORIDADE_BASE", "DT_ABERTURA", "DT_PRAZO_ESTIMADO"]),
              "Prazo fora da regra usada no gerador. Formalizar a tabela de SLA por prioridade "
              "(hoje ela só existe dentro do script) e recalcular.")

    # Geografia: ponto do chamado x bairro do logradouro
    def dist(row):
        cen = CENTROIDE_BAIRRO.get(row.NM_BAIRRO)
        if cen is None or pd.isna(row.NR_LATITUDE):
            return float("nan")
        return haversine_km(row.NR_LATITUDE, row.NR_LONGITUDE, *cen)
    c["DIST_BAIRRO_KM"] = c.apply(dist, axis=1)
    m = c["DIST_BAIRRO_KM"] > DIST_MAX_BAIRRO_KM
    c_ex = c.assign(DIST_BAIRRO_KM=c["DIST_BAIRRO_KM"].round(1))
    registrar("Consistência", tab, "NR_LATITUDE, NR_LONGITUDE",
              f"Coordenada a ≤ {DIST_MAX_BAIRRO_KM:g} km do bairro do logradouro", "Média", m, n,
              exemplos(c_ex, m, ["NR_CHAMADO", "NM_BAIRRO", "DIST_BAIRRO_KM"]),
              "Lat/long é sorteada num retângulo fixo, sem relação com o logradouro informado — "
              "o mapa mostra um chamado da 'Rua Aspicuelta' em Itaquera. Além disso, o retângulo "
              "do gerador (lat −23,59 a −23,54) exclui Santana e Campo Belo inteiros. Gerar o ponto "
              "com jitter em torno do centroide do bairro/logradouro.")

    # Diversidade de descrições (impacta NLP nas fases 6/7)
    dup = c.duplicated("DS_CHAMADO", keep=False)
    registrar("Unicidade", tab, "DS_CHAMADO", "Descrição do chamado não repetida", "Média", dup, n,
              c.loc[dup, "DS_CHAMADO"].value_counts().head(3).index,
              f"Só {c['DS_CHAMADO'].nunique()} textos distintos em {n} chamados, e os sintéticos "
              "usam frases genéricas por prioridade (não citam o problema). Inviabiliza "
              "classificação de texto/NLP e deixa a descrição sem valor analítico. Gerar texto "
              "a partir da subcategoria (templates por subcategoria + variações).")

    # Continuidade da série temporal
    mensal = c.groupby(c["DT_ABERTURA"].dt.to_period("M")).size()
    todos = pd.period_range(mensal.index.min(), mensal.index.max(), freq="M")
    mensal = mensal.reindex(todos, fill_value=0)
    fracos = mensal[mensal < mensal.median() * 0.2]
    registrar("Plausibilidade", tab, "DT_ABERTURA",
              "Volume mensal contínuo (≥ 20% da mediana)", "Média", len(fracos), len(mensal),
              [f"{p}: {v}" for p, v in fracos.items()],
              "Antes de dez/2024 só existem chamados originais (0–4 por mês); os 950 sintéticos "
              "entram a partir de dez/2024 com ~70/mês. Gráficos de tendência mostram um 'salto' artificial. "
              "Filtrar o dashboard a partir de dez/2024 ou estender a janela do gerador.")

    return c


def verificar_artefatos(dados, modelo, ger):
    # Gerador x cadastro de subcategorias
    sub = dados["tb_subcategoria"]
    mapa_csv = dict(zip(sub["ID_SUBCATEGORIA"].astype(int), sub["NR_PRIORIDADE_BASE"].astype(int)))
    div = [f"sub {k}: gerador={v}, csv={mapa_csv.get(k)}"
           for k, v in ger.PRIORIDADE_BASE_POR_SUBCAT.items() if mapa_csv.get(k) != v]
    registrar("Consistência entre artefatos", "gerar_dados_expandidos.py", "PRIORIDADE_BASE_POR_SUBCAT",
              "Prioridade-base do gerador = tb_subcategoria", "Alta", len(div), len(mapa_csv), div,
              "Ler a prioridade de tb_subcategoria.csv em vez de manter cópia fixa no script.")

    origem_existe = Path(ger.CSV_ORIGEM).exists()
    registrar("Consistência entre artefatos", "gerar_dados_expandidos.py", "CSV_ORIGEM",
              "Arquivo de entrada do gerador existe no repositório", "Média",
              0 if origem_existe else 1, 1,
              [Path(ger.CSV_ORIGEM).relative_to(ROOT).as_posix()],
              "O gerador lê tb_chamado_v2.csv (50 chamados originais), que não está versionado: "
              "o tb_chamado_v3.csv não pode ser reproduzido. Versionar o v2 (ex.: em "
              "fase3-ingestao/data/raw/) e corrigir o caminho, que contém crase (\"CSV`s\").")

    sem_csv = sorted(t for t in modelo if t not in {tabela_ddl(n) for n in dados})
    registrar("Consistência entre artefatos", "DDL", "-",
              "Toda tabela do modelo tem massa de dados", "Baixa", len(sem_csv), len(modelo), sem_csv,
              "Sem histórico de status, atendimentos, avaliações e overrides não é possível medir "
              "RN05/RN06 nem calcular SLA pelo caminho do modelo (T_URB_ATENDIMENTO.DT_CONCLUSAO). "
              "Priorizar T_URB_HISTORICO_STATUS e T_URB_ATENDIMENTO na próxima massa.")

    inativos = {
        "tb_subcategoria": ("ID_SUBCATEGORIA", sub),
        "tb_canal_atendimento": ("ID_CANAL", dados["tb_canal_atendimento"]),
    }
    ch = dados["tb_chamado_v3"]
    for nome, (col, df) in inativos.items():
        ids_inativos = df.loc[df["ST_ATIVO"] == "N", col]
        m = ch[col].isin(ids_inativos)
        registrar("Consistência", "tb_chamado_v3", col, f"Chamado não usa {nome} inativo (RN02)",
                  "Média", m, len(ch), ch.loc[m, "NR_CHAMADO"], "Reclassificar chamado.")


# ============================================================================
# 4. PERFIL DESCRITIVO
# ============================================================================


def perfil(c, dados):
    corte = c["DT_ABERTURA"].max()
    final = c[c["ST_CHAMADO"].isin(STATUS_FINAIS)]
    no_prazo = (final["DT_RESOLUCAO"] <= final["DT_PRAZO_ESTIMADO"]).mean() * 100
    tempo = (final["DT_RESOLUCAO"] - final["DT_ABERTURA"]).dt.days

    canal = dados["tb_canal_atendimento"].set_index("ID_CANAL")["NM_CANAL"]
    cat = dados["tb_categoria"].set_index("ID_CATEGORIA")["NM_CATEGORIA"]

    c = c.assign(IDADE=pd.cut((corte - c["DT_ABERTURA"]).dt.days,
                              [-1, 90, 180, 365, 10_000],
                              labels=["≤ 90 d", "91–180 d", "181–365 d", "> 365 d"]))
    pct_final_idade = (c.groupby("IDADE", observed=True)["ST_CHAMADO"]
                       .apply(lambda s: s.isin(STATUS_FINAIS).mean() * 100).round(1))

    return {
        "linhas": {n: len(df) for n, df in dados.items()},
        "corte": corte.date(),
        "periodo": (c["DT_ABERTURA"].min().date(), corte.date()),
        "status": c["ST_CHAMADO"].value_counts(),
        "canal": c["ID_CANAL"].map(canal).value_counts(),
        "categoria": c["ID_CATEGORIA"].map(cat).value_counts(),
        "origem": c["ORIGEM"].value_counts(),
        "score_prior": c.groupby("NR_PRIORIDADE_BASE")["NR_SCORE_PRIORIDADE"]
                        .agg(["count", "min", "median", "max"]),
        # Spearman = Pearson sobre os postos (dispensa scipy)
        "corr_score": c["NR_SCORE_PRIORIDADE"].rank().corr(c["NR_PRIORIDADE_BASE"].rank()),
        "no_prazo": no_prazo,
        "tempo_med": tempo.median(),
        "pct_final_idade": pct_final_idade,
    }


# ============================================================================
# 5. RELATÓRIO
# ============================================================================


def md_tabela(df):
    cols = list(df.columns)
    linhas = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        linhas.append("| " + " | ".join(str(v).replace("|", "\\|") for v in row) + " |")
    return "\n".join(linhas)


def serie_md(s, nome, valor="Qtd"):
    return md_tabela(s.rename_axis(nome).reset_index(name=valor))


def gerar_relatorio(achados, todas, p):
    sev = achados["severidade"].value_counts().reindex(["Alta", "Média", "Baixa"], fill_value=0)

    placar_dim = (todas.assign(ok=todas["qtd_afetada"] == 0)
                  .groupby("dimensao").agg(verificacoes=("ok", "size"), aprovadas=("ok", "sum")))
    placar_dim["reprovadas"] = placar_dim["verificacoes"] - placar_dim["aprovadas"]
    placar_dim["% aprovação"] = (placar_dim["aprovadas"] / placar_dim["verificacoes"] * 100).round(0).astype(int)
    placar_dim = placar_dim.reset_index().rename(columns={
        "dimensao": "Dimensão", "verificacoes": "Verificações",
        "aprovadas": "Aprovadas", "reprovadas": "Reprovadas"})

    # Regras que, se violadas, derrubam o INSERT no Oracle
    regras_carga = r"NOT NULL|Chave primária|UNIQUE|FK →|CHECK|NUMBER|Tamanho cabe|Data no formato"
    bloqueios = achados[achados["regra"].str.contains(regras_carga)]

    placar_tab = (achados.groupby(["tabela", "severidade"]).size().unstack(fill_value=0)
                  .reindex(columns=["Alta", "Média", "Baixa"], fill_value=0))
    placar_tab["Total"] = placar_tab.sum(axis=1)
    placar_tab = placar_tab.sort_values(["Alta", "Média", "Total"], ascending=False).reset_index()

    L = []
    L.append("# UrbanIQ — Diagnóstico de Qualidade de Dados\n")
    L.append("> Gerado automaticamente por `qualidade-dados/diagnostico_qualidade.py`. "
             "Não edite à mão — rode o script novamente.\n")
    L.append("## Escopo\n")
    L.append("| Fonte | Arquivo | Linhas |\n|---|---|---|")
    for nome, qtd in p["linhas"].items():
        arq = "dashboards/powerbi/dados/" if nome == "tb_chamado_v3" else "fase3-ingestao/data/raw/"
        L.append(f"| {nome} | `{arq}{nome}.csv` | {qtd} |")
    L.append("\n**Referência de 'correto':** DDL Oracle `urbaniq-ddl.sql` + `urbaniq-ddl-patch-v2.sql` "
             "(tipos, tamanhos, NOT NULL, PK, UNIQUE, FK e CHECK lidos automaticamente dos scripts) "
             "e regras de negócio do projeto (SLA, score, status, geografia).  ")
    L.append(f"**Data de corte:** {p['corte']} (maior `DT_ABERTURA`; usada no lugar de 'hoje' para "
             "o resultado ser determinístico).\n")

    L.append("## Resumo executivo\n")
    L.append(f"- **{len(todas)} verificações** executadas; **{len(achados)} reprovadas** "
             f"(🔴 {sev['Alta']} alta · 🟠 {sev['Média']} média · 🟡 {sev['Baixa']} baixa).")
    if bloqueios.empty:
        L.append("- **A carga no Oracle não falharia por tipo, domínio ou chave**: não há FK órfã, PK "
                 "duplicada, nulo em coluna obrigatória nem valor fora dos CHECKs. A estrutura básica está sólida.")
    else:
        L.append(f"- ⚠️ **{len(bloqueios)} regra(s) do DDL violada(s)** — a carga no Oracle falharia: "
                 + "; ".join(f"`{t}.{c}` ({r})" for t, c, r in
                             bloqueios[["tabela", "coluna", "regra"]].itertuples(index=False)) + ".")
    L.append("- Leitura dos achados desta execução — os problemas se concentram em três frentes:")
    L.append("  1. **Modelo × dado divergem** — `tb_chamado_v3` traz `DT_RESOLUCAO`, que não existe em "
             "`T_URB_CHAMADO`; o CEP perdeu o zero à esquerda por ser `NUMBER(8)`; o gerador do "
             "dataset depende de um arquivo que não está no repositório.")
    L.append("  2. **Realismo do dado sintético** — coordenadas sem relação com o logradouro, status "
             "independente da idade do chamado, descrições genéricas repetidas e resoluções "
             "posteriores à data de corte.")
    L.append("  3. **Formatos cadastrais** — CPFs com dígito verificador inválido e telefones de "
             "gestores sem o nono dígito.")
    L.append("- **Impacto direto nos KPIs do dashboard:** backlog e % de atraso inflados, mapa de "
             "ocorrências enganoso e série temporal com salto artificial em dez/2024.\n")

    L.append("## Placar por dimensão\n")
    L.append(md_tabela(placar_dim) + "\n")
    L.append("## Placar por tabela (achados)\n")
    L.append(md_tabela(placar_tab.rename(columns={"tabela": "Tabela"})) + "\n")

    L.append("## Achados priorizados\n")
    L.append("Severidade: **🔴 Alta** — quebra carga no Oracle ou distorce KPI · "
             "**🟠 Média** — inconsistência de formato/regra de negócio · "
             "**🟡 Baixa** — cosmético ou informativo.\n")
    icone = {"Alta": "🔴", "Média": "🟠", "Baixa": "🟡"}
    for i, a in enumerate(achados.itertuples(index=False), 1):
        L.append(f"### {i}. {icone[a.severidade]} {a.regra}\n")
        L.append(f"- **Onde:** `{a.tabela}` → `{a.coluna}`  ")
        L.append(f"- **Dimensão:** {a.dimensao} · **Severidade:** {a.severidade}  ")
        L.append(f"- **Afetados:** {a.qtd_afetada} de {a.total} ({a.pct:g}%)  ")
        if a.exemplo:
            L.append(f"- **Exemplos:** `{a.exemplo}`  ")
        L.append(f"- **Recomendação:** {a.recomendacao}\n")

    L.append("## Perfil descritivo de `tb_chamado_v3`\n")
    L.append(f"Período de abertura: **{p['periodo'][0]} a {p['periodo'][1]}** · "
             f"{p['origem'].get('original', 0)} chamados originais + "
             f"{p['origem'].get('sintético', 0)} sintéticos.\n")
    L.append(f"- Chamados finalizados resolvidos **dentro do prazo: {p['no_prazo']:.1f}%** "
             "(o gerador fixa ~65% — o KPI de SLA do dashboard reflete um parâmetro, não um comportamento).")
    L.append(f"- Tempo mediano de resolução: **{p['tempo_med']:.0f} dias**.")
    L.append(f"- Correlação (Spearman) score × prioridade-base: **{p['corr_score']:.2f}** "
             "— coerente, o score segue a criticidade da subcategoria.\n")
    L.append("**% de chamados finalizados por idade** (esperado: crescer com a idade; plano = status sorteado ao acaso)\n")
    L.append(serie_md(p["pct_final_idade"], "Idade do chamado", "% finalizados") + "\n")
    L.append("**Status**\n")
    L.append(serie_md(p["status"], "ST_CHAMADO") + "\n")
    L.append("**Canal**\n")
    L.append(serie_md(p["canal"], "Canal") + "\n")
    L.append("**Categoria**\n")
    L.append(serie_md(p["categoria"], "Categoria") + "\n")
    L.append("**Score por prioridade-base da subcategoria**\n")
    sp = p["score_prior"].reset_index()
    sp.columns = ["Prioridade-base", "Chamados", "Mín", "Mediana", "Máx"]
    L.append(md_tabela(sp) + "\n")

    L.append("## Próximos passos sugeridos\n")
    L.append("1. **DDL (patch v3):** `NR_CEP` → `CHAR(8)`, `NR_CPF_CIDADAO` → `CHAR(11)`; decidir onde "
             "vive a data de resolução (coluna em `T_URB_CHAMADO` ou carga de `T_URB_ATENDIMENTO`).")
    L.append("2. **Gerador:** versionar `tb_chamado_v2.csv`; ler prioridade/SLA dos cadastros; "
             "coordenadas por bairro; status dependente da idade; resolução ≤ data de corte; "
             "descrições por subcategoria.")
    L.append("3. **Cadastros:** reexportar CEP com zero à esquerda, CPFs com DV válido e telefones "
             "com nono dígito.")
    L.append("4. **Dashboard:** até a massa ser regenerada, filtrar a partir de dez/2024 e sinalizar "
             "que o SLA é parâmetro sintético.")
    L.append("5. **Rodar este script** a cada nova massa (pode virar etapa de qualidade na camada "
             "Prata do pipeline medalhão).\n")

    L.append("## Todas as verificações executadas\n")
    tv = todas.sort_values(["dimensao", "tabela", "coluna"])
    tv = tv.assign(Resultado=tv["qtd_afetada"].map(lambda q: "✅" if q == 0 else f"❌ {q}"))
    L.append(md_tabela(tv[["dimensao", "tabela", "coluna", "regra", "Resultado"]]
                       .rename(columns={"dimensao": "Dimensão", "tabela": "Tabela",
                                        "coluna": "Coluna", "regra": "Regra"})))
    L.append("")
    return "\n".join(L)


# ============================================================================
# MAIN
# ============================================================================


def main():
    modelo = ler_modelo()
    dados = ler_dados()
    ger = carregar_gerador()

    verificar_estrutura(dados, modelo)
    verificar_integridade(dados, modelo)
    verificar_dominios(dados)
    c = preparar_chamado(dados)
    c = verificar_chamado(c, dados, ger)
    verificar_artefatos(dados, modelo, ger)

    todas = pd.DataFrame([{**asdict(v), "pct": v.pct} for v in VERIFICACOES])
    achados = todas[todas["qtd_afetada"] > 0].copy()
    achados["_ord"] = achados["severidade"].map(ORDEM_SEVERIDADE)
    achados = (achados.sort_values(["_ord", "pct", "tabela"], ascending=[True, False, True])
               .drop(columns="_ord").reset_index(drop=True))

    colunas = ["tabela", "coluna", "regra", "dimensao", "severidade",
               "qtd_afetada", "total", "pct", "exemplo", "recomendacao"]
    achados[colunas].to_csv(SAIDA_CSV, index=False, encoding="utf-8-sig", lineterminator="\n")
    SAIDA_MD.write_text(gerar_relatorio(achados, todas, perfil(c, dados)), encoding="utf-8",
                        newline="\n")

    sev = achados["severidade"].value_counts()
    print(f"{len(todas)} verificações | {len(achados)} achados "
          f"(Alta {sev.get('Alta', 0)}, Média {sev.get('Média', 0)}, Baixa {sev.get('Baixa', 0)})")
    print(f"-> {SAIDA_CSV.relative_to(ROOT)}")
    print(f"-> {SAIDA_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
