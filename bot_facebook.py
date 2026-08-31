import os
import time
import requests
from google import genai

# ==========================================
# 1. CONFIGURAÇÕES DAS APIS
# ==========================================

# Configuração do Gemini SDK Oficial
# Se você definir no Termux com 'export GEMINI_API_KEY="sua_chave"', ele pega automático.
# Se preferir colar direto aqui, troque "SUA_GEMINI_API_KEY_AQUI" pela sua chave entre aspas.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6LlhLdStch5R9CeKr0Aam13egubrZuj3Cx1868P2flcgw")
client = genai.Client(api_key=GEMINI_API_KEY)

# Configuração da Página Principal (Origem das Promoções - PromoMania)
PAGINA_ORIGEM_ID = "1214303865109377"
PAGINA_ORIGEM_TOKEN = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

# Configuração das Páginas de Destino (Com IDs Reais)
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

# Histórico na memória para impedir publicações duplicadas
posts_processados = set()


# ==========================================
# 2. FUNÇÕES DO SISTEMA
# ==========================================

def classificar_promocao(texto_post):
    """Analisa o texto da promoção usando a IA do Gemini 2.5 Flash e retorna a categoria."""
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
            model='gemini-3.6-flash',
            contents=prompt,
        )
        categoria = response.text.strip().upper()
        if categoria in PAGINAS_DESTINO:
            return categoria
        else:
            print(f"[AVISO IA] Categoria desconhecida retornada: {categoria}")
            return None
    except Exception as e:
        print(f"[ERRO GEMINI] Falha ao classificar com a IA: {e}")
        return None


def buscar_ultimo_post():
    """Busca a última publicação da página principal do Facebook."""
    url = f"https://graph.facebook.com/v20.0/{PAGINA_ORIGEM_ID}/posts"
    params = {
        "access_token": PAGINA_ORIGEM_TOKEN,
        "limit": 1,
        "fields": "id,message,full_picture,created_time"
    }
    try:
        response = requests.get(url, params=params)
        dados = response.json()
        if "data" in dados and len(dados["data"]) > 0:
            return dados["data"][0]
        return None
    except Exception as e:
        print(f"[ERRO FACEBOOK API] Falha ao buscar posts: {e}")
        return None


def publicar_na_pagina(pagina_id, page_token, mensagem, imagem_url=None):
    if imagem_url:
        try:
            # Baixa a imagem temporariamente
            img_res = requests.get(imagem_url, timeout=10)
            if img_res.status_code == 200:
                with open("temp_img.jpg", "wb") as f:
                    f.write(img_res.content)
                
                url = f"https://graph.facebook.com/v20.0/{pagina_id}/photos"
                payload = {
                    "message": mensagem,
                    "access_token": page_token
                }
                with open("temp_img.jpg", "rb") as img_file:
                    files = {"source": img_file}
                    response = requests.post(url, data=payload, files=files)
                return "id" in response.json() or "post_id" in response.json()
        except Exception as e:
            print(f"[AVISO IMAGEM] Falha ao baixar/enviar foto: {e}")

    # Fallback para apenas texto caso nao haja imagem ou ocorra erro
    url = f"https://graph.facebook.com/v20.0/{pagina_id}/feed"
    payload = {
        "message": mensagem,
        "access_token": page_token
    }
    response = requests.post(url, data=payload)
    return "id" in response.json() or "post_id" in response.json()
    """Publica a promoção na página temática correspondente."""
    url = f"https://graph.facebook.com/v20.0/{pagina_id}/feed"
    payload = {
        "message": mensagem,
        "access_token": page_token
    }
    try:
        response = requests.post(url, data=payload)
        res_json = response.json()
        if "id" in res_json:
            print(f"[SUCESSO] Post publicado com sucesso na página ID {pagina_id}! ID do Post: {res_json['id']}")
            return True
        else:
            print(f"[ERRO PUBLICACAO] Erro da API do Facebook: {res_json}")
            return False
    except Exception as e:
        print(f"[ERRO PUBLICACAO] Falha ao enviar requisição: {e}")
        return False


# ==========================================
# 3. LOOP DE EXECUÇÃO AUTOMÁTICA (24/7)
# ==========================================

def executar_automacao():
    print("=" * 60)
    print("🚀 AUTOMAÇÃO PROMOMANIA INICIADA COM SUCESSO!")
    print("Monitorando a página principal a cada 15 minutos...")
    print("=" * 60)

    while True:
        try:
            print("\n[VERIFICAÇÃO] Checando novas publicações...")
            ultimo_post = buscar_ultimo_post()

            if ultimo_post:
                post_id = ultimo_post.get("id")
                mensagem = ultimo_post.get("message", "")
                imagem_url = ultimo_post.get("full_picture", None)

                if post_id not in posts_processados:
                    if mensagem:
                        print(f"📌 Novo post detectado! ID: {post_id}")
                        print(f"📝 Texto: {mensagem[:80]}...")

                        # Classificação via IA
                        categoria = classificar_promocao(mensagem)

                        if categoria:
                            print(f"🤖 IA identificou a categoria: {categoria}")
                            destino = PAGINAS_DESTINO[categoria]
                            
                            # Publicação na página temática
                            sucesso = publicar_na_pagina(
                                pagina_id=destino["id"],
                                page_token=destino["token"],
                                mensagem=mensagem,
                                imagem_url=imagem_url
                            )

                            if sucesso:
                                posts_processados.add(post_id)
                        else:
                            print("[PULADO] Não foi possível categorizar a oferta.")
                    else:
                        print("[PULADO] O post não possui mensagem de texto.")
                else:
                    print("⌛ Nenhum post novo por enquanto.")
            else:
                print("⚠️ Nenhum post retornado da página de origem.")

        except Exception as e:
            print(f"[ERRO NO LOOP] Ocorreu uma exceção inesperada: {e}")

        # Aguarda 15 minutos (900 segundos) para a próxima verificação
        time.sleep(60)


if __name__ == "__main__":
    executar_automacao()









