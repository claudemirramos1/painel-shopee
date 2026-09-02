import os
import time
import requests
import re
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

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
    },
    "PROMONOMIA_OFERTAS": {
        "id": "1214303865109377",
        "token": "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"
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
    texto_lower = texto.lower()

    palavras_casa_cozinha = [
        "pote", "escorredor", "louça", "talheres", "garfo", "faca", "colher",
        "prato", "panela", "frigideira", "assadeira", "taça", "jarra",
        "ralador", "tábua", "utensílio", "limpeza", "mop", "vassoura", "sabão"
    ]
    if any(termo in texto_lower for termo in palavras_casa_cozinha):
        return "PROMONOMIA_OFERTAS"

    keywords = {
        "BEBE_INFANTIL": ["fralda", "mamadeira", "chocalho", "carrinho de bebê", "body infantil", "berço", "naninha"],
        "AUTOMOTIVO": ["pneu", "capacete", "óleo automotivo", "amortecedor", "palheta", "cera automotiva", "moto"],
        "MODA_FEMININA": ["vestido", "saia", "sutiã", "lingerie", "maquiagem", "batom", "salto alto"],
        "MODA_MASCULINA": ["barbeador", "camisa masculina", "bermuda masculina", "sapato masculino"],
        "ELETRONICOS": ["fone bluetooth", "smartwatch", "tv", "notebook", "tablet", "monitor", "placa de vídeo", "ssd"]
    }

    for cat, termos in keywords.items():
        for termo in termos:
            if re.search(rf'\b{termo}\b', texto_lower):
                return cat

    return "PROMONOMIA_OFERTAS"

def classificar_promocao(texto_post):
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            
            prompt = f"""
Você é um classificador estrito de e-commerce. Sua função é ler a oferta e determinar a categoria do produto principal.

**Regras de Classificação Absolutas:**
1. Foque EXCLUSIVAMENTE no PRODUTO QUE ESTÁ SENDO VENDIDO, não nos adjetivos ou públicos secundários.
2. Produtos de Casa, Cozinha, Organização, Limpeza ou Ferramentas (ex: Potes, Panelas, Mop, Furadeira) NÃO pertencem às categorias específicas. Devem ser "OUTROS".
3. Moda é estritamente roupa/acessório/beleza. "Fralda" não é moda feminina, é "BEBE_INFANTIL".
4. Se o texto fala de um smartphone, placa-mãe ou periférico, é "ELETRONICOS".
5. Se não for 100% óbvio que pertence a uma das 5 categorias restritas, responda "OUTROS".

TEXTO DA OFERTA:
"{texto_post}"

Responda APENAS com UMA destas palavras-chave oficiais e nada mais:
BEBE_INFANTIL
AUTOMOTIVO
MODA_FEMININA
MODA_MASCULINA
ELETRONICOS
OUTROS
"""
            modelos = ["gemini-3.6-flash", "gemini-3.1-pro-preview"]

            for modelo in modelos:
                try:
                    response = client.models.generate_content(
                        model=modelo,
                        contents=prompt,
                        config={
                            "temperature": 0.0,
                            "automatic_function_calling": {"disable": True}
                        }
                    )

                    categoria = response.text.strip().upper().replace(".", "").replace(":", "")
                    categorias_validas = {"BEBE_INFANTIL", "AUTOMOTIVO", "MODA_FEMININA", "MODA_MASCULINA", "ELETRONICOS"}

                    if categoria in categorias_validas:
                        return categoria
                    else:
                        return "PROMONOMIA_OFERTAS"

                except Exception as e:
                    print(f"[IA AVISO] Erro no modelo {modelo}: {e}")

        except Exception as e:
            print(f"[IA AVISO] Falha ao inicializar o cliente Gemini: {e}")

    return classificar_por_palavras_chave(texto_post)

def buscar_posts_origem(limite=1):
    url = f"https://graph.facebook.com/v20.0/{PAGINA_ORIGEM_ID}/posts"
    params = {
        "access_token": PAGINA_ORIGEM_TOKEN,
        "limit": limite,
        "fields": "id,message,full_picture,created_time"
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if "data" in data:
            return data["data"]
    except Exception as e:
        print(f"[ERRO FACEBOOK] Falha ao buscar posts: {e}")
    return []

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
    posts_processados = carregar_historico()
    print("🤖 [FILA] Buscando posts recentes e cruzando com a âncora...")
    
    posts = buscar_posts_origem(limite=1)
    if not posts:
        print("📭 Nenhum post retornado do Facebook.")
        return

    novos_posts = [p for p in posts if p["id"] not in posts_processados]
    
    if not novos_posts:
        print("⏳ Nenhum produto novo pendente. A âncora está atualizada!")
        return

    print(f"🔍 Encontrados {len(novos_posts)} novos produtos para processar.")
    
    for post in reversed(novos_posts):
        post_id = post["id"]
        mensagem = post.get("message", "")
        
        if mensagem:
            print(f"\n📦 Processando post ID: {post_id}")
            categoria = classificar_promocao(mensagem)
            if categoria:
                print(f"🎯 Categoria identificada: {categoria}")
                sucesso = republicar_para_destino(post, categoria)
                if sucesso:
                    salvar_no_historico(post_id)
            else:
                print("⚠️ Post sem categoria válida. Registrando no histórico.")
                salvar_no_historico(post_id)
        else:
            salvar_no_historico(post_id)
        
        time.sleep(5)

if __name__ == "__main__":
    executar_bot()
