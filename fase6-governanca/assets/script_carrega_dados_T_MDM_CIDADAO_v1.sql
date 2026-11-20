-- ============================================================
-- BLOCO ANONIMO PL/SQL
-- Projeto  : Cidade Alfa  Master Data Management
-- Objetivo : Carga e transformacao de dados na T_MDM_CIDADAO
-- Origem   : T_SRC_PREFEITURA_CIDADAO(principal) + T_SRC_RECEITA_FEDERAL
-- Destino  : T_MDM_CIDADAO
-- ============================================================
SET SERVEROUTPUT ON SIZE 1000000;

DECLARE
    -- -- Cursor principal — leitura apenas de algumas colunas da tabela de cidadão da Prefeitura ------
    CURSOR c_seleciona_cidadao_prefeitura IS
        SELECT 	p.cpf_prefeitura,
				p.nome_cidadao,
				p.dt_nasc_pref,
				p.sexo_pref,
				p.email_pref,
				p.telefone_pref
		 FROM   t_src_prefeitura_cidadao p;

    -- -- Variavel do tipo RECORD que referencia a tabela T_MDM_CIDADAO ---------------
   v_rec_mdm_cidadao       T_MDM_CIDADAO%ROWTYPE;
   v_rec_mdm_cidadao_vazio T_MDM_CIDADAO%ROWTYPE;

    -- -- Variavel para busca na Receita Federal ---------------
   v_rec_receita       T_SRC_RECEITA_FEDERAL%ROWTYPE;

	-- Variável que converte a data de nascimento da prefeitura para o tipo de dado number
    v_dt_nasc_pref 		DATE := NULL;
	
    -- -- Contadores de auditoria ------------------------------
    v_total_lidos       NUMBER := 0;

    v_total_inseridos   NUMBER := 0;
    v_total_atualizados NUMBER := 0;
    v_total_erros       NUMBER := 0;

