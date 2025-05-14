from db.conexao import conectar_banco, fechar_banco
from utils.siglas import obter_sigla_estado
from utils.process_data import process_data
from utils.cfop import cfop_eh_entrada_varejo
from utils.cnpj import processar_cnpjs
from utils.aliquota import formatar_aliquota
from datetime import datetime

def verificar_e_ajustar_tabela(nome_banco):
    """Verifica e ajusta a estrutura da tabela 0000 se necessário."""
    conexao = conectar_banco(nome_banco)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE '0000'")
            if cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE `0000` 
                    MODIFY COLUMN dt_ini VARCHAR(10),
                    MODIFY COLUMN dt_fin VARCHAR(10),
                    MODIFY COLUMN uf VARCHAR(2);
                """)
                print("✓ Estrutura da tabela 0000 ajustada com sucesso.")
                conexao.commit()
                
                cursor.execute("SHOW TABLES LIKE '0150'")
                if cursor.fetchone():
                    cursor.execute("""
                        ALTER TABLE `0150` 
                        MODIFY COLUMN uf VARCHAR(2);
                    """)
                    print("✓ Estrutura da tabela 0150 ajustada com sucesso.")
                    conexao.commit()
    except Exception as e:
        print(f"[AVISO] Erro ao ajustar tabelas: {e}")
    finally:
        fechar_banco(conexao)

def processar_sped(conteudo, nome_banco):
    print(f"Processando SPED para o banco: {nome_banco}")
    print(f"Tamanho do conteúdo: {len(conteudo)}")
    
    verificar_e_ajustar_tabela(nome_banco)

    conteudo = process_data(conteudo)
    conexao = conectar_banco(nome_banco)
    if not conexao:
        raise Exception(f"[ERRO] Não foi possível conectar ao banco '{nome_banco}'")

    cursor = conexao.cursor()
    linhas = conteudo.split('\n')
    print(f"Total de linhas: {len(linhas)}")

    id_c100_atual = None
    dt_ini_0000 = None
    periodo = None
    filial = None
    ind_oper = None
    cod_part = None
    num_doc = None
    chv_nfe = None

    try:
        linha_atual = 0
        for linha in linhas:
            linha_atual += 1
            if linha_atual % 1000 == 0:
                print(f"Processando linha {linha_atual} de {len(linhas)}")

            if not linha.startswith('|'): 
                continue
                
            blocos = linha.strip().split('|')
            if len(blocos) < 2: 
                continue

            registro = blocos[1]
            print(f"Processando registro: {registro} (linha {linha_atual})")

            if registro == "0000":
                try:
                    dados = blocos[2:-1]
                    print(f"Dados registro 0000: {dados}")

                    if len(dados) > 3 and dados[3]:
                        dados[3] = dados[3][:8]
                    if len(dados) > 4 and dados[4]:
                        dados[4] = dados[4][:8]

                    dt_ini_0000 = dados[3] if len(dados) > 3 else None
                    cnpj = dados[6] if len(dados) > 6 else ""
                    filial = cnpj[8:12] if cnpj and len(cnpj) >= 12 else "0000"
                    periodo = f"{dt_ini_0000[2:4]}/{dt_ini_0000[4:]}" if dt_ini_0000 else None

                    params = dados + [filial, periodo]

                    if len(params) >= 15 and params[14] and len(params[14]) > 1:
                        print(f"[ALERTA] ind_ativ com valor grande: {params[14]} — truncando para 1 caractere.")
                        params[14] = params[14][:1]

                    # Garantir que o campo UF tenha no máximo 2 caracteres
                    if len(params) >= 9 and params[8] and len(params[8]) > 2:
                        print(f"[ALERTA] UF (0000) com valor grande: {params[8]} — truncando para dois caracteres.")
                        params[8] = params[8][:2]

                    placeholders_count = 17
                    while len(params) < placeholders_count:
                        params.append(None)
                    if len(params) > placeholders_count:
                        params = params[:placeholders_count]

                    cursor.execute("""
                        INSERT INTO `0000` (
                            reg, cod_ver, cod_fin, dt_ini, dt_fin, nome, cnpj, cpf, uf, ie,
                            cod_num, im, suframa, ind_perfil, ind_ativ, filial, periodo
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, params)
                    print("✓ Registro 0000 inserido com sucesso")
                except Exception as e:
                    print(f"[ERRO] Falha ao processar registro 0000: {e}")
                    import traceback
                    print(traceback.format_exc())
                    raise

            elif registro == "0150":
                try:
                    dados = blocos[2:-1]
                    while len(dados) < 13:
                        dados.append(None)

                    cod_uf = dados[7][:2] if dados[7] else None
                    uf = obter_sigla_estado(cod_uf)

                    print(f"[DEBUG] cod_uf extraído: {cod_uf}")
                    print(f"[DEBUG] Sigla UF obtida: {uf}")

                    cnpj = dados[4]
                    pj_pf = "PF" if not cnpj or cnpj.strip() == "" else "PJ"

                    params = dados + [cod_uf, uf, pj_pf, periodo]

                    # Garantir que o campo UF (0150) tenha no máximo 2 caracteres
                    if len(params) >= 15 and params[14] and len(params[14]) > 2:
                        print(f"[ALERTA] UF (0150) com valor grande: {params[14]} — truncando para dois caracteres.")
                        params[14] = params[14][:2]

                    placeholders_count = 17
                    while len(params) < placeholders_count:
                        params.append(None)
                    if len(params) > placeholders_count:
                        params = params[:placeholders_count]

                    cursor.execute("""
                        INSERT IGNORE INTO `0150` (
                            reg, cod_part, nome, cod_pais, cnpj, cpf, ie, cod_mun, suframa,
                            ende, num, compl, bairro, cod_uf, uf, pj_pf, periodo
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, params)
                except Exception as e:
                    print(f"[ERRO] Falha ao processar registro 0150: {e}")
                    import traceback
                    print(traceback.format_exc())
                    raise

            elif registro == "0200":
                try:
                    dados = blocos[2:-1]
                    while len(dados) < 13:
                        dados.append(None)
                        
                    params = dados + [periodo]
                    print(f"Parâmetros SQL 0200 (primeiros 5): {params[:5]}...")
                    
                    placeholders_count = """
                        INSERT IGNORE INTO `0200` (
                            reg, cod_item, descr_item, cod_barra, cod_ant_item, unid_inv,
                            tipo_item, cod_ncm, ex_ipi, cod_gen, cod_list, aliq_icms,
                            cest, periodo
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """.count('%s')
                    
                    while len(params) < placeholders_count:
                        params.append(None)
                    
                    if len(params) > placeholders_count:
                        params = params[:placeholders_count]
                    
                    cursor.execute("""
                        INSERT IGNORE INTO `0200` (
                            reg, cod_item, descr_item, cod_barra, cod_ant_item, unid_inv,
                            tipo_item, cod_ncm, ex_ipi, cod_gen, cod_list, aliq_icms,
                            cest, periodo
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, params)
                except Exception as e:
                    print(f"[ERRO] Falha ao processar registro 0200: {e}")
                    import traceback
                    print(traceback.format_exc())
                    raise

            elif registro == "C100":
                try:
                    dados = blocos[2:-1]
                    dados = [d if d not in [None, ''] else "0" for d in dados]
                    while len(dados) < 29:
                        dados.append(None)
                        
                    ind_oper = dados[0]
                    cod_part = dados[2]
                    num_doc = dados[7]
                    chv_nfe = dados[9]
                    
                    params = [periodo] + dados + [filial]
                    print(f"Parâmetros SQL C100 (primeiros 5): {params[:5]}...")
                    
                    print(f"ind_oper: {ind_oper}, tipo: {type(ind_oper)}")
                    print(f"cod_part: {cod_part}, tipo: {type(cod_part)}")
                    print(f"num_doc: {num_doc}, tipo: {type(num_doc)}")
                    print(f"chv_nfe: {chv_nfe}, tipo: {type(chv_nfe)}")
                    
                    placeholders_count = """
                        INSERT INTO c100 (
                            periodo, reg, ind_oper, ind_emit, cod_part, cod_mod, cod_sit, ser,
                            num_doc, chv_nfe, dt_doc, dt_e_s, vl_doc, ind_pgto, vl_desc, vl_abat_nt,
                            vl_merc, ind_frt, vl_frt, vl_seg, vl_out_da, vl_bc_icms, vl_icms,
                            vl_bc_icms_st, vl_icms_st, vl_ipi, vl_pis, vl_cofins, vl_pis_st,
                            vl_cofins_st, filial
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """.count('%s')
                    
                    while len(params) < placeholders_count:
                        params.append(None)
                    
                    if len(params) > placeholders_count:
                        params = params[:placeholders_count]
                    
                    cursor.execute("""
                        INSERT INTO c100 (
                            periodo, reg, ind_oper, ind_emit, cod_part, cod_mod, cod_sit, ser,
                            num_doc, chv_nfe, dt_doc, dt_e_s, vl_doc, ind_pgto, vl_desc, vl_abat_nt,
                            vl_merc, ind_frt, vl_frt, vl_seg, vl_out_da, vl_bc_icms, vl_icms,
                            vl_bc_icms_st, vl_icms_st, vl_ipi, vl_pis, vl_cofins, vl_pis_st,
                            vl_cofins_st, filial
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, params)
                    
                    id_c100_atual = cursor.lastrowid
                    print(f"✓ Registro C100 inserido com sucesso, ID: {id_c100_atual}")
                except Exception as e:
                    print(f"[ERRO] Falha ao processar registro C100: {e}")
                    import traceback
                    print(traceback.format_exc())
                    raise

            elif registro == "C170" and id_c100_atual:
                try:
                    dados = blocos[2:-1]
                    dados = [d if d not in [None, ''] else "0" for d in dados]
                    while len(dados) < 38:
                        dados.append(None)
                    
                    if None in [periodo, id_c100_atual, filial, ind_oper, cod_part, num_doc, chv_nfe]:
                        print(f"[ALERTA] Valores nulos em C170: periodo={periodo}, id_c100={id_c100_atual}, filial={filial}")
                        print(f"ind_oper={ind_oper}, cod_part={cod_part}, num_doc={num_doc}, chv_nfe={chv_nfe}")
                    
                    params = [periodo] + dados + [id_c100_atual, filial, ind_oper, cod_part, num_doc, chv_nfe]
                    print(f"Total de parâmetros C170: {len(params)}")
                    print(f"Parâmetros SQL C170 (primeiros 5): {params[:5]}...")
                    
                    # Contar placeholders
                    placeholders_count = """
                        INSERT INTO c170 (
                            periodo, reg, num_item, cod_item, descr_compl, qtd, unid,
                            vl_item, vl_desc, ind_mov, cst_icms, cfop, cod_nat, vl_bc_icms,
                            aliq_icms, vl_icms, vl_bc_icms_st, aliq_st, vl_icms_st, ind_apur,
                            cst_ipi, cod_enq, vl_bc_ipi, aliq_ipi, vl_ipi, cst_pis, vl_bc_pis,
                            aliq_pis, quant_bc_pis, aliq_pis_reais, vl_pis, cst_cofins,
                            vl_bc_cofins, aliq_cofins, quant_bc_cofins, aliq_cofins_reais,
                            vl_cofins, cod_cta, vl_abat_nt, id_c100, filial, ind_oper,
                            cod_part, num_doc, chv_nfe
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """.count('%s')
                    
                    while len(params) < placeholders_count:
                        params.append(None)
                    
                    if len(params) > placeholders_count:
                        params = params[:placeholders_count]
                    
                    cursor.execute("""
                        INSERT INTO c170 (
                            periodo, reg, num_item, cod_item, descr_compl, qtd, unid,
                            vl_item, vl_desc, ind_mov, cst_icms, cfop, cod_nat, vl_bc_icms,
                            aliq_icms, vl_icms, vl_bc_icms_st, aliq_st, vl_icms_st, ind_apur,
                            cst_ipi, cod_enq, vl_bc_ipi, aliq_ipi, vl_ipi, cst_pis, vl_bc_pis,
                            aliq_pis, quant_bc_pis, aliq_pis_reais, vl_pis, cst_cofins,
                            vl_bc_cofins, aliq_cofins, quant_bc_cofins, aliq_cofins_reais,
                            vl_cofins, cod_cta, vl_abat_nt, id_c100, filial, ind_oper,
                            cod_part, num_doc, chv_nfe
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, params)
                except Exception as e:
                    print(f"[ERRO] Falha ao processar registro C170: {e}")
                    print(f"Length blocos: {len(blocos)}, blocos: {blocos}")
                    import traceback
                    print(traceback.format_exc())
                    raise

        conexao.commit()
        print("✓ Processamento SPED finalizado com sucesso!")

    except Exception as e:
        print(f"[ERRO] Falha ao processar SPED: {e}")
        conexao.rollback()
        import traceback
        print(traceback.format_exc())
        raise

    finally:
        cursor.close()
        fechar_banco(conexao)

def atualizar_ncm(nome_banco):
    conexao = conectar_banco(nome_banco)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                UPDATE c170 c
                JOIN `0200` p ON c.cod_item = p.cod_item
                SET c.ncm = p.cod_ncm
                WHERE c.ncm IS NULL OR c.ncm = ''
            """)
            conexao.commit()
    finally:
        fechar_banco(conexao)

def clonar_c170(nome_banco):
    from utils.cfop import CFOPS_RELEVANTES

    conexao = conectar_banco(nome_banco)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("DELETE FROM c170_clone")
            
            placeholders = ', '.join(['%s' for _ in range(len(CFOPS_RELEVANTES))])
            
            query = """
                INSERT IGNORE INTO c170_clone (
                    id_c170, periodo, reg, num_item, cod_item, descr_compl, qtd, unid,
                    vl_item, vl_desc, cfop, cst, ncm, id_c100, filial, ind_oper,
                    cod_part, num_doc, chv_nfe, aliquota, resultado, chavefinal
                )
                SELECT
                    c.id, c.periodo, c.reg, c.num_item, c.cod_item, c.descr_compl, c.qtd,
                    c.unid, c.vl_item, c.vl_desc, c.cfop, c.cst_icms, c.ncm, c.id_c100,
                    c.filial, c.ind_oper, c.cod_part, c.num_doc, c.chv_nfe, '', '', 
                    CONCAT(c.cod_item, c.chv_nfe)
                FROM c170 c
                JOIN cadastro_fornecedores f ON f.cod_part = c.cod_part
                WHERE f.uf = 'CE'
                  AND f.decreto = 'Não'
                  AND c.cfop IN (""" + placeholders + ")"
            
            print(f"SQL Query: {query}")
            print(f"Params: {tuple(CFOPS_RELEVANTES)}")
            
            cursor.execute(query, tuple(CFOPS_RELEVANTES))
            conexao.commit()
    finally:
        fechar_banco(conexao)

def atualizar_aliquota(nome_banco):
    conexao = conectar_banco(nome_banco)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                UPDATE c170_clone c
                JOIN cadastro_tributacao t ON c.cod_item = t.codigo
                SET c.aliquota = t.aliquota
                WHERE c.aliquota IS NULL OR c.aliquota = ''
            """)
            conexao.commit()
    finally:
        fechar_banco(conexao)

def atualizar_aliquota_simples(nome_banco):
    conexao = conectar_banco(nome_banco)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                UPDATE c170_clone c
                JOIN cadastro_fornecedores f ON c.cod_part = f.cod_part
                SET c.aliquota = CONCAT(FORMAT(REPLACE(c.aliquota, '%', '') + %s, 2), '%%')
                WHERE f.simples = 'Sim'
                AND c.aliquota REGEXP '^[0-9]+(\\.[0-9]*)?%?$'
            """, (3,))
            conexao.commit()
    finally:
        fechar_banco(conexao)

def atualizar_resultado(nome_banco):
    conexao = conectar_banco(nome_banco)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                UPDATE c170_clone
                SET resultado = CASE
                    WHEN aliquota REGEXP '^[A-Za-z]' THEN 0
                    WHEN aliquota IS NULL OR aliquota = '' THEN 0
                    ELSE CAST(REPLACE(vl_item, ',', '.') AS DECIMAL(10,2)) *
                         (CAST(REPLACE(aliquota, '%', '') AS DECIMAL(10,2)) / 100)
                END
            """)
            conexao.commit()
    finally:
        fechar_banco(conexao)
