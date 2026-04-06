from fastmcp import FastMCP

from Resource_Tool import resource_tool as planning_resource_tool
from CPM_Tool import cpm_tool as planning_cpm_tool
from PERT_Tool import pert_tool as planning_pert_tool

from DB_Tool import check_mysql_connection as logic_db_check
from DB_Tool import fetch_all_plans

mcp = FastMCP("PlannerServer")

# 2. Registar a ferramenta do Gabriel no MCP
@mcp.tool()
def resource_tool(plan_id: str) -> str:
    """Analisa a carga de trabalho dos recursos (Overload) para um dado plan_id."""
    return planning_resource_tool(plan_id)

@mcp.tool()
def cpm_tool(plan_id: str) -> str:
    """Calcula o Critical Path Method (CPM) para um dado plan_id."""
    return planning_cpm_tool(plan_id)

@mcp.tool()
def pert_tool(plan_id: str) -> str:
    """Calcula as estimativas PERT (P50, P90, P95) para um dado plan_id."""
    return planning_pert_tool(plan_id)

@mcp.tool()
def test_db_connection() -> str:
    """Verifica se o servidor MySQL está acessível e pronto para receber comandos."""
    # Chamada direta e simples, sem .invoke() nem dicionários!
    return logic_db_check()

@mcp.tool()
def list_available_plans() -> str:
    """Lista todos os IDs e detalhes dos planos existentes na base de dados."""
    return fetch_all_plans()

if __name__ == "__main__":
    mcp.run(transport="stdio")