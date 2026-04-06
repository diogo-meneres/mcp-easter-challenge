from collections import deque
from typing import Dict, List, Tuple

from DB_Tool import get_db_connection, release_db_connection

def fetch_tasks_and_dependencies(plan_id: str) -> Tuple[List[dict], List[dict]]:
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, duration_h FROM tasks WHERE plan_id = %s", (plan_id,))
            tasks = cursor.fetchall()
            
            cursor.execute("SELECT from_task_id, to_task_id, lag_h FROM task_dependencies WHERE plan_id = %s", (plan_id,))
            deps = cursor.fetchall()
            
            return tasks, deps  
    finally:
        if 'conn' in locals() and conn is not None:
            release_db_connection(conn)


def _build_graph(tasks: List[dict], deps: List[dict]) -> Dict[str, dict]:
    if not tasks:
        raise ValueError("Nenhuma tarefa encontrada para o plano informado.")

    task_map: Dict[str, dict] = {}
    for t in tasks:
        task_id = str(t["id"])
        dur = float(t["duration_h"] or 0)
        if dur < 0:
            raise ValueError(f"duration_h negativo na tarefa {task_id}")

        task_map[task_id] = {
            "id": task_id,
            "duration_h": dur,
            "predecessores": [],  # lista de (pred_id, lag_h)
            "sucessores": [],  # lista de (succ_id, lag_h)
            "ES": 0.0,
            "EF": 0.0,
            "LS": 0.0,
            "LF": 0.0,
        }

    for d in deps:
        from_id = str(d["from_task_id"])
        to_id = str(d["to_task_id"])
        lag_h = float(d.get("lag_h", 0) or 0)

        if from_id not in task_map or to_id not in task_map:
            raise ValueError(f"Dependencia invalida: {from_id} -> {to_id}")
        if from_id == to_id:
            raise ValueError(f"Auto-dependencia detetada na tarefa {from_id}")

        task_map[to_id]["predecessores"].append((from_id, lag_h))
        task_map[from_id]["sucessores"].append((to_id, lag_h))

    return task_map

def _topological_order(task_map: Dict[str, dict]) -> List[str]:
    indegree = {task_id: 0 for task_id in task_map}

    for task_id in task_map:
        for succ_id, _ in task_map[task_id]["sucessores"]:
            indegree[succ_id] += 1

    queue = deque([task_id for task_id, deg in indegree.items() if deg == 0])
    order: List[str] = []

    while queue:
        current = queue.popleft()
        order.append(current)

        for succ_id, _ in task_map[current]["sucessores"]:
            indegree[succ_id] -= 1
            if indegree[succ_id] == 0:
                queue.append(succ_id)

    if len(order) != len(task_map):
        raise ValueError("Ciclo detetado no grafo de dependencias (CPM invalido).")

    return order

def cpm_tool(plan_id: str) -> str:
    """
    Calcula CPM:
    - ES/EF (forward pass)
    - LS/LF (backward pass)
    - TS (total slack)
    - tarefas críticas (TS ~= 0)
    """
    tasks, deps = fetch_tasks_and_dependencies(plan_id)
    task_map = _build_graph(tasks, deps)
    order = _topological_order(task_map)

    # Forward pass
    for task_id in order:
        task = task_map[task_id]
        if task["predecessores"]:
            task["ES"] = max(task_map[pred]["EF"] + lag for pred, lag in task["predecessores"])
        else:
            task["ES"] = 0.0
        task["EF"] = task["ES"] + task["duration_h"]

    project_duration = max(task_map[task_id]["EF"] for task_id in order)

    # Backward pass
    for task_id in reversed(order):
        task = task_map[task_id]
        if task["sucessores"]:
            task["LF"] = min(task_map[succ]["LS"] - lag for succ, lag in task["sucessores"])
        else:
            task["LF"] = project_duration
        task["LS"] = task["LF"] - task["duration_h"]

    eps = 1e-9
    critical_tasks: List[str] = []
    output_lines: List[str] = []

    for task_id in order:
        t = task_map[task_id]
        ts = t["LS"] - t["ES"]
        is_critical = abs(ts) <= eps

        if is_critical:
            critical_tasks.append(task_id)

        output_lines.append(
            f"{task_id}: ES={t['ES']:.2f} EF={t['EF']:.2f} "
            f"LS={t['LS']:.2f} LF={t['LF']:.2f} TS={ts:.2f} "
            f"{'CRITICA' if is_critical else ''}"
        )

    return (
        f"Plano: {plan_id}\n"
        f"Duracao total: {project_duration:.2f}h\n"
        f"Tarefas criticas: {' -> '.join(critical_tasks) if critical_tasks else '(nenhuma)'}\n\n"
        + "\n".join(output_lines)
    )