"""
UrbanIQ — Gerador de dados expandidos para o dashboard Power BI
================================================================

Este script lê o tb_chamado_v2.csv (50 chamados originais) e gera uma versão
expandida com N chamados sintéticos que respeitam:

  1. Distribuição de status originais (ABERTO, EM_ANALISE, ...)
  2. Faixa de score por subcategoria (categorias críticas têm score alto)
  3. Região geográfica de São Paulo (lat/long dos originais)
  4. Sazonalidade: janela de datas de dez/2024 a jan/2026
  5. NOVIDADE — coluna DT_RESOLUCAO:
       - preenchida só para status RESOLVIDO e ENCERRADO
       - ~65% dentro do prazo, ~35% em atraso
       - nunca antes de DT_ABERTURA

Reprodutibilidade: usa random.seed(42) — rodar duas vezes gera o mesmo CSV.

Uso:
    python gerar_dados_expandidos.py
    python gerar_dados_expandidos.py --n 500   # gera 500 chamados
    python gerar_dados_expandidos.py --n 2000  # gera 2000 chamados

Saída: tb_chamado_v3.csv na mesma pasta do script.
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SEED = 42
DEFAULT_N = 1000

# Caminho do CSV original (relativo a este script, subindo até a raiz do repo)
REPO_ROOT = Path(__file__).resolve().parents[3]
CSV_ORIGEM = REPO_ROOT / "fase3-ingestao" / "docs" / "CSV`s" / "tb_chamado_v2.csv"
CSV_DESTINO = Path(__file__).parent / "tb_chamado_v3.csv"

# Distribuição de status (baseada nos 50 originais)
DISTRIB_STATUS = [
    ("ABERTO", 0.18),
    ("EM_ANALISE", 0.20),
    ("EM_ATENDIMENTO", 0.20),
    ("RESOLVIDO", 0.24),
    ("ENCERRADO", 0.18),
]

# Distribuição de canais (baseada nos 5 canais de dCanal)
# Damos mais peso a APP_MOBILE e TELEFONE (canais mais usados em cidade real)
DISTRIB_CANAL = [
    (1, 0.35),  # APP_MOBILE
    (2, 0.20),  # PORTAL_WEB
    (3, 0.25),  # TELEFONE
    (4, 0.12),  # SENSOR_IOT
    (5, 0.08),  # CAMERA_HD
]

# Faixa de score por prioridade base (dSubcategoria.NR_PRIORIDADE_BASE 1-5)
# Prioridade base 5 = risco imediato (semáforo, cabo elétrico, dengue) → score alto
# Prioridade base 1 = estético (pichação) → score baixo
FAIXA_SCORE_POR_PRIORIDADE_BASE = {
    5: (65, 95),
    4: (50, 80),
    3: (35, 65),
    2: (25, 50),
    1: (15, 40),
}

# Mapeamento ID_SUBCATEGORIA → NR_PRIORIDADE_BASE (das 24 subcategorias)
# Extraído da base de conhecimento do projeto
PRIORIDADE_BASE_POR_SUBCAT = {
    1: 5,   # Buraco na via
    2: 3,   # Calçada danificada
    3: 4,   # Poste inclinado
    4: 4,   # Poste apagado
    5: 2,   # Lâmpada com defeito
    6: 5,   # Cabo elétrico exposto
    7: 3,   # Acúmulo de lixo
    8: 3,   # Entulho irregular
    9: 1,   # Pichação
    10: 5,  # Foco de dengue
    11: 5,  # Esgoto a céu aberto
    12: 4,  # Animal morto
    13: 2,  # Ponto de ônibus danificado
    14: 2,  # Abrigo sem cobertura
    15: 3,  # Faixa apagada
    16: 4,  # Câmera danificada
    17: 5,  # Semáforo com defeito
    18: 3,  # Placa ausente
    19: 5,  # Árvore com risco de queda
    20: 2,  # Praça degradada
    21: 4,  # Poluição em córrego
    22: 4,  # Bueiro entupido
    23: 3,  # Sinalização ausente
    24: 2,  # Pavimentação deteriorada
}

# Bounding box da Grande São Paulo (lat/long)
LAT_MIN, LAT_MAX = -23.5900, -23.5400
LONG_MIN, LONG_MAX = -46.7100, -46.4600

# Janela de datas de abertura
DATA_MIN = date(2024, 12, 1)
DATA_MAX = date(2026, 1, 31)

# Descrições genéricas de chamado (pool para amostrar)
DESCRICOES_POR_PRIORIDADE = {
    5: [
        "Situação de risco iminente à população",
        "Perigo imediato à integridade física",
        "Necessita intervenção emergencial",
        "Foco crítico identificado, ação urgente",
        "Risco elevado, comunicado à defesa civil",
    ],
    4: [
        "Problema grave afetando fluxo local",
        "Ocorrência prioritária, moradores impactados",
        "Necessita atendimento em até 72h",
        "Impacto significativo no bairro",
    ],
    3: [
        "Ocorrência recorrente na região",
        "Problema afeta rotina dos moradores",
        "Necessita programação para atendimento",
        "Solicitação com impacto médio",
    ],
    2: [
        "Melhoria solicitada pelos cidadãos",
        "Manutenção preventiva necessária",
        "Ajuste operacional na infraestrutura",
    ],
    1: [
        "Solicitação estética / cosmética",
        "Zeladoria de baixa criticidade",
    ],
}


# ============================================================================
# FUNÇÕES
# ============================================================================

def escolher_com_peso(distrib):
    """Sorteia um item de uma lista [(valor, peso), ...] respeitando os pesos."""
    valores, pesos = zip(*distrib)
    return random.choices(valores, weights=pesos, k=1)[0]


def gerar_data_aleatoria(data_min, data_max):
    """Retorna uma data aleatória no intervalo [data_min, data_max]."""
    delta = (data_max - data_min).days
    return data_min + timedelta(days=random.randint(0, delta))


def calcular_prazo_estimado(dt_abertura, prioridade_base):
    """
    Calcula DT_PRAZO_ESTIMADO baseado na prioridade base:
      - prioridade 5 → 1 a 3 dias
      - prioridade 4 → 3 a 7 dias
      - prioridade 3 → 7 a 15 dias
      - prioridade 2 → 15 a 30 dias
      - prioridade 1 → 30 a 60 dias
    """
    faixas = {5: (1, 3), 4: (3, 7), 3: (7, 15), 2: (15, 30), 1: (30, 60)}
    dias_min, dias_max = faixas[prioridade_base]
    return dt_abertura + timedelta(days=random.randint(dias_min, dias_max))


def calcular_dt_resolucao(dt_abertura, dt_prazo, status):
    """
    Preenche DT_RESOLUCAO só para RESOLVIDO/ENCERRADO.
    ~65% dentro do prazo, ~35% em atraso.
    Nunca antes de DT_ABERTURA.
    """
    if status not in ("RESOLVIDO", "ENCERRADO"):
        return ""  # vazio no CSV = NULL no Power BI

    dentro_do_prazo = random.random() < 0.65

    if dentro_do_prazo:
        # Resolvido entre a abertura e o prazo
        dias_uteis = max((dt_prazo - dt_abertura).days, 1)
        offset = random.randint(1, dias_uteis)
        return dt_abertura + timedelta(days=offset)
    else:
        # Resolvido depois do prazo (1 a 20 dias de atraso)
        atraso = random.randint(1, 20)
        return dt_prazo + timedelta(days=atraso)


def gerar_chamado(nr_chamado):
    """Gera 1 chamado sintético com todos os campos preenchidos."""
    id_subcategoria = random.randint(1, 24)
    prioridade_base = PRIORIDADE_BASE_POR_SUBCAT[id_subcategoria]

    score_min, score_max = FAIXA_SCORE_POR_PRIORIDADE_BASE[prioridade_base]
    nr_score = random.randint(score_min, score_max)

    dt_abertura = gerar_data_aleatoria(DATA_MIN, DATA_MAX)
    dt_prazo = calcular_prazo_estimado(dt_abertura, prioridade_base)

    status = escolher_com_peso(DISTRIB_STATUS)
    dt_resolucao = calcular_dt_resolucao(dt_abertura, dt_prazo, status)

    descricao = random.choice(DESCRICOES_POR_PRIORIDADE[prioridade_base])
    id_canal = escolher_com_peso(DISTRIB_CANAL)

    return {
        "NR_CHAMADO": nr_chamado,
        "ID_CIDADAO": random.randint(1, 50),
        "ID_LOGRADOURO": random.randint(1, 20),
        "ID_SUBCATEGORIA": id_subcategoria,
        "DT_ABERTURA": dt_abertura.isoformat(),
        "DS_CHAMADO": descricao,
        "NR_SCORE_PRIORIDADE": nr_score,
        "ST_CHAMADO": status,
        "ID_CANAL": id_canal,
        "DT_PRAZO_ESTIMADO": dt_prazo.isoformat(),
        "DT_RESOLUCAO": dt_resolucao.isoformat() if dt_resolucao else "",
        "NR_LATITUDE": round(random.uniform(LAT_MIN, LAT_MAX), 7),
        "NR_LONGITUDE": round(random.uniform(LONG_MIN, LONG_MAX), 7),
    }


def carregar_originais():
    """Lê os 50 chamados originais e adiciona a coluna DT_RESOLUCAO vazia."""
    if not CSV_ORIGEM.exists():
        raise FileNotFoundError(
            f"CSV original nao encontrado em: {CSV_ORIGEM}\n"
            f"Verifique o caminho relativo do script."
        )

    originais = []
    with open(CSV_ORIGEM, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Retro-preenche DT_RESOLUCAO para os 50 originais tambem
            status = row["ST_CHAMADO"]
            if status in ("RESOLVIDO", "ENCERRADO"):
                dt_abertura = date.fromisoformat(row["DT_ABERTURA"])
                dt_prazo = date.fromisoformat(row["DT_PRAZO_ESTIMADO"])
                dt_resolucao = calcular_dt_resolucao(dt_abertura, dt_prazo, status)
                row["DT_RESOLUCAO"] = dt_resolucao.isoformat()
            else:
                row["DT_RESOLUCAO"] = ""
            originais.append(row)
    return originais


def salvar_csv(dados):
    """Grava o CSV final com a nova coluna DT_RESOLUCAO."""
    campos = [
        "NR_CHAMADO", "ID_CIDADAO", "ID_LOGRADOURO", "ID_SUBCATEGORIA",
        "DT_ABERTURA", "DS_CHAMADO", "NR_SCORE_PRIORIDADE", "ST_CHAMADO",
        "ID_CANAL", "DT_PRAZO_ESTIMADO", "DT_RESOLUCAO",
        "NR_LATITUDE", "NR_LONGITUDE",
    ]
    with open(CSV_DESTINO, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(dados)


def main():
    parser = argparse.ArgumentParser(description="Gera CSV expandido do UrbanIQ")
    parser.add_argument("--n", type=int, default=DEFAULT_N,
                        help=f"Total de chamados a gerar (padrao: {DEFAULT_N})")
    args = parser.parse_args()

    random.seed(SEED)

    print(f"[1/3] Lendo CSV original: {CSV_ORIGEM.name}")
    originais = carregar_originais()
    print(f"      {len(originais)} chamados originais carregados")

    print(f"[2/3] Gerando {args.n - len(originais)} chamados sinteticos...")
    novos = []
    for i in range(len(originais) + 1, args.n + 1):
        novos.append(gerar_chamado(i))

    total = originais + novos
    print(f"      Total no dataset final: {len(total)}")

    print(f"[3/3] Salvando em: {CSV_DESTINO.name}")
    salvar_csv(total)

    # Estatisticas rapidas
    print("\n--- Estatisticas do dataset gerado ---")
    from collections import Counter
    status_count = Counter(row["ST_CHAMADO"] for row in total)
    for st, ct in sorted(status_count.items()):
        pct = ct / len(total) * 100
        print(f"  {st:<20} {ct:>5} ({pct:5.1f}%)")

    com_resolucao = sum(1 for row in total if row["DT_RESOLUCAO"])
    print(f"\n  Chamados com DT_RESOLUCAO: {com_resolucao} ({com_resolucao/len(total)*100:.1f}%)")
    print(f"\nOK - CSV pronto: {CSV_DESTINO}")


if __name__ == "__main__":
    main()
