-- ============================================================
-- CONSULTAS DE EVIDENCIA - PBL FASE 6
-- Apoio para gerar os prints do PDF. Nao faz parte da entrega.
-- Execute uma consulta por vez (Ctrl+Enter) e capture a tela
-- com o comando e o resultado visiveis.
-- ============================================================

-- [01] Tabelas de origem carregadas (esperado: 100 e 100)
SELECT 'T_SRC_PREFEITURA_CIDADAO' AS tabela, COUNT(*) AS linhas FROM t_src_prefeitura_cidadao
UNION ALL
SELECT 'T_SRC_RECEITA_FEDERAL', COUNT(*) FROM t_src_receita_federal;

-- [02] ANTES: rodar o cria_mdm_cidadao.sql e o script v1 (F5) e depois esta consulta
--      (esperado: NR_IDADE, NM_FAIXA_ETARIA, NM_SEXO e NM_ESCOLARIDADE nulos)
SELECT * FROM t_mdm_cidadao ORDER BY id_gold_cidadao;

-- [03] Rodar o cria_mdm_cidadao.sql e o script v2 (F5) e capturar a saida do script
--      (esperado: 100 lidos, 100 inseridos, 0 atualizados, 0 erros)

-- [04] DEPOIS: as mesmas colunas agora preenchidas
SELECT * FROM t_mdm_cidadao ORDER BY id_gold_cidadao;

-- [05] Conferencia das colunas novas
--      (esperado: 100 linhas, 94 com idade e faixa, 100 com sexo e escolaridade)
SELECT COUNT(*)               AS linhas,
       COUNT(nr_idade)        AS com_idade,
       COUNT(nm_faixa_etaria) AS com_faixa_etaria,
       COUNT(nm_sexo)         AS com_sexo,
       COUNT(nm_escolaridade) AS com_escolaridade
FROM   t_mdm_cidadao;

-- [06] Divergencias (esperado: NAO 67, SIM 33)
SELECT fl_divergencia, COUNT(*) AS qtde_cidadaos
FROM   t_mdm_cidadao
GROUP BY fl_divergencia
ORDER BY fl_divergencia;

-- [07] Exemplos de divergencia tratada: sexo diferente entre as origens
--      e cidadaos sem data de nascimento valida (esperado: 7 linhas)
SELECT nr_cpf_cidadao_mascara, nm_cidadao, nr_idade, nm_faixa_etaria, nm_sexo, ds_divergencia
FROM   t_mdm_cidadao
WHERE  dt_nascimento IS NULL
OR     ds_divergencia LIKE '%Sexo%'
ORDER BY nm_cidadao;

-- [08] Rodar o script v2 de novo (F5), sem recriar a tabela, e capturar a saida
--      (esperado: 100 lidos, 0 inseridos, 100 atualizados, 0 erros)

-- [09] Rodar o cria_view_qtd_total_fx_etaria_escolaridade.sql (F5) e capturar
--      a criacao da view e o resultado (esperado: 16 linhas, soma 100)
