# UrbanIQ — Diagnóstico de Qualidade de Dados

> Gerado automaticamente por `qualidade-dados/diagnostico_qualidade.py`. Não edite à mão — rode o script novamente.

## Escopo

| Fonte | Arquivo | Linhas |
|---|---|---|
| tb_bairro | `fase3-ingestao/data/raw/tb_bairro.csv` | 15 |
| tb_canal_atendimento | `fase3-ingestao/data/raw/tb_canal_atendimento.csv` | 5 |
| tb_categoria | `fase3-ingestao/data/raw/tb_categoria.csv` | 8 |
| tb_cidadao | `fase3-ingestao/data/raw/tb_cidadao.csv` | 50 |
| tb_cidade | `fase3-ingestao/data/raw/tb_cidade.csv` | 5 |
| tb_equipe | `fase3-ingestao/data/raw/tb_equipe.csv` | 5 |
| tb_estado | `fase3-ingestao/data/raw/tb_estado.csv` | 3 |
| tb_gestor | `fase3-ingestao/data/raw/tb_gestor.csv` | 15 |
| tb_logradouro | `fase3-ingestao/data/raw/tb_logradouro.csv` | 20 |
| tb_subcategoria | `fase3-ingestao/data/raw/tb_subcategoria.csv` | 24 |
| tb_chamado_v3 | `dashboards/powerbi/dados/tb_chamado_v3.csv` | 1000 |

**Referência de 'correto':** DDL Oracle `urbaniq-ddl.sql` + `urbaniq-ddl-patch-v2.sql` (tipos, tamanhos, NOT NULL, PK, UNIQUE, FK e CHECK lidos automaticamente dos scripts) e regras de negócio do projeto (SLA, score, status, geografia).  
**Data de corte:** 2026-01-31 (maior `DT_ABERTURA`; usada no lugar de 'hoje' para o resultado ser determinístico).

## Resumo executivo

- **245 verificações** executadas; **15 reprovadas** (🔴 1 alta · 🟠 9 média · 🟡 5 baixa).
- **A carga no Oracle não falharia por tipo, domínio ou chave**: não há FK órfã, PK duplicada, nulo em coluna obrigatória nem valor fora dos CHECKs. A estrutura básica está sólida.
- Leitura dos achados desta execução — os problemas se concentram em três frentes:
  1. **Modelo × dado divergem** — `tb_chamado_v3` traz `DT_RESOLUCAO`, que não existe em `T_URB_CHAMADO`; o CEP perdeu o zero à esquerda por ser `NUMBER(8)`; o gerador do dataset depende de um arquivo que não está no repositório.
  2. **Realismo do dado sintético** — coordenadas sem relação com o logradouro, status independente da idade do chamado, descrições genéricas repetidas e resoluções posteriores à data de corte.
  3. **Formatos cadastrais** — CPFs com dígito verificador inválido e telefones de gestores sem o nono dígito.
- **Impacto direto nos KPIs do dashboard:** backlog e % de atraso inflados, mapa de ocorrências enganoso e série temporal com salto artificial em dez/2024.

## Placar por dimensão

| Dimensão | Verificações | Aprovadas | Reprovadas | % aprovação |
|---|---|---|---|---|
| Completude | 46 | 45 | 1 | 98 |
| Consistência | 9 | 7 | 2 | 78 |
| Consistência entre artefatos | 25 | 22 | 3 | 88 |
| Consistência temporal | 3 | 2 | 1 | 67 |
| Integridade referencial | 18 | 16 | 2 | 89 |
| Plausibilidade | 2 | 0 | 2 | 0 |
| Unicidade | 15 | 14 | 1 | 93 |
| Validade | 127 | 124 | 3 | 98 |

## Placar por tabela (achados)

| Tabela | Alta | Média | Baixa | Total |
|---|---|---|---|---|
| tb_chamado_v3 | 1 | 5 | 0 | 6 |
| tb_cidadao | 0 | 1 | 1 | 2 |
| tb_logradouro | 0 | 1 | 1 | 2 |
| gerar_dados_expandidos.py | 0 | 1 | 0 | 1 |
| tb_gestor | 0 | 1 | 0 | 1 |
| DDL | 0 | 0 | 1 | 1 |
| tb_bairro | 0 | 0 | 1 | 1 |
| tb_estado | 0 | 0 | 1 | 1 |

## Achados priorizados

Severidade: **🔴 Alta** — quebra carga no Oracle ou distorce KPI · **🟠 Média** — inconsistência de formato/regra de negócio · **🟡 Baixa** — cosmético ou informativo.

### 1. 🔴 Colunas do CSV existem em T_URB_CHAMADO

- **Onde:** `tb_chamado_v3` → `DT_RESOLUCAO`  
- **Dimensão:** Consistência entre artefatos · **Severidade:** Alta  
- **Afetados:** 1 de 13 (7.7%)  
- **Exemplos:** `DT_RESOLUCAO`  
- **Recomendação:** Coluna sem destino no modelo físico: a carga no Oracle vai descartá-la ou falhar. Adicionar a coluna ao DDL (patch v3) ou mapear para a tabela correta.

### 2. 🟠 Arquivo de entrada do gerador existe no repositório