BEGIN
/*
    DBMS_OUTPUT.PUT_LINE('============================================');
    DBMS_OUTPUT.PUT_LINE('INICIO DA CARGA para a a tabela T_MDM_CIDADAO');
    DBMS_OUTPUT.PUT_LINE('Data/Hora: ' || TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS'));
    DBMS_OUTPUT.PUT_LINE('============================================');
*/
    -- -- Loop principal — um registro da Prefeitura por vez ---
    FOR r_cidadao_prefeitura IN  c_seleciona_cidadao_prefeitura LOOP

		-- Limpa todas as variáveis record para cada linha existente no cursor r_cidadao_prefeitura
		v_rec_mdm_cidadao := v_rec_mdm_cidadao_vazio;
		
		-- Sempre que iniciar a flag divergencia é NAO
		v_rec_mdm_cidadao.fl_divergencia := 'NAO'; 
		
        v_total_lidos := v_total_lidos + 1;

        -- ----------------------------------------------------
        -- REGRA 1 — NR_CPF_CIDADAO
        -- Origem: CPF_PREFEITURA formato 000.000.000/00
        -- Remover pontos e barra com REPLACE aninhado
        -- Converter para NUMBER
        ----------------------------------------------------
		v_rec_mdm_cidadao.nr_cpf_cidadao := TO_NUMBER( REPLACE(
                            REPLACE(r_cidadao_prefeitura.CPF_PREFEITURA, '.', ''),
                            '-', '') );
		v_rec_mdm_cidadao.nr_cpf_cidadao_mascara := r_cidadao_prefeitura.CPF_PREFEITURA;
		
		--DBMS_OUTPUT.PUT_LINE( 'CPF CONVERTIDO: ' || v_rec_mdm_cidadao.nr_cpf_cidadao || ' CPF antigo: ' || r_cidadao_prefeitura.CPF_PREFEITURA );
		
        -- ----------------------------------------------------
        -- SELECIONA OS DADOS EXISTENTES NA TABELA DA RECEITA FEDERAL T_SRC_RECEITA FEDERAL
        -- O formato do CPF da Receita Federal é o mesmo da Prefeitura, conteúdo composto por numeros e caracteres.
        -- Formato Receita e Prefeitura: 000.000.000-00
        -- ----------------------------------------------------
        BEGIN
            SELECT *
            INTO v_rec_receita
            FROM t_src_receita_federal
            WHERE cpf_receita = r_cidadao_prefeitura.CPF_PREFEITURA
            AND ROWNUM = 1;
			
			-- O cidadão está cadastrado na Receita Federal
			v_rec_mdm_cidadao.nm_cidadao := UPPER(TRIM(v_rec_receita.nome_completo));
			
			IF r_cidadao_prefeitura.nome_cidadao IS NULL THEN
			   v_rec_mdm_cidadao.fl_divergencia := 'SIM';
               v_rec_mdm_cidadao.ds_divergencia := v_rec_mdm_cidadao.ds_divergencia ||
               'Nome do cidadao divergente entre a Receita Federal e a Prefeitura. ';
			ELSIF r_cidadao_prefeitura.nome_cidadao <> v_rec_mdm_cidadao.nm_cidadao THEN
               v_rec_mdm_cidadao.fl_divergencia := 'SIM';
               v_rec_mdm_cidadao.ds_divergencia := v_rec_mdm_cidadao.ds_divergencia ||
               'Nome do cidadao divergente entre a Receita Federal e a Prefeitura. ';
			END IF;

			-- ============================================================
			-- REGRA 3: Data de Nascmento 
			-- Receita Federal : Formato caractere DD/MM/YYYY   v_rec_receita.DT_NASCIMENTO
			-- Prefeitura      : Formato  caractere MM/DD/YYYY   r_cidadao_prefeitura.DT_NASC_PREF
			-- Destino         : v_rec_mdm_cidadao.DT_NASCIMENTO
			-- ============================================================
			-- -- Verificar se ambas as datas estão nulas ---------------
			IF TRIM(v_rec_receita.DT_NASCIMENTO) IS NULL OR TRIM(r_cidadao_prefeitura.DT_NASC_PREF) IS NULL THEN
				v_rec_mdm_cidadao.fl_divergencia := 'SIM';
				IF	TRIM(v_rec_receita.DT_NASCIMENTO) IS NULL THEN
					-- A data mais importante é a Receita, então verificamos se ela está  nula
					v_rec_mdm_cidadao.ds_divergencia := v_rec_mdm_cidadao.ds_divergencia ||
					' A data de nascimento nao foi localizada na base de dados da Receita Federal. ';
				ELSIF TRIM(r_cidadao_prefeitura.DT_NASC_PREF) IS NULL THEN
					-- Aqui verificamos se a data da Prefeitura está nula
						v_rec_mdm_cidadao.fl_divergencia := 'SIM';
						v_rec_mdm_cidadao.ds_divergencia := v_rec_mdm_cidadao.ds_divergencia ||
						'A data de nascimento nao foi localizada na base de dados da Prefeitura. ';
				END IF;
			ELSE
				-- Converter data da Receita Federal para data e no fomato (DD/MM/YYYY)
				BEGIN
					v_rec_mdm_cidadao.dt_nascimento := TO_DATE(TRIM(v_rec_receita.DT_NASCIMENTO),'DD/MM/YYYY');
					v_dt_nasc_pref := TO_DATE(TRIM(r_cidadao_prefeitura.DT_NASC_PREF),'MM/DD/YYYY');
					IF v_dt_nasc_pref <> v_rec_mdm_cidadao.dt_nascimento then
						v_rec_mdm_cidadao.fl_divergencia := 'SIM';
						v_rec_mdm_cidadao.ds_divergencia := v_rec_mdm_cidadao.ds_divergencia ||
						'A data de nascimento da Prefeitura está diferente da Receita Federal. ';
					END IF;
				EXCEPTION
					WHEN OTHERS THEN
						v_rec_mdm_cidadao.dt_nascimento  := NULL;
						v_rec_mdm_cidadao.fl_divergencia := 'SIM';
						v_rec_mdm_cidadao.ds_divergencia := v_rec_mdm_cidadao.ds_divergencia ||
						'Erro na conversao da data de nascimento da Receita Federal ou da Prefeitura. Favor verificar ';
				END;
			END IF;
	
		END;
        -- ----------------------------------------------------
        -- REGRA  NM_ESTADO_CIVIL
        -- Origem dos dados Receita Federal: S / C / D / V / U. Converter para descricao completa
        -- ----------------------------------------------------
        CASE UPPER(TRIM(v_rec_receita.ESTADO_CIVIL))
              WHEN 'S' THEN v_rec_mdm_cidadao.nm_estado_civil := 'SOLTEIRO';
              WHEN 'C' THEN v_rec_mdm_cidadao.nm_estado_civil := 'CASADO';
              WHEN 'D' THEN v_rec_mdm_cidadao.nm_estado_civil := 'DIVORCIADO';
              WHEN 'V' THEN v_rec_mdm_cidadao.nm_estado_civil := 'VIUVO';
              WHEN 'U' THEN v_rec_mdm_cidadao.nm_estado_civil := 'UNIAO_ESTAVEL';
		ELSE
           v_rec_mdm_cidadao.nm_estado_civil := 'NAO_INFORMADO';
           v_rec_mdm_cidadao.fl_divergencia  := 'SIM';
           v_rec_mdm_cidadao.ds_divergencia  := v_rec_mdm_cidadao.ds_divergencia ||
           'Dominio de estado civil nao reconhecido, sendo gravado como NAO_INFORMADO. ';
        END CASE;
		
		  -- ----------------------------------------------------
        -- REGRA  Data da Carga: Assumir SYSDATE, ou seja, dd/mm/yyyyy hh24:mi:ss
        -- ----------------------------------------------------
		v_rec_mdm_cidadao.dt_carga := SYSTIMESTAMP;

		-- Cria o conteúdo para a chave primária do dado mestre do cidadão.
		v_rec_mdm_cidadao.id_gold_cidadao := SQ_MDM_CIDADAO.NEXTVAL;
		-- ----------------------------------------------------
        -- GRAVACAO NA T_MDM_CIDADAO
        -- INSERT com tratamento DUP_VAL_ON_INDEX ? UPDATE
        -- ----------------------------------------------------
        BEGIN
            INSERT INTO T_MDM_CIDADAO (
                ID_GOLD_CIDADAO,
                NR_CPF_CIDADAO,
				NR_CPF_CIDADAO_MASCARA,
                NM_CIDADAO,
                DT_NASCIMENTO,
                NM_ESTADO_CIVIL,
                DT_CARGA,
                FL_DIVERGENCIA,
                DS_DIVERGENCIA
            ) VALUES (
                v_rec_mdm_cidadao.id_gold_cidadao,
                v_rec_mdm_cidadao.nr_cpf_cidadao,
				v_rec_mdm_cidadao.nr_cpf_cidadao_mascara,
                v_rec_mdm_cidadao.nm_cidadao,
                v_rec_mdm_cidadao.dt_nascimento,
                v_rec_mdm_cidadao.nm_estado_civil,
                v_rec_mdm_cidadao.dt_carga,
                v_rec_mdm_cidadao.fl_divergencia,
                v_rec_mdm_cidadao.ds_divergencia
            );

            v_total_inseridos := v_total_inseridos + 1;

        EXCEPTION
            -- -- Cidadao ja cadastrado pelo CPF, sendo assim fazer UPDATE ---
            WHEN DUP_VAL_ON_INDEX THEN
                BEGIN
                    UPDATE T_MDM_CIDADAO SET
                        NM_CIDADAO      = v_rec_mdm_cidadao.nm_cidadao,
                        DT_NASCIMENTO   = v_rec_mdm_cidadao.dt_nascimento,
                        NM_ESTADO_CIVIL = v_rec_mdm_cidadao.nm_estado_civil,
                        DT_CARGA        = v_rec_mdm_cidadao.dt_carga,
                        FL_DIVERGENCIA  = v_rec_mdm_cidadao.fl_divergencia,
                        DS_DIVERGENCIA  = v_rec_mdm_cidadao.ds_divergencia
                    WHERE NR_CPF_CIDADAO = v_rec_mdm_cidadao.nr_cpf_cidadao;

                    v_total_atualizados := v_total_atualizados + 1;

                    DBMS_OUTPUT.PUT_LINE(
                        'UPDATE CPF: ' || v_rec_mdm_cidadao.nr_cpf_cidadao ||
                        ' | Cidadao: '   || v_rec_mdm_cidadao.nm_cidadao
                    );
                EXCEPTION
                    WHEN OTHERS THEN
                        v_total_erros := v_total_erros + 1;
                        DBMS_OUTPUT.PUT_LINE(
                            'ERRO no UPDATE pela chave CPF: ' || v_rec_mdm_cidadao.nr_cpf_cidadao ||
                            ' | Erro: '  || SQLERRM
                        );
                END;

            -- -- Outros erros no INSERT --------------------
            WHEN OTHERS THEN
                v_total_erros := v_total_erros + 1;
                DBMS_OUTPUT.PUT_LINE(
                    'ERRO no INSERT Linha: ' || v_rec_mdm_cidadao.id_gold_cidadao ||
                    ' | CPF: '  || v_rec_mdm_cidadao.nr_cpf_cidadao ||
                    ' | Erro: ' || SQLERRM
                );
				raise_application_error (-20010, 'Erro critico ' || SQLErrM);

        END; -- fim INSERT/UPDATE

