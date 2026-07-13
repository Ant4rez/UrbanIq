-- ============================================================
-- PROJETO FÍSICO DE BANCO DE DADOS - PATCH v2
-- Sistema: UrbanIQ - Plataforma de Gestão de Chamados Urbanos
-- Aluno:   Thiago Fiel de Oliveira | RM 570088
-- Curso:   Data Science - FIAP | Complemento da Fase 2 (preparação Fase 4)
-- ------------------------------------------------------------
-- OBJETIVO: este script é um PATCH incremental. Roda EM CIMA do
-- urbaniq_ddl.sql original, sem recriar nada que já existe.
-- Fecha as lacunas identificadas entre o DER conceitual e o DDL
-- físico e cria a estrutura exigida pela RN06 (Motor de Score).
--
-- ORDEM DE EXECUÇÃO (importante):
--   [0] Sequences novas
--   [1] Tabela T_URB_CANAL_ATENDIMENTO + carga inicial
--   [2] Colunas novas em T_URB_CHAMADO (canal, prazo, geo) + FK
--   [3] Tabela T_URB_SCORE_OVERRIDE + FKs
--   [4] Trigger RN05 (avaliação só em chamado RESOLVIDO/ENCERRADO)
--   [5] Trigger RN02 (chamado bloqueado em subcategoria inativa)
--   [6] Índices novos
-- ============================================================


-- ============================================================
-- [0] SEQUENCES NOVAS
-- ============================================================

CREATE SEQUENCE SQ_URB_CANAL     START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;
CREATE SEQUENCE SQ_URB_OVERRIDE  START WITH 1 INCREMENT BY 1 NOCACHE NOCYCLE;


-- ============================================================
-- [1] T_URB_CANAL_ATENDIMENTO
-- Estava no DER conceitual (Fase 1) e não foi para o DDL físico.
-- Registra a origem de cada chamado (dado estratégico de gestão).
-- ============================================================

CREATE TABLE T_URB_CANAL_ATENDIMENTO (
    ID_CANAL    NUMBER(10)    NOT NULL,
    NM_CANAL    VARCHAR2(40)  NOT NULL,
    DS_CANAL    VARCHAR2(200),
    ST_ATIVO    CHAR(1)       DEFAULT 'S' NOT NULL,
    CONSTRAINT PK_T_URB_CANAL     PRIMARY KEY (ID_CANAL),
    CONSTRAINT UK_URB_CANAL_NOME  UNIQUE (NM_CANAL),
    CONSTRAINT CK_URB_CANAL_ATIVO CHECK (ST_ATIVO IN ('S','N'))
);

COMMENT ON TABLE  T_URB_CANAL_ATENDIMENTO          IS 'Canais de origem dos chamados (app, web, telefone, sensores)';
COMMENT ON COLUMN T_URB_CANAL_ATENDIMENTO.ID_CANAL IS 'Identificador único do canal de atendimento';
COMMENT ON COLUMN T_URB_CANAL_ATENDIMENTO.NM_CANAL IS 'Nome do canal (ex: APP_MOBILE, PORTAL_WEB)';
COMMENT ON COLUMN T_URB_CANAL_ATENDIMENTO.DS_CANAL IS 'Descrição do canal de origem';
COMMENT ON COLUMN T_URB_CANAL_ATENDIMENTO.ST_ATIVO IS 'Status: S=ativo, N=inativo';

-- Carga inicial dos 5 canais previstos na arquitetura (Fase 3)
INSERT INTO T_URB_CANAL_ATENDIMENTO (ID_CANAL, NM_CANAL, DS_CANAL, ST_ATIVO)
    VALUES (SQ_URB_CANAL.NEXTVAL, 'APP_MOBILE', 'Aplicativo móvel do cidadão (iOS/Android)', 'S');
INSERT INTO T_URB_CANAL_ATENDIMENTO (ID_CANAL, NM_CANAL, DS_CANAL, ST_ATIVO)
    VALUES (SQ_URB_CANAL.NEXTVAL, 'PORTAL_WEB', 'Portal web da prefeitura', 'S');
