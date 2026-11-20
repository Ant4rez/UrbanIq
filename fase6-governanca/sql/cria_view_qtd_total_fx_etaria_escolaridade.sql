-- ============================================================
-- VIEW LOGICA ANALITICA
-- Projeto  : Cidade Alfa  Master Data Management
-- Objetivo : Exibir a quantidade total da populacao agrupada
--            por faixa etaria e escolaridade
-- Origem   : T_MDM_CIDADAO (tabela de dados mestres)
--
-- GRUPO: DataGuy
-- COMPONENTES EM ORDEM ALFABETICA          RM
-- Thiago Fiel de Oliveira                  570088
--
-- Ordenacao: da maior para a menor quantidade, para que os
-- maiores grupos da populacao aparecam primeiro. Faixa etaria e
-- escolaridade entram como desempate, mantendo sempre a mesma
-- ordem entre grupos com a mesma quantidade.
-- Cidadaos sem data de nascimento valida ficam com a faixa
-- etaria nula na T_MDM_CIDADAO e aparecem como NAO_INFORMADO.
-- ============================================================

CREATE OR REPLACE VIEW V_MDM_FX_ETARIA_ESCOLARIDADE AS
SELECT  NVL(nm_faixa_etaria, 'NAO_INFORMADO') AS nm_faixa_etaria,
        NVL(nm_escolaridade, 'NAO_INFORMADO') AS nm_escolaridade,
        COUNT(*)                              AS qtde_cidadaos
FROM    t_mdm_cidadao
GROUP BY NVL(nm_faixa_etaria, 'NAO_INFORMADO'),
         NVL(nm_escolaridade, 'NAO_INFORMADO')
ORDER BY qtde_cidadaos DESC,
         NVL(nm_faixa_etaria, 'NAO_INFORMADO'),
         NVL(nm_escolaridade, 'NAO_INFORMADO');

-- Execucao da view para analise do resultado
SELECT  *
FROM    V_MDM_FX_ETARIA_ESCOLARIDADE;
