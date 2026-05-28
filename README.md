<div align="center">

# UrbanIQ

### Plataforma Inteligente de Gestão de Chamados Urbanos

*Transformando dados urbanos em decisões inteligentes — com priorização automática, transparência em tempo real e melhoria contínua dos serviços públicos.*

<br>

![Status](https://img.shields.io/badge/status-em%20desenvolvimento-C4A882?style=for-the-badge)
![Fase](https://img.shields.io/badge/fase-3%20de%207-3D3630?style=for-the-badge)
![Licença](https://img.shields.io/badge/licença-acadêmica-F9F6F0?style=for-the-badge&labelColor=3D3630)

![Oracle](https://img.shields.io/badge/Oracle_21c-F80000?style=flat-square&logo=oracle&logoColor=white)
![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=flat-square&logo=databricks&logoColor=white)
![Delta Lake](https://img.shields.io/badge/Delta_Lake-00ADD4?style=flat-square&logo=delta&logoColor=white)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=flat-square&logo=powerbi&logoColor=black)
![SQL](https://img.shields.io/badge/SQL-336791?style=flat-square&logo=postgresql&logoColor=white)

</div>

---

## Sobre o Projeto

**UrbanIQ** é uma plataforma de dados que centraliza, prioriza e dá transparência aos chamados urbanos de uma cidade. Em vez de pedidos de serviço público que se perdem entre canais desconexos, o UrbanIQ unifica as solicitações dos cidadãos, prioriza automaticamente por impacto e urgência e devolve à população acompanhamento em tempo real — reconstruindo a confiança entre cidadão e gestão pública.

O projeto nasce do **Desafio 3 — Participação Cidadã e Serviços Públicos** da cidade fictícia *Alfa*, no contexto do PBL (*Project Based Learning*) da FIAP, e é desenvolvido como um **pipeline de dados completo de 7 fases**, da descoberta do problema à entrega de um produto de dados com impacto social.

> **Visão de produto:** ser a ponte inteligente entre o problema do cidadão e a ação da gestão pública, orientada por dados.

---

## O Problema

A persona central do projeto é **Fernanda Borges**, 34 anos, cidadã que registra um chamado de infraestrutura e enfrenta uma jornada de frustração:

| Dor | Consequência |
|-----|--------------|
| Falta de retorno e acompanhamento | Cidadão sem saber o andamento do pedido |
| Informações inconsistentes entre canais | Perda de confiança no serviço público |
| Demora na resolução | Riscos urbanos persistem por meses |
| Baixa transparência e previsibilidade | Desengajamento da população |

**Diagnóstico raiz:** a falha não está só na operação, mas na ausência de uso inteligente dos dados para priorizar, analisar e decidir.

---

## A Solução

| O UrbanIQ **é** | O UrbanIQ **faz** |
|----------------|-------------------|
| Plataforma inteligente de gestão de chamados | Centraliza dados de múltiplos canais |
| Sistema orientado por dados para decisão | Classifica e prioriza chamados automaticamente |
| Solução integrada cidadão ↔ gestão pública | Permite acompanhamento em tempo real |
| Ferramenta de priorização por impacto e urgência | Gera insights e identifica tendências urbanas |

---

## Arquitetura de Dados Distribuída

A arquitetura separa **dados sensíveis** (on-premise, sob LGPD) de **dados massivos** (nuvem), com processamento em **arquitetura medalhão** (Bronze, Prata, Ouro):

<div align="center">

![Arquitetura de Dados do UrbanIQ](docs/assets/arquitetura.png)

</div>

**Princípios de design:**

- **Privacidade by design** — CPF, endereço e dados biométricos isolados on-premise, em conformidade com a LGPD.
- **Escalabilidade** — camada de nuvem preparada para grandes volumes (sensores, logs, eventos) e acessos simultâneos.
- **Tempo real** — *event stream* para notificação automática de chamados críticos (score elevado).

---

## Modelo de Dados

Modelo físico relacional em **Oracle Database 21c**, normalizado até a **3ª Forma Normal**.

<div align="center">

| Métrica | Valor |
|---------|:-----:|
| Tabelas | **15** |
| Chaves estrangeiras | **17** |
| Sequences | **14** |
| Índices de performance | **7** |
| Prefixo padrão | `T_URB_` |

</div>

**Tabela central:** `T_URB_CHAMADO` — armazena cada chamado urbano com `NR_SCORE_PRIORIDADE` (0–100, calculado pelo motor de priorização) e ciclo de status `ABERTO → EM_ANALISE → EM_ATENDIMENTO → RESOLVIDO → ENCERRADO`.

**Domínios principais:**

- **Endereço hierárquico:** `ESTADO → CIDADE → BAIRRO → LOGRADOURO`, com relação N:N entre cidadão e logradouro (histórico de endereços).
- **Classificação:** `CATEGORIA → SUBCATEGORIA` (com prioridade base 1–5).
- **Atendimento:** `EQUIPE → GESTOR → ATENDIMENTO`, equipes especializadas por tipo de ocorrência.
- **Rastreabilidade:** `HISTORICO_STATUS` (base do Portal de Transparência e dos indicadores de SLA).
- **Feedback:** `AVALIACAO` (nota 1–5, restrita a chamados resolvidos/encerrados).

### Regras de Negócio

| Regra | Descrição |
|:-----:|-----------|
| **RN01** | Normalização hierárquica de endereços + relação N:N cidadão–logradouro |
| **RN02** | Classificação obrigatória Categoria → Subcategoria, com prioridade base |
| **RN03** | Todo chamado registra histórico completo de mudanças de status (transparência + SLA) |
| **RN04** | Cada chamado é atendido por um gestor de equipe especializada |
| **RN05** | Avaliação permitida apenas em chamados resolvidos/encerrados, máx. 1 por chamado |

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Modelagem | Oracle SQL Data Modeler |
| Banco transacional | Oracle Database 21c |
| Big Data / Lakehouse | Databricks Community Edition · Delta Lake |
| Arquitetura de armazenamento | Medalhão (Bronze · Prata · Ouro) |
| Persistência NoSQL (projetada) | MongoDB (geoespacial 2dsphere) · Redis (cache de score, TTL) · Apache Kafka (eventos) |
| Visualização | Power BI |
| Linguagem | SQL |

---

## Estrutura do Repositório

```
UrbanIQ/
├── README.md
├── docs/
│   └── assets/                      # Imagens do README (diagramas, prints)
│
├── fase1-descoberta/
│   ├── docs/                        # Persona, mapa de empatia, jornada, visão de produto, regras
│   └── modelo-conceitual/           # DER conceitual (Oracle Data Modeler)
│
├── fase2-modelagem/
│   ├── docs/                        # Documentos da fase (componentes, regras de negócio)
│   ├── relacional/
│   │   ├── ddl/                     # Script DDL (15 tabelas, 14 sequences, 7 índices)
│   │   └── modelo/                  # Projeto físico Oracle Data Modeler (.dmd)
│   └── nosql/                       # Arquitetura de dados não estruturados
│
└── fase3-ingestao/
    ├── docs/                        # Arquitetura distribuída e evidências
    ├── data/
    │   └── raw/                     # 10 datasets de carga inicial (modelo T_URB_)
    └── databricks/
        ├── notebooks/               # Notebooks do Databricks
        └── sql/                     # Instruções SQL executadas (tabelas Delta)
```

---

## Roadmap — Pipeline de 7 Fases

| Fase | Etapa | Status |
|:----:|-------|:------:|
| **1** | Descoberta e Contexto (*Design Thinking*) | Concluída |
| **2** | Modelagem e Arquitetura (conceitual → físico) | Concluída |
| **3** | Coleta, Ingestão e Persistência (Big Data) | Concluída |
| **4** | Exploração e Preparação de Dados | Próxima |
| **5** | Modelagem Analítica e Visualização | Planejada |
| **6** | Engenharia e Governança de Dados | Planejada |
| **7** | Produto de Dados e Impacto Social | Planejada |

---

## Autor

**Thiago Fiel de Oliveira**
Data Science · FIAP · Turma 1TSCO
Grupo **DataGuy**

---

<div align="center">

*UrbanIQ — porque toda cidade inteligente precisa de uma infraestrutura inteligente de dados.*

</div>