INSERT INTO T_URB_CANAL_ATENDIMENTO (ID_CANAL, NM_CANAL, DS_CANAL, ST_ATIVO)
    VALUES (SQ_URB_CANAL.NEXTVAL, 'TELEFONE', 'Central telefônica 156', 'S');
INSERT INTO T_URB_CANAL_ATENDIMENTO (ID_CANAL, NM_CANAL, DS_CANAL, ST_ATIVO)
    VALUES (SQ_URB_CANAL.NEXTVAL, 'SENSOR_IOT', 'Sensor IoT urbano (detecção automática)', 'S');
INSERT INTO T_URB_CANAL_ATENDIMENTO (ID_CANAL, NM_CANAL, DS_CANAL, ST_ATIVO)
    VALUES (SQ_URB_CANAL.NEXTVAL, 'CAMERA_HD', 'Câmera de monitoramento urbano (visão computacional)', 'S');
COMMIT;


-- ============================================================
-- [2] NOVAS COLUNAS EM T_URB_CHAMADO
-- ID_CANAL          -> origem do chamado (FK)  [nullable: dados antigos não têm canal]
-- DT_PRAZO_ESTIMADO -> SLA que existia no DER e sumiu no DDL
-- NR_LATITUDE/LONG  -> ponto exato p/ Mapa de Ocorrências (Fase 5)
-- ============================================================

ALTER TABLE T_URB_CHAMADO ADD (
    ID_CANAL          NUMBER(10),
    DT_PRAZO_ESTIMADO DATE,
    NR_LATITUDE       NUMBER(10,7),
    NR_LONGITUDE      NUMBER(10,7)
);

ALTER TABLE T_URB_CHAMADO
    ADD CONSTRAINT FK_URB_CHAM_CANAL FOREIGN KEY (ID_CANAL)
    REFERENCES T_URB_CANAL_ATENDIMENTO (ID_CANAL);

ALTER TABLE T_URB_CHAMADO
    ADD CONSTRAINT CK_URB_CHAM_LATITUDE  CHECK (NR_LATITUDE  BETWEEN -90  AND 90);
ALTER TABLE T_URB_CHAMADO
    ADD CONSTRAINT CK_URB_CHAM_LONGITUDE CHECK (NR_LONGITUDE BETWEEN -180 AND 180);

COMMENT ON COLUMN T_URB_CHAMADO.ID_CANAL          IS 'FK - canal de origem do chamado (null = chamados legados sem canal)';
COMMENT ON COLUMN T_URB_CHAMADO.DT_PRAZO_ESTIMADO IS 'Prazo estimado de resolução (SLA) exibido no Portal de Transparência';
COMMENT ON COLUMN T_URB_CHAMADO.NR_LATITUDE       IS 'Latitude do ponto exato da ocorrência (mapa de ocorrências)';
COMMENT ON COLUMN T_URB_CHAMADO.NR_LONGITUDE      IS 'Longitude do ponto exato da ocorrência (mapa de ocorrências)';


-- ============================================================
-- [3] T_URB_SCORE_OVERRIDE (RN06 - override manual do gestor)
-- Histórico de ajustes manuais do score. Nunca sobrescreve:
-- cada ajuste gera uma linha com valor anterior, novo e justificativa.
-- ============================================================

CREATE TABLE T_URB_SCORE_OVERRIDE (
    NR_OVERRIDE        NUMBER(10)    NOT NULL,
    NR_CHAMADO         NUMBER(10)    NOT NULL,
    ID_GESTOR          NUMBER(10)    NOT NULL,
    NR_SCORE_ANTERIOR  NUMBER(3)     NOT NULL,
    NR_SCORE_NOVO      NUMBER(3)     NOT NULL,
    DS_JUSTIFICATIVA   VARCHAR2(500) NOT NULL,
    DT_OVERRIDE        DATE          DEFAULT SYSDATE NOT NULL,
    CONSTRAINT PK_T_URB_SCORE_OVERRIDE   PRIMARY KEY (NR_OVERRIDE),
    CONSTRAINT FK_URB_OVR_CHAMADO        FOREIGN KEY (NR_CHAMADO)
        REFERENCES T_URB_CHAMADO (NR_CHAMADO),
    CONSTRAINT FK_URB_OVR_GESTOR         FOREIGN KEY (ID_GESTOR)
        REFERENCES T_URB_GESTOR (ID_GESTOR),
    CONSTRAINT CK_URB_OVR_SCORE_ANT      CHECK (NR_SCORE_ANTERIOR BETWEEN 0 AND 100),
    CONSTRAINT CK_URB_OVR_SCORE_NOVO     CHECK (NR_SCORE_NOVO     BETWEEN 0 AND 100)
);

