import pymysql

from DB_Tool import get_db_connection, release_db_connection

def fetch_resource_load(plan_id: str):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Definir janela temporal (dias do plano)
            cursor.execute("SELECT DATEDIFF(baseline_end, baseline_start) + 1 AS dias FROM plans WHERE id = %s", (plan_id,))
            plan = cursor.fetchone()
            if not plan:
                return []
            dias = float(plan['dias'] or 1.0)

            # 2 e 3. Calcular horas alocadas e capacidade por recurso
            sql = """
                SELECT 
                    r.name as nome,
                    (r.capacity_hours_per_day * %s) as capacidade,
                    COALESCE(SUM(TIMESTAMPDIFF(MINUTE, a.start, a.end)) / 60.0, 0) AS horas_alocadas
                FROM resources r
                LEFT JOIN assignments a ON r.id = a.resource_id AND a.plan_id = %s
                GROUP BY r.id, r.name, r.capacity_hours_per_day
            """
            cursor.execute(sql, (dias, plan_id))
            resultados = cursor.fetchall()

            # 4. Formatar os valores e retornar a lista de dicionários
            for r in resultados:
                r['capacidade'] = float(r['capacidade'])
                r['horas_alocadas'] = float(r['horas_alocadas'])
            
            return resultados
    except Exception as e:
        # Apanha qualquer erro e devolve como texto para o LLM ler
        return f"❌ Erro ao analisar recursos: {str(e)}"    
    finally:
        conn.close()

def resource_tool(plan_id: str) -> str:
    """
    Analisa carga dos recursos:
    - >120%: OVERLOAD GRAVE
    - >100%: OVERLOAD
    - >=80%: OK
    - <80%: SUBUTILIZADO
    """
    resources = fetch_resource_load(plan_id)

    if not resources:
        return f"Plano: {plan_id}\n\nSem recursos alocados."

    output = []
    overload_count = 0

    for r in resources:
        capacidade = float(r["capacidade"] or 0)
        horas_alocadas = float(r["horas_alocadas"] or 0)

        if capacidade <= 0:
            carga = 0.0
            excesso = horas_alocadas
            estado = "SEM CAPACIDADE DEFINIDA"
        else:
            carga = (horas_alocadas / capacidade) * 100.0
            excesso = max(0.0, horas_alocadas - capacidade)

            if carga > 120:
                estado = "OVERLOAD GRAVE"
            elif carga > 100:
                estado = "OVERLOAD"
            elif carga >= 80:
                estado = "OK"
            else:
                estado = "SUBUTILIZADO"

        if "OVERLOAD" in estado:
            overload_count += 1

        output.append(
            f"{r['nome']}: {carga:.0f}% | excesso={excesso:.1f}h | {estado}"
        )

    return (
        f"Plano: {plan_id}\n\n"
        + "\n".join(output)
        + f"\n\nRecursos em overload: {overload_count}"
    )