- **Onde:** `gerar_dados_expandidos.py` → `CSV_ORIGEM`  
- **Dimensão:** Consistência entre artefatos · **Severidade:** Média  
- **Afetados:** 1 de 1 (100%)  
- **Exemplos:** `fase3-ingestao/docs/CSV`s/tb_chamado_v2.csv`  
- **Recomendação:** O gerador lê tb_chamado_v2.csv (50 chamados originais), que não está versionado: o tb_chamado_v3.csv não pode ser reproduzido. Versionar o v2 (ex.: em fase3-ingestao/data/raw/) e corrigir o caminho, que contém crase ("CSV`s").

### 3. 🟠 Descrição do chamado não repetida

- **Onde:** `tb_chamado_v3` → `DS_CHAMADO`  
- **Dimensão:** Unicidade · **Severidade:** Média  
- **Afetados:** 1000 de 1000 (100%)  
- **Exemplos:** `Ajuste operacional na infraestrutura | Necessita programação para atendimento | Manutenção preventiva necessária`  
- **Recomendação:** Só 42 textos distintos em 1000 chamados, e os sintéticos usam frases genéricas por prioridade (não citam o problema). Inviabiliza classificação de texto/NLP e deixa a descrição sem valor analítico. Gerar texto a partir da subcategoria (templates por subcategoria + variações).

### 4. 🟠 CPF com dígitos verificadores válidos

- **Onde:** `tb_cidadao` → `NR_CPF_CIDADAO`  
- **Dimensão:** Validade · **Severidade:** Média  
- **Afetados:** 50 de 50 (100%)  
- **Exemplos:** `70000001001 | 70000002002 | 70000003003`  
- **Recomendação:** O DDL documenta 'CPF deve ser válido'. Gerar CPFs sintéticos com DV correto (qualquer validação na aplicação/ETL rejeitaria estes). Guardar como CHAR(11) — NUMBER(11) perde zeros à esquerda (CPFs iniciados por 0).

### 5. 🟠 Celular com 9º dígito (11 posições)

- **Onde:** `tb_gestor` → `NR_TELEFONE`  
- **Dimensão:** Validade · **Severidade:** Média  
- **Afetados:** 15 de 15 (100%)  
- **Exemplos:** `1191000001 | 1191000002 | 1191000003`  
- **Recomendação:** Número começa com 9 (celular) mas tem só 8 dígitos após o DDD — falta o nono dígito, obrigatório desde 2016. Padronizar com o formato de tb_cidadao.

### 6. 🟠 CEP com 8 dígitos

- **Onde:** `tb_logradouro` → `NR_CEP`  
- **Dimensão:** Validade · **Severidade:** Média  
- **Afetados:** 20 de 20 (100%)  
- **Exemplos:** `NM_LOGRADOURO=Rua Aspicuelta, NR_CEP=5422001 | NM_LOGRADOURO=Rua Fradique Coutinho, NR_CEP=5422002 | NM_LOGRADOURO=Rua dos Pinheiros, NR_CEP=5422003`  
- **Recomendação:** CEPs da capital paulista começam com 0 (01000-000 a 05999-999; 08xxx-xxx) e o zero à esquerda foi perdido — o CSV foi exportado de uma coluna numérica. Trocar NR_CEP de NUMBER(8) para CHAR(8) no DDL e reexportar com zero à esquerda (ex.: 5422001 → 05422001). Sem isso, qualquer cruzamento com base de CEP (Correios/IBGE) falha.

### 7. 🟠 Coordenada a ≤ 5 km do bairro do logradouro

- **Onde:** `tb_chamado_v3` → `NR_LATITUDE, NR_LONGITUDE`  
- **Dimensão:** Consistência · **Severidade:** Média  
- **Afetados:** 738 de 1000 (73.8%)  
- **Exemplos:** `NR_CHAMADO=51, NM_BAIRRO=Pinheiros, DIST_BAIRRO_KM=5.5 | NR_CHAMADO=52, NM_BAIRRO=Itaquera, DIST_BAIRRO_KM=20.8 | NR_CHAMADO=53, NM_BAIRRO=Itaquera, DIST_BAIRRO_KM=19.2`  
- **Recomendação:** Lat/long é sorteada num retângulo fixo, sem relação com o logradouro informado — o mapa mostra um chamado da 'Rua Aspicuelta' em Itaquera. Além disso, o retângulo do gerador (lat −23,59 a −23,54) exclui Santana e Campo Belo inteiros. Gerar o ponto com jitter em torno do centroide do bairro/logradouro.

### 8. 🟠 Chamado não finalizado com prazo vencido há > 90 dias

- **Onde:** `tb_chamado_v3` → `ST_CHAMADO`  
- **Dimensão:** Plausibilidade · **Severidade:** Média  
- **Afetados:** 451 de 1000 (45.1%)  
- **Exemplos:** `NR_CHAMADO=1, ST_CHAMADO=ABERTO, DT_ABERTURA=2024-12-18 | NR_CHAMADO=2, ST_CHAMADO=EM_ANALISE, DT_ABERTURA=2024-02-14 | NR_CHAMADO=3, ST_CHAMADO=EM_ATENDIMENTO, DT_ABERTURA=2025-07-03`  
- **Recomendação:** O gerador sorteia o status independentemente da data de abertura: chamados de 2024–início de 2025 continuam ABERTO/EM_ANALISE, enquanto a proporção de finalizados não cresce com a idade. Isso infla o backlog e o % de atraso no dashboard. Tornar a probabilidade de status final crescente com a idade do chamado.

### 9. 🟠 Volume mensal contínuo (≥ 20% da mediana)

