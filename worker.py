import os
import json
import io
import re
import time
import tempfile
import requests
from PIL import Image, ImageOps
from google import genai
from juntar_video_foto import juntar_video_foto

SUPABASE_URL = "https://ftumdeqziwyljmaehaqk.supabase.co"
SUPABASE_KEY = "sb_publishable_8qfsBhW22Sx25mvPcxWNvw_4teJRbfu"

TELEGRAM_CANAL_TOKEN = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TELEGRAM_CANAL_ID = "-1004406728710"

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

print("🤖 Iniciando Worker Inteligente com Roteamento Multi-Categorias...")

def carregar_rascunhos():
    try:
        url = f"{SUPABASE_URL}/rest/v1/ofertas?select=*&order=created_at.asc&limit=1"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200: return []
        return r.json()
    except:
        return []

def remover_rascunho(rascunho_id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/ofertas?id=eq.{rascunho_id}"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        requests.delete(url, headers=headers, timeout=20)
        print(f"🗑️ Oferta {rascunho_id} removida da fila.")
    except:
        pass

def classificar_por_palavras_chave(texto):
    texto_lower = texto.lower()
    categorias_encontradas = []

    if any(k in texto_lower for k in ["infantil", "bebe", "nenem", "crianca", "brinquedo", "chupeta", "fralda", "maternidade", "carrinho de bebe"]):
        categorias_encontradas.append("BEBE_INFANTIL")
    if any(k in texto_lower for k in ["carro", "moto", "automotivo", "veiculo", "pneu", "retrovisor", "farol", "volante", "tapete automotivo"]):
        categorias_encontradas.append("AUTOMOTIVO")
    if any(k in texto_lower for k in ["fone", "bluetooth", "smartphone", "celular", "carregador", "smartwatch", "cabo usb", "lampada led", "caixa de som", "gamer", "mouse", "teclado"]):
        categorias_encontradas.append("ELETRONICOS")
    if any(k in texto_lower for k in ["vestido", "feminina", "bolsa", "cropped", "saia", "salto", "biquini", "conjunto feminino", "maquiagem"]):
        categorias_encontradas.append("MODA_FEMININA")
    if any(k in texto_lower for k in ["masculina", "bermuda", "calca jeans", "camisa polo", "tenis masculino", "carteira masculina"]):
        categorias_encontradas.append("MODA_MASCULINA")

    return categorias_encontradas if categorias_encontradas else ["PROMONOMIA_OFERTAS"]

def classificar_oferta_gemini(texto_post):
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    if not GEMINI_API_KEY:
        return classificar_por_palavras_chave(texto_post)

    tentativas = 3
    for tentativa in range(1, tentativas + 1):
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"""
            Você é um classificador estrito de e-commerce. Sua função é ler a oferta e determinar a categoria ou categorias do produto principal.
            **Regras de Classificação:**
            1. Foque EXCLUSIVAMENTE no PRODUTO QUE ESTÁ SENDO VENDIDO.
            2. Categorias permitidas: BEBE_INFANTIL, AUTOMOTIVO, MODA_FEMININA, MODA_MASCULINA, ELETRONICOS, PROMONOMIA_OFERTAS.
            3. Se o produto se encaixar em mais de uma categoria, retorne todas separadas por vírgula (Exemplo: BEBE_INFANTIL, MODA_FEMININA). Caso contrário, retorne apenas uma.
            TEXTO DA OFERTA: "{texto_post}"
            Responda APENAS com as palavras-chave oficiais separadas por vírgula e nada mais:
            """
            response = client.chats.create(model="gemini-3.6-flash").send_message(prompt)
            resposta_texto = response.text.strip().upper().replace(".", "")

            candidatas = [c.strip() for c in resposta_texto.split(",")]
            cats_validas = [c for c in candidatas if c in PAGINAS_DESTINO]

            if cats_validas:
                print(f"🎯 Categorias identificadas pela IA: {cats_validas}")
                return cats_validas
        except Exception as e:
            print(f"⚠️ Tentativa {tentativa}/{tentativas} - Erro na IA Gemini: {e}")
            if tentativa < tentativas:
                time.sleep(2)

    print("⚠️ Falha na IA após 3 tentativas. Acionando fallback por palavras-chave...")
    return classificar_por_palavras_chave(texto_post)

def extrair_dados_do_texto_bruto(texto_bruto):
    if not texto_bruto: return "Produto", "0,00", ""
    link = ""
    match_link = re.search(r'(https?://\S+)', texto_bruto)
    if match_link: link = match_link.group(1)
    preco = "0,00"
    match_preco = re.search(r'R\$\s*([\d\.,]+)', texto_bruto, re.IGNORECASE)
    if match_preco: preco = match_preco.group(1)
    titulo = texto_bruto
    titulo = re.sub(r'Dê uma olhada em\s*', '', titulo, flags=re.IGNORECASE)
    if match_preco: titulo = re.sub(rf'por\s*R\$\s*{re.escape(preco)}.*', '', titulo, flags=re.IGNORECASE)
    if match_link: titulo = titulo.replace(link, '')
    titulo = titulo.replace("Compre na Shopee agora!", "").strip()
    titulo = re.sub(r'\s+', ' ', titulo).strip()
    return titulo if titulo else "Oferta Imperdível", preco, link

def obter_texto_anuncio(item):
    if item.get("formatado"):
        link = item.get("link") or ""
        return item.get("formatado"), link
    texto_base = item.get("titulo") or ""
    titulo, preco, link = extrair_dados_do_texto_bruto(texto_base)
    if item.get("titulo") and "Dê uma olhada" not in item.get("titulo"): titulo = item.get("titulo")
    if item.get("preco"): preco = item.get("preco")
    if item.get("link"): link = item.get("link")
    return f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{titulo}**\n\n✅ **Por:** R$ {preco}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {link}", link

def obter_fotos_lista(item):
    val = item.get("fotos") or item.get("imagem") or item.get("foto") or item.get("img")
    if not val: return []
    urls = []
    if isinstance(val, list):
        for p in val:
            if isinstance(p, str): urls.append(p)
            elif isinstance(p, dict):
                u = p.get("url") or p.get("link") or p.get("path") or p.get("fileUrl")
                if u: urls.append(u)
    elif isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                for p in parsed:
                    if isinstance(p, str): urls.append(p)
                    elif isinstance(p, dict):
                        u = p.get("url") or p.get("link")
                        if u: urls.append(u)
        except:
            urls.append(val)
    return urls

def processar_imagem(img_url):
    try:
        resp = requests.get(img_url, timeout=15)
        if resp.status_code != 200: return None
        img = Image.open(io.BytesIO(resp.content))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img_a = ImageOps.pad(img, (1200, 1200), color=(255, 255, 255))
        buf = io.BytesIO()
        img_a.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        return buf
    except:
        return None

def processar_video(video_url):
    try:
        if isinstance(video_url, bytes):
            return video_url

        if os.path.isfile(video_url):
            with open(video_url, "rb") as f:
                return f.read()

        resp = requests.get(video_url, timeout=120)
        if resp.status_code != 200:
            print(f"❌ Erro ao baixar vídeo: HTTP {resp.status_code}")
            return None

        return resp.content
    except Exception as e:
        print(f"❌ Erro ao baixar vídeo: {e}")
        return None


def criar_video_com_foto(video_url, fotos_urls):
    try:
        if not video_url or not fotos_urls:
            return None

        pasta_temp = tempfile.mkdtemp(prefix="video_foto_")
        video_original = os.path.join(pasta_temp, "video_original.mp4")
        fotos_originais = []

        print("⬇️ Baixando vídeo para montagem...")
        video_data = processar_video(video_url)

        if not video_data:
            print("❌ Não foi possível baixar o vídeo para montagem.")
            return None

        with open(video_original, "wb") as f:
            f.write(video_data)

        for i, foto_url in enumerate(fotos_urls, 1):
            print(f"⬇️ Baixando foto {i}/{len(fotos_urls)} para montagem...")
            foto_data = processar_imagem(foto_url)

            if not foto_data:
                print(f"⚠️ Não foi possível baixar a foto {i}. Pulando...")
                continue

            foto_original = os.path.join(
                pasta_temp,
                f"foto_{i}.jpg"
            )

            with open(foto_original, "wb") as f:
                f.write(foto_data.getvalue())

            fotos_originais.append(foto_original)

        if not fotos_originais:
            print("❌ Nenhuma foto pôde ser baixada para a montagem.")
            return None

        video_final = os.path.join(pasta_temp, "video_final.mp4")

        print(f"🎬 Montando vídeo + {len(fotos_originais)} foto(s)...")

        juntar_video_foto(
            video_original,
            fotos_originais,
            video_final
        )

        if not os.path.exists(video_final):
            print("❌ O vídeo combinado não foi criado.")
            return None

        print("✅ Vídeo combinado criado com sucesso.")

        with open(video_final, "rb") as f:
            return f.read()

    except Exception as e:
        print(f"❌ Erro ao criar vídeo combinado: {e}")
        return None

def enviar_telegram(texto, imagens_ref, video_ref=None):
    if not TELEGRAM_CANAL_TOKEN or not TELEGRAM_CANAL_ID: return False
    try:
        if video_ref:
            video_data = processar_video(video_ref)

            if video_data:
                url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendVideo"
                r = requests.post(
                    url,
                    data={
                        "chat_id": TELEGRAM_CANAL_ID,
                        "caption": texto,
                        "parse_mode": "Markdown"
                    },
                    files={
                        "video": ("video.mp4", video_data, "video/mp4")
                    },
                    timeout=180
                )

                resposta = r.json()

                if resposta.get("ok", False):
                    print("🎥 Vídeo enviado para o Telegram.")
                    return True

                print(f"❌ Erro Telegram vídeo: {r.text}")
                return False

            print("❌ Não foi possível baixar o vídeo.")
            return False

        if not imagens_ref:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMessage"
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'text': texto, 'parse_mode': 'Markdown'}, timeout=30)
            return r.json().get("ok", False)
        if isinstance(imagens_ref, str): imagens_ref = [imagens_ref]
        midia_processada, files_dict = [], {}
        for i, img_url in enumerate(imagens_ref):
            img_io = processar_imagem(img_url)
            if img_io:
                file_key = f"photo_{i}"
                files_dict[file_key] = ('foto.jpg', img_io.getvalue(), 'image/jpeg')
                item_midia = {"type": "photo", "media": f"attach://{file_key}"}
                if i == 0 and texto:
                    item_midia["caption"] = texto
                    item_midia["parse_mode"] = "Markdown"
                midia_processada.append(item_midia)
        if len(midia_processada) > 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMediaGroup"
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'media': json.dumps(midia_processada)}, files=files_dict, timeout=40)
            return r.json().get("ok", False)
        elif len(midia_processada) == 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendPhoto"
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'caption': texto, 'parse_mode': 'Markdown'}, files={'photo': files_dict['photo_0']}, timeout=30)
            return r.json().get("ok", False)
        return False
    except:
        return False

