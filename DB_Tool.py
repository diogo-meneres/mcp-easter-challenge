import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

_conexao_persistente = None

def _create_new_connection():
    """Função base que apenas cria a ligação."""
    return pymysql.connect(
        host='127.0.0.1', 
        port=3306, 
        user='root', 
        password='root',
        database='planner', 
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5
    )

def get_db_connection():
    """O Gestor Inteligente de Conexões."""
    global _conexao_persistente
    modo = os.getenv("DB_CONNECTION_MODE", "per_request")

    if modo == "persistent":
        # Se a conexão não existe ou caiu, criamos uma nova
        if _conexao_persistente is None or not _conexao_persistente.open:
            print("🔄 A criar nova Conexão Persistente...")
            _conexao_persistente = _create_new_connection()
        else:
            # ping() verifica se o MySQL desligou
            # Se sim, o reconnect=True liga novamente
            _conexao_persistente.ping(reconnect=True)
            
        return _conexao_persistente
    else:
        # Modo clássico (Abre e fecha)
        return _create_new_connection()

def release_db_connection(connection):
    """Fecha a conexão se não estivermos no modo persistente."""
    modo = os.getenv("DB_CONNECTION_MODE", "per_request")
    if modo != "persistent":
        connection.close()

def check_mysql_connection():
    """Verifica se o MySQL está vivo."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        connection.close()
        return "✅ Conexão estabelecida! O MySQL está online e a base de dados 'planner' está acessível."
    except Exception as e:
        return f"❌ Falha na ligação ao MySQL: {str(e)}"
    
def fetch_all_plans():
    """Procura todos os planos disponíveis na base de dados."""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Removi a 'description' da query
            cursor.execute("SELECT id, name FROM plans")
            plans = cursor.fetchall()
            
            if not plans:
                return "Nenhum plano encontrado na base de dados."
            
            # Ajustei o texto para mostrar apenas o ID e o Nome
            linhas = [f"ID: {p['id']} | Nome: {p['name']}" for p in plans]
            return "Planos Disponíveis:\n" + "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao ler planos: {str(e)}"
    finally:
        if 'connection' in locals() and connection is not None:
            release_db_connection(connection)