from fastmcp import FastMCP

from Resource_Tool import resource_tool as planning_resource_tool
from CPM_Tool import cpm_tool as planning_cpm_tool
from PERT_Tool import pert_tool as logic_pert_tool

mcp = FastMCP("PlannerServer")

# 2. Registar a ferramenta do Gabriel no MCP
@mcp.tool()
def resource_tool(plan_id: str) -> str:
    """Analisa a carga de trabalho dos recursos (Overload) para um dado plan_id."""
    return planning_resource_tool.invoke({"plan_id": plan_id})

@mcp.tool()
def cpm_tool(plan_id: str) -> str:
    """Calcula o Critical Path Method (CPM) para um dado plan_id."""
    return planning_cpm_tool.invoke({"plan_id": plan_id})

@mcp.tool()
def pert_tool(plan_id: str) -> str:
    """Calcula as estimativas PERT (P50, P90, P95) para um dado plan_id."""
    return logic_pert_tool.invoke({"plan_id": plan_id})

if __name__ == "__main__":
    mcp.run(transport="stdio")