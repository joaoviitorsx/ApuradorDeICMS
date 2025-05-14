import pymysql
from pymysql.cursors import DictCursor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('database')

def conectar_banco(nome_banco=None):
    try:
        conexao = pymysql.connect(
            host='localhost',
            user='root',
            password='1234',
            database=nome_banco if nome_banco else None,
            charset='utf8mb4',
            cursorclass=DictCursor,
            autocommit=True
        )
        return conexao
    except Exception as e:
        logger.error(f"Erro ao conectar com o banco '{nome_banco}': {e}")
        return None

def fechar_banco(conexao):
    if conexao and conexao.open:
        try:
            conexao.close()
        except Exception as e:
            logger.error(f"Erro ao fechar conexão: {e}")

def criar_banco_se_nao_existir(nome_banco):
    conexao = conectar_banco()
    if not conexao:
        logger.error("Não foi possível se conectar ao MySQL para criar o banco")
        return False
    
    try:
        with conexao.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{nome_banco}` DEFAULT CHARACTER SET 'utf8mb4'")
        conexao.commit()
        logger.info(f"Banco '{nome_banco}' verificado/criado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar banco '{nome_banco}': {e}")
        return False
    finally:
        fechar_banco(conexao)