- **Onde:** `tb_chamado_v3` → `DT_ABERTURA`  
- **Dimensão:** Plausibilidade · **Severidade:** Média  
- **Afetados:** 10 de 24 (41.7%)  
- **Exemplos:** `2024-02: 4 | 2024-03: 1 | 2024-04: 3`  
- **Recomendação:** Antes de dez/2024 só existem chamados originais (0–4 por mês); os 950 sintéticos entram a partir de dez/2024 com ~70/mês. Gráficos de tendência mostram um 'salto' artificial. Filtrar o dashboard a partir de dez/2024 ou estender a janela do gerador.

### 10. 🟠 Resolução ≤ data de corte do dataset (2026-01-31)

- **Onde:** `tb_chamado_v3` → `DT_RESOLUCAO`  
- **Dimensão:** Consistência temporal · **Severidade:** Média  
- **Afetados:** 10 de 1000 (1%)  
- **Exemplos:** `NR_CHAMADO=118, DT_ABERTURA=2026-01-10, DT_RESOLUCAO=2026-03-08 | NR_CHAMADO=356, DT_ABERTURA=2026-01-29, DT_RESOLUCAO=2026-02-23 | NR_CHAMADO=453, DT_ABERTURA=2026-01-23, DT_RESOLUCAO=2026-02-03`  
- **Recomendação:** O snapshot termina na última abertura, mas há resoluções registradas depois dela (datas 'do futuro' em relação à extração). No gerador, limitar DT_RESOLUCAO a DATA_MAX ou manter o chamado em EM_ATENDIMENTO quando a resolução cairia após o corte.

### 11. 🟡 Coluna opcional 100% vazia

- **Onde:** `tb_logradouro` → `DS_COMPLEMENTO`  
- **Dimensão:** Completude · **Severidade:** Baixa  
- **Afetados:** 20 de 20 (100%)  
- **Exemplos:** `todas as linhas vazias`  
- **Recomendação:** Coluna sem nenhum valor: confirmar se o dado existe na origem ou retirá-la do modelo/visuais.

### 12. 🟡 Registro-pai referenciado por ao menos um filho

- **Onde:** `tb_estado` → `ID_ESTADO`  
- **Dimensão:** Integridade referencial · **Severidade:** Baixa  
- **Afetados:** 2 de 3 (66.7%)  
- **Exemplos:** `RJ | MG`  
- **Recomendação:** Cadastro sem uso: aparece em filtros/slicers do dashboard sem nenhum dado. Completar a massa (ex.: logradouros/chamados para essas entidades) ou documentar como cadastro de referência.

### 13. 🟡 Toda tabela do modelo tem massa de dados

- **Onde:** `DDL` → `-`  
- **Dimensão:** Consistência entre artefatos · **Severidade:** Baixa  
- **Afetados:** 6 de 17 (35.3%)  
- **Exemplos:** `T_URB_ATENDIMENTO | T_URB_AVALIACAO | T_URB_CIDADAO_LOGRADOURO`  
- **Recomendação:** Sem histórico de status, atendimentos, avaliações e overrides não é possível medir RN05/RN06 nem calcular SLA pelo caminho do modelo (T_URB_ATENDIMENTO.DT_CONCLUSAO). Priorizar T_URB_HISTORICO_STATUS e T_URB_ATENDIMENTO na próxima massa.

### 14. 🟡 Registro-pai referenciado por ao menos um filho

- **Onde:** `tb_bairro` → `ID_BAIRRO`  
- **Dimensão:** Integridade referencial · **Severidade:** Baixa  
- **Afetados:** 5 de 15 (33.3%)  
- **Exemplos:** `Jardim Tranquilidade | Vila Galvão | Cambuí`  
- **Recomendação:** Cadastro sem uso: aparece em filtros/slicers do dashboard sem nenhum dado. Completar a massa (ex.: logradouros/chamados para essas entidades) ou documentar como cadastro de referência.

### 15. 🟡 E-mail derivado do nome sem erro de transliteração

- **Onde:** `tb_cidadao` → `DS_EMAIL`  
- **Dimensão:** Consistência · **Severidade:** Baixa  
- **Afetados:** 2 de 50 (4%)  
- **Exemplos:** `NM_CIDADAO=Márcio Araújo, DS_EMAIL=marcio.araojo23@urbiq.com.br | NM_CIDADAO=Claudia Araújo, DS_EMAIL=claudia.araojo48@urbiq.com.br`  
- **Recomendação:** Transliteração de acentos gerou grafia errada no e-mail (ex.: ú → o). Usar unicodedata.normalize('NFKD') no gerador.

## Perfil descritivo de `tb_chamado_v3`

Período de abertura: **2024-02-02 a 2026-01-31** · 50 chamados originais + 950 sintéticos.

- Chamados finalizados resolvidos **dentro do prazo: 67.2%** (o gerador fixa ~65% — o KPI de SLA do dashboard reflete um parâmetro, não um comportamento).
- Tempo mediano de resolução: **8 dias**.
- Correlação (Spearman) score × prioridade-base: **0.90** — coerente, o score segue a criticidade da subcategoria.

**% de chamados finalizados por idade** (esperado: crescer com a idade; plano = status sorteado ao acaso)

| Idade do chamado | % finalizados |
|---|---|
| ≤ 90 d | 33.5 |
| 91–180 d | 44.4 |
| 181–365 d | 38.1 |
| > 365 d | 38.2 |

**Status**

