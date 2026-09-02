import os
import time
import requests
import re

PAGINA_ORIGEM_ID = "1214303865109377"
PAGINA_ORIGEM_TOKEN = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

PAGINAS_DESTINO = {
    "BEBE_INFANTIL": {
        "id": "1214563361750206",
        "token": "EAAPFihJ9FJcBSdespc7VwtM9EyGZCm7CbRoPJ94WLZBZBsSXZAZBkjwtstxV4x0laEifWI26akmjosi883ZCAT7XPbQcnC5ONRPoaFH1aE6oXHUp5cvO1IHrZCoy09ZAp64M9uy3LNeNgIFsiajXDa83NGYKeyGdZBZBE5FS2xDiffRjOLzrMjtyj2pEXKPRfHEnGYZBpKA"
    },
    "AUTOMOTIVO": {
        "id": "1237238682815031",
        "token": "EAAPFihJ9FJcBSTc9xPtGPFIzMOvSowsCwYCYtYGhGbFGAwcGzQZBVxD12CzfD07QYeOL2NUo60iZCc8VaLe5kaNdvb4ucQaZB6bjz9p3JDZAswXW6V65efdBROok7wuc5hWC0fZBxTaTAWFmT5ECY4kwufZAZCiEjqFQBR8ocKvZBn4ZAmAVjjMZA5pzrZA8Qb4nCsi6SF3DWIu"
    },
    "MODA_FEMININA": {
        "id": "1354603781059423",
        "token": "EAAPFihJ9FJcBSSRyA7r1ZBp8XjDpZBZCI5kbBZCrhP9twlHOyLuNYRhqrA9KS50Wal5O4ZAg6baAl8O5VPT0gFhSNdBynMLsnflcSekcRIt6FrOeQJ90mJHqxlI0BmlEOXlWASWprE54LdARYpPr8SnDXVpXqGCncZC96gqvu7JlWJeXo7AwYDWr3FQk44gvwxNo0n"
    },
    "MODA_MASCULINA": {
        "id": "1226863517186687",
        "token": "EAAPFihJ9FJcBSXdZAf6qETU3aSuzE0VtVWtffFYrlCglPmyTnQtAQb5zKkohioKuqBztbXOZCUDvZAbv2ihkF4foVGW7KhvAIvBMvqqNZAEKjxLwllCNRwGU0xSJf2aW7OdpOTSS1vcCSqU1yy4Fx7zEz8EoL0vhPyKwbSXNgSq3GqPVUnqcTf1dm1k9ij5DFlwF"
    },
    "ELETRONICOS": {
        "id": "1330088230179474",
        "token": "EAAPFihJ9FJcBSbcBsbl9WoqGztGBiGaJi9ORgJmUMoLpZCGD5BFp2qbZA3mC1kcyZCJVQ32ldZCLYACpQ5DSuh4mmKdWtOAdUuRzoImnbooiSVS3t56EnY9jqdguUlN6TQlNPq9kL4RU3OoEBR5zP0JUg9Uu4BkSgcYRQtmRqLg3Tb0z9d2ZBhLfUfZAHGvR6PpFr9mZCk6"
    }
}

ARQUIVO_HISTORICO = os.path.expanduser("posts_processados.txt")

def carregar_historico():
    if os.path.exists(ARQUIVO_HISTORICO):
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def salvar_no_historico(post_id):
    with open(ARQUIVO_HISTORICO, "a", encoding="utf-8") as f:
        f.write(f"{post_id}\n")

def classificar_por_palavras_chave(texto):
    if not texto:
        return None
    texto_lower = texto.lower()
    keywords = {
        "BEBE_INFANTIL": ["fralda", "mamadeira", "chocalho", "carrinho", "body", "berço", "naninha", "bebe", "infantil"],
        "AUTOMOTIVO": ["pneu", "capacete", "oleo", "amortecedor", "palheta", "cera", "moto", "carro", "automotivo"],
        "MODA_FEMININA": ["vestido", "saia", "sutia", "lingerie", "maquiagem", "batom", "salto", "feminina", "feminino"],
        "MODA_MASCULINA": ["barbeador", "camisa", "bermuda", "sapato", "masculina", "masculino"],
        "ELETRONICOS": ["fone", "smartwatch", "tv", "notebook", "tablet", "monitor", "ssd", "bluetooth", "eletronicos", "celular", "smartphone", "shopee"]
    }
    for cat, termos in keywords.items():
        for termo in termos:
            if re.search(rf'\b{termo}\b', texto_lower):
                return cat
    return None

def buscar_ultimo_video():
    # Busca direto no endpoint de vídeos da página, garantindo o acesso ao conteúdo multimídia
    url = f"https://graph.facebook.com/v20.0/{PAGINA_ORIGEM_ID}/videos"
    params = {
        "access_token": PAGINA_ORIGEM_TOKEN,
        "limit": 1,
        "fields": "id,description,source,created_time,title"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "data" in data and len(data["data"]) > 0:
            v = data["data"][0]
            # Padroniza a estrutura para manter compatibilidade com o restante do script
            return {
                "id": v.get("id"),
                "message": v.get("description") or v.get("title") or "",
                "source": v.get("source")
            }
    except Exception as e:
        print(f"[ERRO FACEBOOK] {e}")
    return None

def republicar_para_destino(video_obj, categoria):
    destino = PAGINAS_DESTINO.get(categoria)
    if not destino:
        return False

    midia_url = video_obj.get("source")
    texto_extraido = video_obj.get("message", "")

    if not midia_url:
        print("❌ [ERRO] URL de origem do vídeo não encontrada.")
        return False

    url = f"https://graph.facebook.com/v20.0/{destino['id']}/videos"
    payload = {
        "access_token": destino["token"], 
        "description": texto_extraido if texto_extraido else "Achados Shopee", 
        "file_url": midia_url
    }

    try:
        resp = requests.post(url, data=payload, timeout=30)
        res_data = resp.json()
        if "id" in res_data:
            print(f"✅ [SUCESSO] Vídeo encaminhado para a página de nicho: {categoria}!")
            return True
        else:
            print(f"❌ [ERRO FB]: {res_data}")
    except Exception as e:
        print(f"❌ [ERRO FB] Falha: {e}")
    return False

def executar_bot():
    posts_processados = carregar_historico()
    print("🤖 [FILA] Verificando novos vídeos na página promomaniaofertas...")
    
    video = buscar_ultimo_video()
    if not video:
        print("📭 Nenhum vídeo encontrado.")
        return

    post_id = video["id"]

    if post_id in posts_processados:
        print("⏳ Nenhum vídeo novo encontrado.")
        return

    texto_post = video.get("message", "")
    print(f"🔍 Legenda do vídeo detectada: '{texto_post}'")

    categoria = classificar_por_palavras_chave(texto_post)
    if not categoria:
        categoria = "ELETRONICOS" # Categoria padrão para testes se não houver palavra-chave exata

    print(f"🎯 Vídeo classificado para o nicho: {categoria}")
    sucesso = republicar_para_destino(video, categoria)
    if sucesso:
        salvar_no_historico(post_id)

if __name__ == "__main__":
    executar_bot()
