import pymysql

def get_db_connection():
    return pymysql.connect(
        host='127.0.0.1', 
        port=3306, 
        user='root', 
        password='root',
        database='planner', 
        cursorclass=pymysql.cursors.DictCursor, # Devolve dicionários em vez de listas simples
        connect_timeout=5
    )

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
            cursor.execute("SELECT id, name, description FROM plans")
            plans = cursor.fetchall()
            
            if not plans:
                return "Nenhum plano encontrado na base de dados."
            
            linhas = [f"ID: {p['id']} | Nome: {p['name']} | Desc: {p['description']}" for p in plans]
            return "Planos Disponíveis:\n" + "\n".join(linhas)
    except Exception as e:
        return f"❌ Erro ao ler planos: {str(e)}"
    finally:
        # Nota: Se a conexão falhar no início, o 'connection' não existe. 
        # Mas o try/except acima trata disso.
        pass