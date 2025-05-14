from db.conexao import conectar_banco, fechar_banco, criar_banco_se_nao_existir
from db.criadorTabelas import criar_tabelas
import re

NOME_BANCO_EMPRESAS = 'db_apuradorICMS'

def nomear_banco_por_razao_social(razao_social):
    nome_banco = re.sub(r'[^a-zA-Z0-9]', '_', razao_social.lower())
    nome_banco = f"empresa_{nome_banco[:30]}"
    return nome_banco

def cadastrar_empresa(cnpj, razao_social):
    conexao = conectar_banco(NOME_BANCO_EMPRESAS)
    if not conexao:
        criar_banco_principal()
        conexao = conectar_banco(NOME_BANCO_EMPRESAS)
        
    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cnpj VARCHAR(14) UNIQUE,
                    razao_social VARCHAR(100)
                )
            """)
            
            cursor.execute("""
                INSERT INTO empresas (cnpj, razao_social) VALUES (%s, %s)
            """, (cnpj, razao_social))
        conexao.commit()
    except Exception as e:
        print(f"Erro ao cadastrar empresa: {e}")
        return False
    finally:
        fechar_banco(conexao)

    nome_banco = nomear_banco_por_razao_social(razao_social)
    criar_banco_se_nao_existir(nome_banco)

    conexao_empresa = conectar_banco(nome_banco)
    if not conexao_empresa:
        return False
        
    try:
        cursor_empresa = conexao_empresa.cursor()
        criar_tabelas(cursor_empresa)
        conexao_empresa.commit()
        return True
    except Exception as e:
        print(f"Erro ao criar tabelas para empresa {razao_social}: {e}")
        return False
    finally:
        fechar_banco(conexao_empresa)

def criar_banco_principal():
    criar_banco_se_nao_existir(NOME_BANCO_EMPRESAS)
    conexao = conectar_banco(NOME_BANCO_EMPRESAS)
    try:
        with conexao.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    cnpj VARCHAR(14) UNIQUE,
                    razao_social VARCHAR(100)
                )
            """)
        conexao.commit()
    finally:
        fechar_banco(conexao)