-- ============================================================
-- PBL FASE 4 - 2ª ENTREGA: INSTRUÇÃO SQL (JOIN + FILTRO DE LINHA)
-- Projeto: Cidade Alfa - Avaliações de Pontos Turísticos
-- Aluno:   Thiago Fiel de Oliveira | RM 570088 | FIAP
-- ------------------------------------------------------------
-- Pergunta de negócio (Q2):
--   "Determinados bairros da cidade Alfa concentram avaliações
--    mais altas dos pontos turísticos?"
--
-- Técnica: JUNÇÃO (JOIN) entre 4 tabelas + FILTRO DE LINHA.
--          SEM agrupamento (GROUP BY) - a agregação é feita
--          depois, em Python (Fase 4 - 3ª entrega).
--
-- Cadeia de JOINs:
--   ALFA_LOCALIZACAO (bairro)
--     -> ALFA_PONTO_TURISTICO (ponto + lat/long)
--     -> ALFA_EVENTO_PONTO_TURISTICO (preço)
--     -> ALFA_AVALIACAO (nota dada pela pessoa)
--
-- Filtro de linha: apenas pontos turísticos e eventos ATIVOS.
--   (A limpeza de notas nulas/negativas é feita na etapa Python,
--    seguindo o fluxo do exercício guiado.)
-- ============================================================

SELECT loc.nm_bairro,
       pt.nm_ponto_turistico,
       pt.nr_latitude,
       pt.nr_longitude,
       ept.vl_preco_unitario,
       av.dt_avaliacao,
       av.nr_nota_avaliacao
FROM ALFA_LOCALIZACAO loc
JOIN ALFA_PONTO_TURISTICO pt
    ON pt.id_localizacao = loc.id_localizacao
JOIN ALFA_EVENTO_PONTO_TURISTICO ept
    ON ept.id_ponto_turistico = pt.id_ponto_turistico
JOIN ALFA_AVALIACAO av
    ON av.id_evento_ponto_turistico = ept.id_evento_ponto_turistico
WHERE pt.st_ponto_turistico = 'A'
  AND ept.st_evento = 'A'
ORDER BY loc.nm_bairro, pt.nm_ponto_turistico, av.dt_avaliacao;
