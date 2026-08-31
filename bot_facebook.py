import os
import time
import requests
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LlhLdStch5R9CeKr0Aam13egubrZuj3Cx1868P2flcgw")
client = genai.Client(api_key=GEMINI_API_KEY)

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

posts_processados = set()

def classificar_promocao(texto_post):
    prompt = f"""
    Sua tarefa é analisar o texto de uma promoção e classificá-lo estritamente em UMA destas 5 categorias:
    - BEBE_INFANTIL
    - AUTOMOTIVO
    - MODA_FEMININA
    - MODA_MASCULINA
    - ELETRONICOS

    Regras:
    - Responda APENAS com o nome da categoria exata em letras maiúsculas.
    - Não adicione explicações, pontuação ou texto adicional.

    Texto da promoção:
    \"\"\"{texto_post}\"\"\"
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        categoria = response.text.strip().upper()
        if categoria in PAGINAS_DESTINO:
            return categoria
        else:
            print(f"[AVISO IA] Categoria não identificada: {categoria}")
            return None
    except Exception as e:
        print(f"[ERRO GEMINI] Falha ao classificar com a IA: {e}")
        return None

def buscar_ultimo_post():
    url = f"https://graph.facebook.com/v20.0/{PAGINA_ORIGEM_ID}/posts"
    params = {
        "access_token": PAGINA_ORIGEM_TOKEN,
        "limit": 1,
        "fields": "id,message,full_picture,created_time"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]
    except Exception as e:
        print(f"[ERRO FACEBOOK] Falha ao buscar posts: {e}")
    return None

def republicar_para_destino(post, categoria):
    destino = PAGINAS_DESTINO.get(categoria)
    if not destino:
        return False

    url = f"https://graph.facebook.com/v20.0/{destino['id']}/photos" if "full_picture" in post else f"https://graph.facebook.com/v20.0/{destino['id']}/feed"
    
    payload = {
        "access_token": destino["token"],
        "message": post.get("message", "")
    }
    if "full_picture" in post:
        payload["url"] = post["full_picture"]

    try:
        resp = requests.post(url, data=payload, timeout=15)
        res_data = resp.json()
        if "id" in res_data:
            print(f"✅ [SUCESSO] Post {post['id']} publicado na página {categoria}!")
            return True
        else:
            print(f"❌ [ERRO FB] Resposta inválida: {res_data}")
    except Exception as e:
        print(f"❌ [ERRO FB] Falha ao republicar em {categoria}: {e}")
    return False

def executar_bot():
    print("🤖 Bot Distribuidor de Conteúdo Iniciado!")
    post = buscar_ultimo_post()
    if not post:
        print("📭 Nenhum post encontrado na página de origem.")
        return

    post_id = post["id"]
    if post_id in posts_processados:
        print(f"⏳ Post {post_id} já foi processado anteriormente.")
        return

    mensagem = post.get("message", "")
    if not mensagem:
        print(f"⚠️ Post {post_id} não contém texto para classificação.")
        return

    print(f"🔍 Novo post detectado: {post_id}")
    print("🤖 Classificando categoria com o Gemini...")
    
    categoria = classificar_promocao(mensagem)
    if categoria:
        print(f"🎯 Categoria identificada: {categoria}")
        sucesso = republicar_para_destino(post, categoria)
        if sucesso:
            posts_processados.add(post_id)
    else:
        print("⚠️ Post não pertence a nenhuma das 5 categorias configuradas.")

if __name__ == "__main__":
    executar_bot()
