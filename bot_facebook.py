import os
import time
import requests
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
    """
    Fallback caso a Gemini não esteja disponível.
    As palavras-chave servem apenas como auxílio.
    Se não houver correspondência clara, envia para PromoManiaOfertas.
    """
    texto_lower = texto.lower()

    palavras_outros = [
        "pote", "potes",
        "escorredor", "escorredor de louça", "escorredor de pratos",
        "talheres", "garfo", "faca", "colher",
        "prato", "panela", "frigideira", "assadeira", "forma",
        "travessa", "copo", "taça", "jarra",
        "ralador", "peneira", "abridor",
        "tábua de corte", "tábua de cozinha",
        "utensílio de cozinha", "utensilios de cozinha",
        "organizador de cozinha",
        "cozinha", "casa", "utilidades domésticas",
        "limpeza", "organizador doméstico"
    ]

    if any(termo in texto_lower for termo in palavras_outros):
        return "PROMONOMIA_OFERTAS"

    keywords = {
        "BEBE_INFANTIL": [
            "fralda", "bebê", "bebe", "infantil",
            "mamadeira", "chocalho", "carrinho de bebê",
            "body infantil", "brinquedo infantil"
        ],
        "AUTOMOTIVO": [
            "carro", "moto", "pneu", "capacete",
            "óleo automotivo", "oleo automotivo",
            "automotivo", "led para carro",
            "suporte celular carro", "suporte veicular",
            "amortecedor", "porta malas",
            "tampa traseira"
        ],
        "MODA_FEMININA": [
            "vestido", "saia", "blusa feminina",
            "sutiã", "lingerie", "bolsa feminina",
            "salto", "saltos", "maquiagem"
        ],
        "MODA_MASCULINA": [
            "camisa masculina", "camiseta masculina",
            "barbeador", "carteira masculina",
            "bermuda masculina", "sapato masculino"
        ],
        "ELETRONICOS": [
            "fone", "fone bluetooth", "bluetooth",
            "celular", "carregador", "smartwatch",
            "smart watch", "tv", "televisão",
            "notebook", "xiaomi", "cabo usb",
            "cabo tipo c", "cabo usb-c",
            "tablet", "mouse", "teclado",
            "caixa de som", "headset"
        ]
    }

    for cat, termos in keywords.items():
        if any(termo in texto_lower for termo in termos):
            return cat

    return "PROMONOMIA_OFERTAS"

def classificar_promocao(texto_post):
    """
    Gemini é o classificador principal.
    As palavras-chave são utilizadas somente como fallback.
    """
    if GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
Você é o classificador oficial das páginas PromoMania.

Analise cuidadosamente o PRODUTO anunciado no texto abaixo.

Você deve escolher EXATAMENTE UMA destas categorias:

BEBE_INFANTIL
AUTOMOTIVO
MODA_FEMININA
MODA_MASCULINA
ELETRONICOS
OUTROS

REGRAS IMPORTANTES:

1. Classifique pelo produto, sua finalidade e seu contexto completo.
2. NÃO classifique simplesmente porque uma palavra-chave aparece no texto.
3. Só escolha uma das 5 categorias específicas quando o produto pertencer claramente a ela.
4. Se o produto for de CASA, COZINHA, UTILIDADES DOMÉSTICAS, LIMPEZA,
   ORGANIZAÇÃO, DECORAÇÃO ou qualquer outra área que não esteja entre
   as 5 categorias específicas, responda OUTROS.
5. Potes, escorredores, panelas, talheres, pratos, utensílios de cozinha,
   organizadores domésticos e produtos semelhantes são OUTROS.
6. Se houver dúvida razoável entre duas categorias, responda OUTROS.
7. NÃO tente encaixar um produto em uma categoria apenas para evitar OUTROS.
8. OUTROS significa que o produto deve ser enviado para PromoManiaOfertas.
9. Analise o produto principal anunciado, e não acessórios ou palavras
   secundárias presentes na descrição.
10. Responda SOMENTE com uma das 6 opções abaixo, sem explicação:

BEBE_INFANTIL
AUTOMOTIVO
MODA_FEMININA
MODA_MASCULINA
ELETRONICOS
OUTROS

TEXTO DA PROMOÇÃO:
\"\"\"{texto_post}\"\"\"
"""
            modelos = [
                "gemini-3.6-flash",
                "gemini-3.5-flash"
            ]

            for modelo in modelos:
                try:
                    response = client.models.generate_content(
                        model=modelo,
                        contents=prompt,
                        config={
                            "automatic_function_calling": {
                                "disable": True
                            }
                        }
                    )

                    categoria = response.text.strip().upper()
                    categoria = categoria.replace(".", "").replace(":", "").strip()

                    categorias_validas = {
                        "BEBE_INFANTIL",
                        "AUTOMOTIVO",
                        "MODA_FEMININA",
                        "MODA_MASCULINA",
                        "ELETRONICOS",
                        "OUTROS"
                    }

                    if categoria == "OUTROS":
                        return "PROMONOMIA_OFERTAS"

                    if categoria in categorias_validas:
                        return categoria

                except Exception as e:
                    print(f"[IA AVISO] Erro no modelo {modelo}: {e}")

        except Exception as e:
            print(f"[IA AVISO] Falha ao inicializar o cliente Gemini: {e}")

    return classificar_por_palavras_chave(texto_post)

def buscar_posts_origem(limite=10):
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
    
    posts = buscar_posts_origem(limite=10)
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
