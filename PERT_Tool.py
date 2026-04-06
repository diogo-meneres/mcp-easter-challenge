import math
from typing import List, Tuple

from langchain.tools import tool
from pydantic import BaseModel, Field


import pymysql

def get_db_connection():
    return pymysql.connect(
        host='127.0.0.1', port=3306, user='root', password='root',
        database='planner', cursorclass=pymysql.cursors.DictCursor
    )

def fetch_pert_data(plan_id: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT duration_h FROM tasks WHERE plan_id = %s", (plan_id,))
            tasks = cursor.fetchall()
            
            # Opção B: derivar (o)timista -20%, (m)edia, (p)essimista +50%
            pert_data = []
            for t in tasks:
                m = float(t['duration_h'])
                o = m * 0.8
                p = m * 1.5
                pert_data.append((o, m, p))
            
            return pert_data
    finally:
        conn.close()


class PERTInput(BaseModel):
    plan_id: str = Field(description="ID do plano")


@tool(args_schema=PERTInput)
def pert_tool(plan_id: str) -> str:
    """
    Calcula P50, P90 e P95 via aproximação normal:
    - media por tarefa: (o + 4m + p) / 6
    - sigma por tarefa: (p - o) / 6
    """
    tasks_pert = fetch_pert_data(plan_id)

    if not tasks_pert:
        raise ValueError("Nenhum dado PERT encontrado para o plano informado.")

    mu_total = 0.0
    sigma2_total = 0.0

    for o, m, p in tasks_pert:
        if o < 0 or m < 0 or p < 0:
            raise ValueError("Valores PERT não podem ser negativos.")
        if p < o:
            raise ValueError("Valor pessimista (p) não pode ser menor que otimista (o).")

        mu = (o + 4.0 * m + p) / 6.0
        sigma = (p - o) / 6.0

        mu_total += mu
        sigma2_total += sigma * sigma

    sigma_total = math.sqrt(sigma2_total)

    p50 = mu_total
    p90 = mu_total + 1.2816 * sigma_total
    p95 = mu_total + 1.6449 * sigma_total

    return (
        f"Plano: {plan_id}\n"
        f"P50: {p50:.2f}h\n"
        f"P90: {p90:.2f}h\n"
        f"P95: {p95:.2f}h\n"
        f"Desvio padrao: ±{sigma_total:.2f}h"
    )