def enviar_facebook(texto, link, imagem_url=None, video_url=None, categoria="PROMONOMIA_OFERTAS"):
    cfg = PAGINAS_DESTINO.get(categoria, PAGINAS_DESTINO["PROMONOMIA_OFERTAS"])
    page_id = cfg["id"]
    access_token = cfg["token"]

    if not page_id or not access_token: return False
    try:
        legenda = texto.replace("**", "*")

        if video_url:
            video_data = processar_video(video_url)

            if video_data:
                url = f"https://graph.facebook.com/v19.0/{page_id}/videos"
                r = requests.post(
                    url,
                    data={
                        "description": legenda,
                        "access_token": access_token
                    },
                    files={
                        "source": ("video.mp4", video_data, "video/mp4")
                    },
                    timeout=180
                )

                resposta = r.json()

                if "id" in resposta:
                    print(f"🎥 [SUCESSO] Vídeo publicado na página: {categoria} (ID: {page_id})")
                    return True

                print(f"❌ Erro Facebook vídeo ({categoria}): {r.text}")
                return False

            return False

        if imagem_url:
            img_io = processar_imagem(imagem_url)
            if img_io:
                if link and link not in legenda: legenda += f"\n\n🔗 {link}"
                url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
                r = requests.post(url, data={'caption': legenda, 'access_token': access_token}, files={'source': ('foto.jpg', img_io.getvalue(), 'image/jpeg')}, timeout=40)
                sucesso = "id" in r.json() or "post_id" in r.json()
                if sucesso:
                    print(f"✅ [SUCESSO] Post publicado na página: {categoria} (ID: {page_id})")
                return sucesso
        url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
        r = requests.post(url, data={'message': legenda, 'link': link, 'access_token': access_token}, timeout=30)
        sucesso = "id" in r.json()
        if sucesso:
            print(f"✅ [SUCESSO] Post publicado na página: {categoria} (ID: {page_id})")
        return sucesso
    except Exception as e:
        print(f"❌ Erro ao postar no Facebook ({categoria}): {e}")
        return False