/*
		DBMS_OUTPUT.PUT_LINE( v_rec_mdm_cidadao.id_gold_cidadao || chr(10) || v_rec_mdm_cidadao.nr_cpf_cidadao || chr(10) || 
		v_rec_mdm_cidadao.nr_cpf_cidadao_mascara
		|| chr(10) || v_rec_mdm_cidadao.nm_cidadao || chr(10) || v_rec_mdm_cidadao.fl_divergencia || chr(10) || v_rec_mdm_cidadao.ds_divergencia
		|| chr(10) || v_rec_mdm_cidadao.dt_nascimento || chr(10) || v_rec_mdm_cidadao.nm_estado_civil || chr(10) || v_rec_mdm_cidadao.dt_carga);
*/

		END LOOP; -- fim cursor

    COMMIT;

    -- -- Relatorio final --------------------------------------
    DBMS_OUTPUT.PUT_LINE(' ');
    DBMS_OUTPUT.PUT_LINE('============================================');
    DBMS_OUTPUT.PUT_LINE('RESULTADO DO PROCESSAMENTO: CARGA NA TABELA T_MDM_CIDADAO');
    DBMS_OUTPUT.PUT_LINE('============================================');
    DBMS_OUTPUT.PUT_LINE('Registros lidos              : ' || v_total_lidos);
    DBMS_OUTPUT.PUT_LINE('Inseridos com sucesso        : ' || v_total_inseridos);
    DBMS_OUTPUT.PUT_LINE('Atualizados (UPDATE)         : ' || v_total_atualizados);
    DBMS_OUTPUT.PUT_LINE('Erros                        : ' || v_total_erros);
    DBMS_OUTPUT.PUT_LINE('Data/Hora termino            : ' ||
                          TO_CHAR(SYSDATE,'DD/MM/YYYY HH24:MI:SS'));
    DBMS_OUTPUT.PUT_LINE('============================================');

EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        DBMS_OUTPUT.PUT_LINE('ERRO CRITICO COM CARGA INTERROMPIDA: ' || SQLERRM);
END;
/