COMMENT ON TABLE  T_URB_SCORE_OVERRIDE                   IS 'Histórico de ajustes manuais do score de prioridade pelos gestores (RN06)';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.NR_OVERRIDE       IS 'Identificador único do ajuste manual';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.NR_CHAMADO        IS 'FK - chamado cujo score foi ajustado';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.ID_GESTOR         IS 'FK - gestor que realizou o ajuste';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.NR_SCORE_ANTERIOR IS 'Score calculado pelo algoritmo antes do ajuste';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.NR_SCORE_NOVO     IS 'Score definido manualmente pelo gestor';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.DS_JUSTIFICATIVA  IS 'Justificativa obrigatória do ajuste manual';
COMMENT ON COLUMN T_URB_SCORE_OVERRIDE.DT_OVERRIDE       IS 'Data e hora do ajuste';


-- ============================================================
-- [4] TRIGGER RN05 - Enforcement da avaliação
-- Avaliação só é permitida em chamados RESOLVIDO ou ENCERRADO.
-- ============================================================

CREATE OR REPLACE TRIGGER TRG_URB_AVAL_STATUS
BEFORE INSERT ON T_URB_AVALIACAO
FOR EACH ROW
DECLARE
    v_status T_URB_CHAMADO.ST_CHAMADO%TYPE;
BEGIN
    SELECT ST_CHAMADO
      INTO v_status
      FROM T_URB_CHAMADO
     WHERE NR_CHAMADO = :NEW.NR_CHAMADO;

    IF v_status NOT IN ('RESOLVIDO','ENCERRADO') THEN
        RAISE_APPLICATION_ERROR(-20001,
            'RN05: avaliacao permitida apenas para chamados RESOLVIDO ou ENCERRADO. Status atual: ' || v_status);
    END IF;
END;
/


-- ============================================================
-- [5] TRIGGER RN02 - Enforcement de subcategoria ativa
-- Não é permitido abrir chamado em subcategoria inativa.
-- ============================================================

CREATE OR REPLACE TRIGGER TRG_URB_CHAM_SUBCAT_ATIVA
BEFORE INSERT ON T_URB_CHAMADO
FOR EACH ROW
DECLARE
    v_ativo T_URB_SUBCATEGORIA.ST_ATIVO%TYPE;
BEGIN
    SELECT ST_ATIVO
      INTO v_ativo
      FROM T_URB_SUBCATEGORIA
     WHERE ID_SUBCATEGORIA = :NEW.ID_SUBCATEGORIA;

    IF v_ativo = 'N' THEN
        RAISE_APPLICATION_ERROR(-20002,
            'RN02: nao e permitido abrir chamado em subcategoria inativa.');
    END IF;
END;
/


-- ============================================================
-- [6] ÍNDICES NOVOS
-- ============================================================

CREATE INDEX IDX_URB_CHAMADO_CANAL   ON T_URB_CHAMADO (ID_CANAL);
CREATE INDEX IDX_URB_CHAMADO_SUBCAT  ON T_URB_CHAMADO (ID_SUBCATEGORIA);
CREATE INDEX IDX_URB_OVR_CHAMADO     ON T_URB_SCORE_OVERRIDE (NR_CHAMADO);


-- ============================================================
-- FIM DO PATCH v2
-- ACRÉSCIMOS: +2 tabelas | +2 sequences | +3 índices | +2 triggers
-- TOTAL APÓS v2: 17 TABELAS | 16 SEQUENCES | 10 ÍNDICES | 2 TRIGGERS
-- UrbanIQ - FIAP 2026
-- ============================================================