| ST_CHAMADO | Qtd |
|---|---|
| RESOLVIDO | 231 |
| EM_ANALISE | 212 |
| EM_ATENDIMENTO | 203 |
| ABERTO | 201 |
| ENCERRADO | 153 |

**Canal**

| Canal | Qtd |
|---|---|
| APP_MOBILE | 348 |
| TELEFONE | 242 |
| PORTAL_WEB | 197 |
| SENSOR_IOT | 120 |
| CAMERA_HD | 93 |

**Categoria**

| Categoria | Qtd |
|---|---|
| Infraestrutura Viária | 129 |
| Iluminação Pública | 128 |
| Saúde Pública | 127 |
| Serviços Públicos | 127 |
| Transporte Público | 124 |
| Meio Ambiente | 123 |
| Zeladoria Urbana | 121 |
| Segurança Pública | 121 |

**Score por prioridade-base da subcategoria**

| Prioridade-base | Chamados | Mín | Mediana | Máx |
|---|---|---|---|---|
| 1 | 39 | 15 | 27.0 | 40 |
| 2 | 208 | 25 | 39.0 | 50 |
| 3 | 251 | 35 | 51.0 | 65 |
| 4 | 248 | 50 | 65.0 | 80 |
| 5 | 254 | 65 | 80.0 | 95 |

## Próximos passos sugeridos

1. **DDL (patch v3):** `NR_CEP` → `CHAR(8)`, `NR_CPF_CIDADAO` → `CHAR(11)`; decidir onde vive a data de resolução (coluna em `T_URB_CHAMADO` ou carga de `T_URB_ATENDIMENTO`).
2. **Gerador:** versionar `tb_chamado_v2.csv`; ler prioridade/SLA dos cadastros; coordenadas por bairro; status dependente da idade; resolução ≤ data de corte; descrições por subcategoria.
3. **Cadastros:** reexportar CEP com zero à esquerda, CPFs com DV válido e telefones com nono dígito.
4. **Dashboard:** até a massa ser regenerada, filtrar a partir de dez/2024 e sinalizar que o SLA é parâmetro sintético.
5. **Rodar este script** a cada nova massa (pode virar etapa de qualidade na camada Prata do pipeline medalhão).

## Todas as verificações executadas

