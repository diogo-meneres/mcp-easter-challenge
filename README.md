# mcp-easter-challenge

## Levantar a base de dados
```bash
docker compose down -v
docker compose up -d
docker compose logs -f
```

## Instruções para correr o projeto
1. Criar o ambiente dele (limpo e compatível):
```bash
python -m venv venv
```
2. Ativar o ambiente:
```bash
source venv/bin/activate  # No Mac/Linux
# ou .\venv\Scripts\activate no Windows
```
3. Instalar tudo
```bash
pip install -r requirements.txt
```
4. Correr num terminal o server
```bash
python server.py
```
5. Correr noutro terminal o agent
```bash
python agent.py
```


## Para reativar o venv
```bash
source venv/bin/activate
```
