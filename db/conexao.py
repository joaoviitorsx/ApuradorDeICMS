import pymysql
from pymysql.cursors import DictCursor
import logging
import os
from dotenv import load_dotenv
from dbutils.pooled_db import PooledDB
from pathlib import Path

dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger('database')

_connection_pools = {}

def get_connection_pool(nome_banco=None):
    global _connection_pools
    
    pool_key = nome_banco if nome_banco else 'default'
    
    if pool_key in _connection_pools:
        return _connection_pools[pool_key]
    
    try:
        pool = PooledDB(
            creator=pymysql,
            maxconnections=int(os.getenv('DB_MAX_CONNECTIONS', 10)),
            mincached=int(os.getenv('DB_MIN_CACHED', 2)),
            maxcached=int(os.getenv('DB_MAX_CACHED', 5)),
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=nome_banco,
            charset=os.getenv('DB_CHARSET', 'utf8mb4'),
            cursorclass=DictCursor,
            autocommit=True
        )
        _connection_pools[pool_key] = pool
        return pool
    except Exception as e:
        logger.error(f"Erro ao criar pool para banco '{nome_banco}': {e}")
        return None

def conectar_banco(nome_banco=None):
    try:
        pool = get_connection_pool(nome_banco)
        if pool:
            return pool.connection()
        return None
    except Exception as e:
        logger.error(f"Erro ao conectar com o banco '{nome_banco}': {e}")
        return None

def fechar_banco(conexao):
    if conexao:
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