| Dimensão | Tabela | Coluna | Regra | Resultado |
|---|---|---|---|---|
| Completude | tb_bairro | ID_BAIRRO | NOT NULL | ✅ |
| Completude | tb_bairro | ID_CIDADE | NOT NULL | ✅ |
| Completude | tb_bairro | NM_BAIRRO | NOT NULL | ✅ |
| Completude | tb_canal_atendimento | ID_CANAL | NOT NULL | ✅ |
| Completude | tb_canal_atendimento | NM_CANAL | NOT NULL | ✅ |
| Completude | tb_canal_atendimento | ST_ATIVO | NOT NULL | ✅ |
| Completude | tb_categoria | ID_CATEGORIA | NOT NULL | ✅ |
| Completude | tb_categoria | NM_CATEGORIA | NOT NULL | ✅ |
| Completude | tb_categoria | ST_ATIVO | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | DS_CHAMADO | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | DT_ABERTURA | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | ID_CIDADAO | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | ID_LOGRADOURO | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | ID_SUBCATEGORIA | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | NR_CHAMADO | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | NR_SCORE_PRIORIDADE | NOT NULL | ✅ |
| Completude | tb_chamado_v3 | ST_CHAMADO | NOT NULL | ✅ |
| Completude | tb_cidadao | DS_EMAIL | NOT NULL | ✅ |
| Completude | tb_cidadao | ID_CIDADAO | NOT NULL | ✅ |
| Completude | tb_cidadao | NM_CIDADAO | NOT NULL | ✅ |
| Completude | tb_cidadao | NR_CPF_CIDADAO | NOT NULL | ✅ |
| Completude | tb_cidadao | NR_TELEFONE | NOT NULL | ✅ |
| Completude | tb_cidade | ID_CIDADE | NOT NULL | ✅ |
| Completude | tb_cidade | ID_ESTADO | NOT NULL | ✅ |
| Completude | tb_cidade | NM_CIDADE | NOT NULL | ✅ |
| Completude | tb_equipe | ID_EQUIPE | NOT NULL | ✅ |
| Completude | tb_equipe | NM_EQUIPE | NOT NULL | ✅ |
| Completude | tb_equipe | ST_ATIVO | NOT NULL | ✅ |
| Completude | tb_estado | ID_ESTADO | NOT NULL | ✅ |
| Completude | tb_estado | NM_ESTADO | NOT NULL | ✅ |
| Completude | tb_estado | SG_ESTADO | NOT NULL | ✅ |
| Completude | tb_gestor | DS_CARGO | NOT NULL | ✅ |
| Completude | tb_gestor | ID_EQUIPE | NOT NULL | ✅ |
| Completude | tb_gestor | ID_GESTOR | NOT NULL | ✅ |
| Completude | tb_gestor | NM_GESTOR | NOT NULL | ✅ |
| Completude | tb_gestor | NR_MATRICULA | NOT NULL | ✅ |
| Completude | tb_logradouro | DS_COMPLEMENTO | Coluna opcional 100% vazia | ❌ 20 |
| Completude | tb_logradouro | ID_BAIRRO | NOT NULL | ✅ |
| Completude | tb_logradouro | ID_LOGRADOURO | NOT NULL | ✅ |
| Completude | tb_logradouro | NM_LOGRADOURO | NOT NULL | ✅ |
| Completude | tb_logradouro | NR_CEP | NOT NULL | ✅ |
| Completude | tb_subcategoria | ID_CATEGORIA | NOT NULL | ✅ |
| Completude | tb_subcategoria | ID_SUBCATEGORIA | NOT NULL | ✅ |
| Completude | tb_subcategoria | NM_SUBCATEGORIA | NOT NULL | ✅ |
| Completude | tb_subcategoria | NR_PRIORIDADE_BASE | NOT NULL | ✅ |
| Completude | tb_subcategoria | ST_ATIVO | NOT NULL | ✅ |
| Consistência | tb_chamado_v3 | DT_PRAZO_ESTIMADO | Prazo (dias) dentro do SLA da prioridade-base (5→1–3d … 1→30–60d) | ✅ |
| Consistência | tb_chamado_v3 | DT_RESOLUCAO | Resolução só em status RESOLVIDO/ENCERRADO | ✅ |
| Consistência | tb_chamado_v3 | DT_RESOLUCAO | Status RESOLVIDO/ENCERRADO tem data de resolução | ✅ |
| Consistência | tb_chamado_v3 | ID_CANAL | Chamado não usa tb_canal_atendimento inativo (RN02) | ✅ |
| Consistência | tb_chamado_v3 | ID_SUBCATEGORIA | Chamado não usa tb_subcategoria inativo (RN02) | ✅ |
| Consistência | tb_chamado_v3 | NR_LATITUDE, NR_LONGITUDE | Coordenada a ≤ 5 km do bairro do logradouro | ❌ 738 |
| Consistência | tb_chamado_v3 | NR_SCORE_PRIORIDADE | Score dentro da faixa esperada para a prioridade-base da subcategoria | ✅ |
| Consistência | tb_cidadao | DS_EMAIL | E-mail derivado do nome sem erro de transliteração | ❌ 2 |
| Consistência | tb_cidadao | DT_NASCIMENTO | Idade plausível (16–110 anos na data de corte) | ✅ |
| Consistência entre artefatos | DDL | - | Toda tabela do modelo tem massa de dados | ❌ 6 |
| Consistência entre artefatos | gerar_dados_expandidos.py | CSV_ORIGEM | Arquivo de entrada do gerador existe no repositório | ❌ 1 |
| Consistência entre artefatos | gerar_dados_expandidos.py | PRIORIDADE_BASE_POR_SUBCAT | Prioridade-base do gerador = tb_subcategoria | ✅ |
| Consistência entre artefatos | tb_bairro | - | Colunas do CSV existem em T_URB_BAIRRO | ✅ |
| Consistência entre artefatos | tb_bairro | - | Colunas NOT NULL de T_URB_BAIRRO presentes no CSV | ✅ |
| Consistência entre artefatos | tb_canal_atendimento | - | Colunas do CSV existem em T_URB_CANAL_ATENDIMENTO | ✅ |
| Consistência entre artefatos | tb_canal_atendimento | - | Colunas NOT NULL de T_URB_CANAL_ATENDIMENTO presentes no CSV | ✅ |
| Consistência entre artefatos | tb_categoria | - | Colunas do CSV existem em T_URB_CATEGORIA | ✅ |
| Consistência entre artefatos | tb_categoria | - | Colunas NOT NULL de T_URB_CATEGORIA presentes no CSV | ✅ |
| Consistência entre artefatos | tb_chamado_v3 | - | Colunas NOT NULL de T_URB_CHAMADO presentes no CSV | ✅ |
| Consistência entre artefatos | tb_chamado_v3 | DT_RESOLUCAO | Colunas do CSV existem em T_URB_CHAMADO | ❌ 1 |
| Consistência entre artefatos | tb_cidadao | - | Colunas do CSV existem em T_URB_CIDADAO | ✅ |
| Consistência entre artefatos | tb_cidadao | - | Colunas NOT NULL de T_URB_CIDADAO presentes no CSV | ✅ |
| Consistência entre artefatos | tb_cidade | - | Colunas do CSV existem em T_URB_CIDADE | ✅ |
| Consistência entre artefatos | tb_cidade | - | Colunas NOT NULL de T_URB_CIDADE presentes no CSV | ✅ |
| Consistência entre artefatos | tb_equipe | - | Colunas do CSV existem em T_URB_EQUIPE | ✅ |
| Consistência entre artefatos | tb_equipe | - | Colunas NOT NULL de T_URB_EQUIPE presentes no CSV | ✅ |
| Consistência entre artefatos | tb_estado | - | Colunas do CSV existem em T_URB_ESTADO | ✅ |
| Consistência entre artefatos | tb_estado | - | Colunas NOT NULL de T_URB_ESTADO presentes no CSV | ✅ |
| Consistência entre artefatos | tb_gestor | - | Colunas do CSV existem em T_URB_GESTOR | ✅ |
| Consistência entre artefatos | tb_gestor | - | Colunas NOT NULL de T_URB_GESTOR presentes no CSV | ✅ |
| Consistência entre artefatos | tb_logradouro | - | Colunas do CSV existem em T_URB_LOGRADOURO | ✅ |
| Consistência entre artefatos | tb_logradouro | - | Colunas NOT NULL de T_URB_LOGRADOURO presentes no CSV | ✅ |
| Consistência entre artefatos | tb_subcategoria | - | Colunas do CSV existem em T_URB_SUBCATEGORIA | ✅ |
| Consistência entre artefatos | tb_subcategoria | - | Colunas NOT NULL de T_URB_SUBCATEGORIA presentes no CSV | ✅ |
| Consistência temporal | tb_chamado_v3 | DT_PRAZO_ESTIMADO | Prazo ≥ abertura | ✅ |
| Consistência temporal | tb_chamado_v3 | DT_RESOLUCAO | Resolução ≥ abertura | ✅ |
| Consistência temporal | tb_chamado_v3 | DT_RESOLUCAO | Resolução ≤ data de corte do dataset (2026-01-31) | ❌ 10 |
| Integridade referencial | tb_bairro | ID_BAIRRO | Registro-pai referenciado por ao menos um filho | ❌ 5 |
| Integridade referencial | tb_bairro | ID_CIDADE | FK → tb_cidade.ID_CIDADE | ✅ |
| Integridade referencial | tb_canal_atendimento | ID_CANAL | Registro-pai referenciado por ao menos um filho | ✅ |
| Integridade referencial | tb_categoria | ID_CATEGORIA | Registro-pai referenciado por ao menos um filho | ✅ |
| Integridade referencial | tb_chamado_v3 | ID_CANAL | FK → tb_canal_atendimento.ID_CANAL | ✅ |
| Integridade referencial | tb_chamado_v3 | ID_CIDADAO | FK → tb_cidadao.ID_CIDADAO | ✅ |
| Integridade referencial | tb_chamado_v3 | ID_LOGRADOURO | FK → tb_logradouro.ID_LOGRADOURO | ✅ |
| Integridade referencial | tb_chamado_v3 | ID_SUBCATEGORIA | FK → tb_subcategoria.ID_SUBCATEGORIA | ✅ |
| Integridade referencial | tb_cidadao | ID_CIDADAO | Registro-pai referenciado por ao menos um filho | ✅ |
| Integridade referencial | tb_cidade | ID_CIDADE | Registro-pai referenciado por ao menos um filho | ✅ |
| Integridade referencial | tb_cidade | ID_ESTADO | FK → tb_estado.ID_ESTADO | ✅ |
| Integridade referencial | tb_equipe | ID_EQUIPE | Registro-pai referenciado por ao menos um filho | ✅ |
| Integridade referencial | tb_estado | ID_ESTADO | Registro-pai referenciado por ao menos um filho | ❌ 2 |
| Integridade referencial | tb_gestor | ID_EQUIPE | FK → tb_equipe.ID_EQUIPE | ✅ |
| Integridade referencial | tb_logradouro | ID_BAIRRO | FK → tb_bairro.ID_BAIRRO | ✅ |
| Integridade referencial | tb_logradouro | ID_LOGRADOURO | Registro-pai referenciado por ao menos um filho | ✅ |
| Integridade referencial | tb_subcategoria | ID_CATEGORIA | FK → tb_categoria.ID_CATEGORIA | ✅ |
| Integridade referencial | tb_subcategoria | ID_SUBCATEGORIA | Registro-pai referenciado por ao menos um filho | ✅ |
| Plausibilidade | tb_chamado_v3 | DT_ABERTURA | Volume mensal contínuo (≥ 20% da mediana) | ❌ 10 |
| Plausibilidade | tb_chamado_v3 | ST_CHAMADO | Chamado não finalizado com prazo vencido há > 90 dias | ❌ 451 |
| Unicidade | tb_bairro | ID_BAIRRO | Chave primária única | ✅ |
| Unicidade | tb_canal_atendimento | ID_CANAL | Chave primária única | ✅ |
| Unicidade | tb_canal_atendimento | NM_CANAL | Restrição UNIQUE | ✅ |
| Unicidade | tb_categoria | ID_CATEGORIA | Chave primária única | ✅ |
| Unicidade | tb_chamado_v3 | DS_CHAMADO | Descrição do chamado não repetida | ❌ 1000 |
| Unicidade | tb_chamado_v3 | NR_CHAMADO | Chave primária única | ✅ |
| Unicidade | tb_cidadao | ID_CIDADAO | Chave primária única | ✅ |
| Unicidade | tb_cidadao | NR_CPF_CIDADAO | Restrição UNIQUE | ✅ |
| Unicidade | tb_cidade | ID_CIDADE | Chave primária única | ✅ |
| Unicidade | tb_equipe | ID_EQUIPE | Chave primária única | ✅ |
| Unicidade | tb_estado | ID_ESTADO | Chave primária única | ✅ |
| Unicidade | tb_gestor | ID_GESTOR | Chave primária única | ✅ |
| Unicidade | tb_gestor | NR_MATRICULA | Restrição UNIQUE | ✅ |
| Unicidade | tb_logradouro | ID_LOGRADOURO | Chave primária única | ✅ |
| Unicidade | tb_subcategoria | ID_SUBCATEGORIA | Chave primária única | ✅ |
| Validade | tb_bairro | ID_BAIRRO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_bairro | ID_BAIRRO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_bairro | ID_CIDADE | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_bairro | ID_CIDADE | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_bairro | NM_BAIRRO | Tamanho cabe em VARCHAR2(60) (bytes UTF-8) | ✅ |
| Validade | tb_bairro | NM_BAIRRO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_bairro | NM_ZONA_BAIRRO | Tamanho cabe em VARCHAR2(30) (bytes UTF-8) | ✅ |
| Validade | tb_bairro | NM_ZONA_BAIRRO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_bairro | NM_ZONA_BAIRRO | Zona em ['Centro', 'Leste', 'Norte', 'Oeste', 'Sul'] | ✅ |
| Validade | tb_canal_atendimento | DS_CANAL | Tamanho cabe em VARCHAR2(200) (bytes UTF-8) | ✅ |
| Validade | tb_canal_atendimento | DS_CANAL | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_canal_atendimento | ID_CANAL | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_canal_atendimento | ID_CANAL | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_canal_atendimento | NM_CANAL | Tamanho cabe em VARCHAR2(40) (bytes UTF-8) | ✅ |
| Validade | tb_canal_atendimento | NM_CANAL | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_canal_atendimento | ST_ATIVO | Tamanho cabe em CHAR(1) (bytes UTF-8) | ✅ |
| Validade | tb_canal_atendimento | ST_ATIVO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_canal_atendimento | ST_ATIVO | CHECK IN (S, N) | ✅ |
| Validade | tb_categoria | DS_CATEGORIA | Tamanho cabe em VARCHAR2(200) (bytes UTF-8) | ✅ |
| Validade | tb_categoria | DS_CATEGORIA | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_categoria | ID_CATEGORIA | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_categoria | ID_CATEGORIA | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_categoria | NM_CATEGORIA | Tamanho cabe em VARCHAR2(80) (bytes UTF-8) | ✅ |
| Validade | tb_categoria | NM_CATEGORIA | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_categoria | ST_ATIVO | Tamanho cabe em CHAR(1) (bytes UTF-8) | ✅ |
| Validade | tb_categoria | ST_ATIVO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_categoria | ST_ATIVO | CHECK IN (S, N) | ✅ |
| Validade | tb_chamado_v3 | DS_CHAMADO | Tamanho cabe em VARCHAR2(500) (bytes UTF-8) | ✅ |
| Validade | tb_chamado_v3 | DS_CHAMADO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_chamado_v3 | DT_ABERTURA | Data no formato AAAA-MM-DD | ✅ |
| Validade | tb_chamado_v3 | DT_PRAZO_ESTIMADO | Data no formato AAAA-MM-DD | ✅ |
| Validade | tb_chamado_v3 | ID_CANAL | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_chamado_v3 | ID_CANAL | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_chamado_v3 | ID_CIDADAO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_chamado_v3 | ID_CIDADAO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_chamado_v3 | ID_LOGRADOURO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_chamado_v3 | ID_LOGRADOURO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_chamado_v3 | ID_SUBCATEGORIA | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_chamado_v3 | ID_SUBCATEGORIA | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_chamado_v3 | NR_CHAMADO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_chamado_v3 | NR_CHAMADO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_chamado_v3 | NR_LATITUDE | Valor numérico (NUMBER(10,7)) | ✅ |
| Validade | tb_chamado_v3 | NR_LATITUDE | Precisão cabe em NUMBER(10,7) | ✅ |
| Validade | tb_chamado_v3 | NR_LATITUDE | CHECK BETWEEN -90 AND 90 | ✅ |
| Validade | tb_chamado_v3 | NR_LONGITUDE | Valor numérico (NUMBER(10,7)) | ✅ |
| Validade | tb_chamado_v3 | NR_LONGITUDE | Precisão cabe em NUMBER(10,7) | ✅ |
| Validade | tb_chamado_v3 | NR_LONGITUDE | CHECK BETWEEN -180 AND 180 | ✅ |
| Validade | tb_chamado_v3 | NR_SCORE_PRIORIDADE | Valor numérico (NUMBER(3,0)) | ✅ |
| Validade | tb_chamado_v3 | NR_SCORE_PRIORIDADE | Precisão cabe em NUMBER(3,0) | ✅ |
| Validade | tb_chamado_v3 | NR_SCORE_PRIORIDADE | CHECK BETWEEN 0 AND 100 | ✅ |
| Validade | tb_chamado_v3 | ST_CHAMADO | Tamanho cabe em VARCHAR2(20) (bytes UTF-8) | ✅ |
| Validade | tb_chamado_v3 | ST_CHAMADO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_chamado_v3 | ST_CHAMADO | CHECK IN (ABERTO, EM_ANALISE, EM_ATENDIMENTO, RESOLVIDO, ENCERRADO) | ✅ |
| Validade | tb_cidadao | DS_EMAIL | Tamanho cabe em VARCHAR2(100) (bytes UTF-8) | ✅ |
| Validade | tb_cidadao | DS_EMAIL | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_cidadao | DS_EMAIL | E-mail em formato válido | ✅ |
| Validade | tb_cidadao | DT_NASCIMENTO | Data no formato AAAA-MM-DD | ✅ |
| Validade | tb_cidadao | ID_CIDADAO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_cidadao | ID_CIDADAO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_cidadao | NM_CIDADAO | Tamanho cabe em VARCHAR2(100) (bytes UTF-8) | ✅ |
| Validade | tb_cidadao | NM_CIDADAO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_cidadao | NR_CPF_CIDADAO | Valor numérico (NUMBER(11,0)) | ✅ |
| Validade | tb_cidadao | NR_CPF_CIDADAO | Precisão cabe em NUMBER(11,0) | ✅ |
| Validade | tb_cidadao | NR_CPF_CIDADAO | CPF com dígitos verificadores válidos | ❌ 50 |
| Validade | tb_cidadao | NR_TELEFONE | Tamanho cabe em VARCHAR2(30) (bytes UTF-8) | ✅ |
| Validade | tb_cidadao | NR_TELEFONE | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_cidadao | NR_TELEFONE | Telefone só com dígitos, 10 ou 11 posições (DDD + número) | ✅ |
| Validade | tb_cidadao | NR_TELEFONE | Celular com 9º dígito (11 posições) | ✅ |
| Validade | tb_cidade | ID_CIDADE | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_cidade | ID_CIDADE | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_cidade | ID_ESTADO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_cidade | ID_ESTADO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_cidade | NM_CIDADE | Tamanho cabe em VARCHAR2(60) (bytes UTF-8) | ✅ |
| Validade | tb_cidade | NM_CIDADE | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_equipe | DS_ESPECIALIDADE | Tamanho cabe em VARCHAR2(200) (bytes UTF-8) | ✅ |
| Validade | tb_equipe | DS_ESPECIALIDADE | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_equipe | ID_EQUIPE | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_equipe | ID_EQUIPE | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_equipe | NM_EQUIPE | Tamanho cabe em VARCHAR2(80) (bytes UTF-8) | ✅ |
| Validade | tb_equipe | NM_EQUIPE | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_equipe | ST_ATIVO | Tamanho cabe em CHAR(1) (bytes UTF-8) | ✅ |
| Validade | tb_equipe | ST_ATIVO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_equipe | ST_ATIVO | CHECK IN (S, N) | ✅ |
| Validade | tb_estado | ID_ESTADO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_estado | ID_ESTADO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_estado | NM_ESTADO | Tamanho cabe em VARCHAR2(40) (bytes UTF-8) | ✅ |
| Validade | tb_estado | NM_ESTADO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_estado | SG_ESTADO | Tamanho cabe em CHAR(2) (bytes UTF-8) | ✅ |
| Validade | tb_estado | SG_ESTADO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_estado | SG_ESTADO | UF válida | ✅ |
| Validade | tb_gestor | DS_CARGO | Tamanho cabe em VARCHAR2(60) (bytes UTF-8) | ✅ |
| Validade | tb_gestor | DS_CARGO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_gestor | ID_EQUIPE | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_gestor | ID_EQUIPE | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_gestor | ID_GESTOR | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_gestor | ID_GESTOR | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_gestor | NM_GESTOR | Tamanho cabe em VARCHAR2(100) (bytes UTF-8) | ✅ |
| Validade | tb_gestor | NM_GESTOR | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_gestor | NR_MATRICULA | Tamanho cabe em VARCHAR2(20) (bytes UTF-8) | ✅ |
| Validade | tb_gestor | NR_MATRICULA | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_gestor | NR_TELEFONE | Tamanho cabe em VARCHAR2(30) (bytes UTF-8) | ✅ |
| Validade | tb_gestor | NR_TELEFONE | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_gestor | NR_TELEFONE | Telefone só com dígitos, 10 ou 11 posições (DDD + número) | ✅ |
| Validade | tb_gestor | NR_TELEFONE | Celular com 9º dígito (11 posições) | ❌ 15 |
| Validade | tb_logradouro | DS_COMPLEMENTO | Tamanho cabe em VARCHAR2(50) (bytes UTF-8) | ✅ |
| Validade | tb_logradouro | DS_COMPLEMENTO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_logradouro | ID_BAIRRO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_logradouro | ID_BAIRRO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_logradouro | ID_LOGRADOURO | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_logradouro | ID_LOGRADOURO | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_logradouro | NM_LOGRADOURO | Tamanho cabe em VARCHAR2(120) (bytes UTF-8) | ✅ |
| Validade | tb_logradouro | NM_LOGRADOURO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_logradouro | NR_CEP | Valor numérico (NUMBER(8,0)) | ✅ |
| Validade | tb_logradouro | NR_CEP | Precisão cabe em NUMBER(8,0) | ✅ |
| Validade | tb_logradouro | NR_CEP | CEP com 8 dígitos | ❌ 20 |
| Validade | tb_subcategoria | ID_CATEGORIA | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_subcategoria | ID_CATEGORIA | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_subcategoria | ID_SUBCATEGORIA | Valor numérico (NUMBER(10,0)) | ✅ |
| Validade | tb_subcategoria | ID_SUBCATEGORIA | Precisão cabe em NUMBER(10,0) | ✅ |
| Validade | tb_subcategoria | NM_SUBCATEGORIA | Tamanho cabe em VARCHAR2(100) (bytes UTF-8) | ✅ |
| Validade | tb_subcategoria | NM_SUBCATEGORIA | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_subcategoria | NR_PRIORIDADE_BASE | Valor numérico (NUMBER(1,0)) | ✅ |
| Validade | tb_subcategoria | NR_PRIORIDADE_BASE | Precisão cabe em NUMBER(1,0) | ✅ |
| Validade | tb_subcategoria | NR_PRIORIDADE_BASE | CHECK BETWEEN 1 AND 5 | ✅ |
| Validade | tb_subcategoria | ST_ATIVO | Tamanho cabe em CHAR(1) (bytes UTF-8) | ✅ |
| Validade | tb_subcategoria | ST_ATIVO | Sem espaços extras (início/fim/duplos) | ✅ |
| Validade | tb_subcategoria | ST_ATIVO | CHECK IN (S, N) | ✅ |
