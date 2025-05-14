from db.conexao import conectar_banco, fechar_banco
from utils.siglas import obter_sigla_estado
from utils.process_data import process_data
from utils.cfop import cfop_eh_entrada_varejo
from utils.cnpj import processar_cnpjs
from utils.aliquota import formatar_aliquota
from datetime import datetime

def processar_sped(conteudo, nome_banco):
    conteudo = process_data(conteudo)
    conexao = conectar_banco(nome_banco)
    if not conexao:
        raise Exception(f"[ERRO] Não foi possível conectar ao banco '{nome_banco}'")

    cursor = conexao.cursor()
    linhas = conteudo.split('\n')

    id_c100_atual = None
    dt_ini_0000 = None
    periodo = None
    filial = None

    try:
        for linha in linhas:
            if not linha.startswith('|'): continue
            blocos = linha.strip().split('|')
            if len(blocos) < 2: continue

            registro = blocos[1]

            if registro == "0000":
                dados = blocos[2:-1]
                dt_ini_0000 = dados[3]
                cnpj = dados[6]
                filial = cnpj[8:12] if len(cnpj) >= 12 else "0000"
                periodo = f"{dt_ini_0000[2:4]}/{dt_ini_0000[4:]}"
                dados.append(filial)
                cursor.execute("""
                    INSERT INTO `0000` (
                        reg, cod_ver, cod_fin, dt_ini, dt_fin, nome, cnpj, cpf, uf, ie,
                        cod_num, im, suframa, ind_perfil, ind_ativ, filial, periodo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados + [periodo])

            elif registro == "0150":
                dados = blocos[2:-1]
                while len(dados) < 13:
                    dados.append(None)
                cod_uf = dados[7][:2] if dados[7] else None
                uf = obter_sigla_estado(cod_uf)
                cnpj = dados[4]
                pj_pf = "PF" if cnpj is None or cnpj.strip() == "" else "PJ"
                dados += [cod_uf, uf, pj_pf, periodo]
                cursor.execute("""
                    INSERT IGNORE INTO `0150` (
                        reg, cod_part, nome, cod_pais, cnpj, cpf, ie, cod_mun, suframa,
                        ende, num, compl, bairro, cod_uf, uf, pj_pf, periodo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados)

            elif registro == "0200":
                dados = blocos[2:-1]
                while len(dados) < 13:
                    dados.append(None)
                dados.append(periodo)
                cursor.execute("""
                    INSERT IGNORE INTO `0200` (
                        reg, cod_item, descr_item, cod_barra, cod_ant_item, unid_inv,
                        tipo_item, cod_ncm, ex_ipi, cod_gen, cod_list, aliq_icms,
                        cest, periodo
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados)

            elif registro == "C100":
                dados = blocos[2:-1]
                while len(dados) < 29:
                    dados.append(None)
                dados_final = [periodo] + dados + [filial]
                cursor.execute("""
                    INSERT INTO c100 (
                        periodo, reg, ind_oper, ind_emit, cod_part, cod_mod, cod_sit, ser,
                        num_doc, chv_nfe, dt_doc, dt_e_s, vl_doc, ind_pgto, vl_desc, vl_abat_nt,
                        vl_merc, ind_frt, vl_frt, vl_seg, vl_out_da, vl_bc_icms, vl_icms,
                        vl_bc_icms_st, vl_icms_st, vl_ipi, vl_pis, vl_cofins, vl_pis_st,
                        vl_cofins_st, filial
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados_final)
                id_c100_atual = cursor.lastrowid
                ind_oper = dados[0]
                cod_part = dados[4]
                num_doc = dados[7]
                chv_nfe = dados[9]

            elif registro == "C170" and id_c100_atual:
                dados = blocos[2:-1]
                while len(dados) < 38:
                    dados.append(None)
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
                              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [periodo] + dados + [id_c100_atual, filial, ind_oper, cod_part, num_doc, chv_nfe])

        conexao.commit()

    except Exception as e:
        print(f"[ERRO] Falha ao processar SPED: {e}")
        conexao.rollback()
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

            cursor.execute(f"""
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
                  AND c.cfop IN ({','.join(['%s'] * len(CFOPS_RELEVANTES))})
            """, tuple(CFOPS_RELEVANTES))

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
                SET c.aliquota = CONCAT(FORMAT(REPLACE(c.aliquota, '%', '') + 3, 2), '%')
                WHERE f.simples = 'Sim'
                AND c.aliquota REGEXP '^[0-9]+(\\.[0-9]*)?%?$'
            """)
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
