import asyncio
import json
from datetime import datetime
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def log_message(role: str, content: str):
    """Guarda as mensagens num ficheiro de texto."""
    with open("chat_history.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {role}:\n{content}\n{'-'*40}\n")

async def iniciar_agente():
    llm = AsyncOpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
    
    server_params = StdioServerParameters(command="python", args=["server.py"])

    print("🔄 A iniciar Servidor MCP...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            ferramentas_mcp = await session.list_tools()
            ferramentas_llm = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                } for t in ferramentas_mcp.tools
            ]

            print("\n✅ Agente pronto! (Escreve 'sair' para terminar)")

            while True:
                pergunta = input("\n👤 Tu: ")
                if pergunta.lower() in ['sair', 'exit', 'quit']:
                    print("Até à próxima!")
                    break
                
                log_message("Utilizador", pergunta)
                
                print("🧠 A pensar...")
                # Envia APENAS a pergunta atual (sem histórico na memória)
                messages = [
                    {"role": "system", "content": "És um gestor de projetos. Usa as ferramentas disponíveis para ajudar o utilizador."},
                    {"role": "user", "content": pergunta}
                ]
                
                resposta_llm = await llm.chat.completions.create(
                    model="local-model",
                    messages=messages,
                    tools=ferramentas_llm
                )

                mensagem = resposta_llm.choices[0].message
                
                if mensagem.tool_calls:
                    acao = mensagem.tool_calls[0]
                    nome_ferramenta = acao.function.name
                    print(f"🛠️ A consultar base de dados (Ferramenta: {nome_ferramenta})...")
                    
                    resultado_mcp = await session.call_tool(
                        nome_ferramenta, 
                        arguments=json.loads(acao.function.arguments)
                    )
                    
                    # Imprime e regista o resultado cru da ferramenta (sem 2ª chamada ao LLM)
                    resultado_texto = resultado_mcp.content[0].text
                    print(f"\n📥 RESULTADO DO MCP:\n{resultado_texto}")
                    log_message(f"Ferramenta ({nome_ferramenta})", resultado_texto)

                else:
                    texto_agente = mensagem.content
                    print(f"\n🤖 Agente: {texto_agente}")
                    log_message("Agente", texto_agente)

if __name__ == "__main__":
    asyncio.run(iniciar_agente())