if __name__ == "__main__":
    INTERVALO_MINUTOS = 15

    print("🤖 Worker iniciado.")
    print(f"⏱️ Intervalo entre publicações: {INTERVALO_MINUTOS} minutos")

    try:
        rascunhos = carregar_rascunhos()

        if not rascunhos:
            print("📭 Fila de ofertas vazia. Encerrando execução.")
            exit(0)

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        url_controle = (
            f"{SUPABASE_URL.rsplit('/ofertas', 1)[0]}"
            "/rest/v1/rpc/tentar_reservar_publicacao"
        )

        resposta_reserva = requests.post(
            url_controle,
            headers=headers,
            json={},
            timeout=20
        )

        if resposta_reserva.status_code != 200:
            print(
                f"❌ Erro ao verificar intervalo de publicação: "
                f"{resposta_reserva.status_code} - {resposta_reserva.text}"
            )
            exit(1)

        pode_publicar = resposta_reserva.json()

        if not pode_publicar:
            print(
                "⏳ Ainda não passaram 15 minutos desde a última "
                "reserva/publicação. Encerrando execução."
            )
            exit(0)

        proxima = rascunhos[0]

        texto_bruto_oferta = (
            proxima.get("titulo")
            or proxima.get("formatado")
            or ""
        )

        categorias_detectadas = classificar_oferta_gemini(
            texto_bruto_oferta
        )

        texto, link = obter_texto_anuncio(proxima)

        fotos = obter_fotos_lista(proxima)
        foto_principal = fotos[0] if fotos else None

        video = proxima.get("video")

        video_para_publicar = video

        if video and fotos:
            print(
                f"🎬 Vídeo + {len(fotos)} foto(s) detectados. "
                "Criando vídeo combinado..."
            )

            video_combinado = criar_video_com_foto(video, fotos)

            if video_combinado:
                video_para_publicar = video_combinado
            else:
                print("⚠️ Montagem falhou. Usando vídeo original.")

        print(
            f"🚀 Publicando oferta: "
            f"{texto_bruto_oferta[:60]}..."
        )

        ok_tg = enviar_telegram(
            texto,
            fotos,
            video_ref=video_para_publicar
        )

        paginas_alvo = set(
            ["PROMONOMIA_OFERTAS"] + categorias_detectadas
        )

        sucesso_geral = False

        for cat in paginas_alvo:
            ok_fb = enviar_facebook(
                texto,
                link,
                foto_principal,
                video_url=video_para_publicar,
                categoria=cat
            )

            if ok_fb:
                sucesso_geral = True

        if ok_tg or sucesso_geral:
            remover_rascunho(proxima["id"])

            print(
                "✅ Oferta processada, publicada e removida "
                "da fila com sucesso!"
            )

        else:
            print(
                "❌ Falha ao publicar oferta. "
                "A oferta permanece na fila para nova tentativa."
            )

    except KeyboardInterrupt:
        print("\n🛑 Worker encerrado.")

    except Exception as e:
        print(f"❌ Erro no worker: {e}")
        exit(1)
