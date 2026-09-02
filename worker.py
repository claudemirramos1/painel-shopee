import os
import json
import io
import re
import requests
from PIL import Image, ImageOps

SUPABASE_URL = "https://ftumdeqziwyljmaehaqk.supabase.co"
SUPABASE_KEY = "sb_publishable_8qfsBhW22Sx25mvPcxWNvw_4teJRbfu"

FACEBOOK_PAGE_ID = "1214303865109377"
FACEBOOK_ACCESS_TOKEN = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"
TELEGRAM_CANAL_TOKEN = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TELEGRAM_CANAL_ID = "-1004406728710"

print("🤖 Iniciando Worker Inteligente (Execução Única)...")

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

def enviar_telegram(texto, imagens_ref):
    if not TELEGRAM_CANAL_TOKEN or not TELEGRAM_CANAL_ID: return False
    try:
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

def enviar_facebook(texto, link, imagem_url=None):
    if not FACEBOOK_PAGE_ID or not FACEBOOK_ACCESS_TOKEN: return False
    try:
        legenda = texto.replace("**", "*")
        if imagem_url:
            img_io = processar_imagem(imagem_url)
            if img_io:
                if link and link not in legenda: legenda += f"\n\n🔗 {link}"
                url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
                r = requests.post(url, data={'caption': legenda, 'access_token': FACEBOOK_ACCESS_TOKEN}, files={'source': ('foto.jpg', img_io.getvalue(), 'image/jpeg')}, timeout=40)
                return "id" in r.json() or "post_id" in r.json()
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        r = requests.post(url, data={'message': legenda, 'link': link, 'access_token': FACEBOOK_ACCESS_TOKEN}, timeout=30)
        return "id" in r.json()
    except:
        return False

# Execução única
rascunhos = carregar_rascunhos()
if rascunhos:
    proxima = rascunhos[0]
    texto, link = obter_texto_anuncio(proxima)
    fotos = obter_fotos_lista(proxima)
    foto_principal = fotos[0] if fotos else None

    print(f"🚀 Publicando oferta: {proxima.get('titulo')}")
    ok_tg = enviar_telegram(texto, fotos)
    ok_fb = enviar_facebook(texto, link, foto_principal)

    if ok_tg or ok_fb:
        remover_rascunho(proxima["id"])
        print("✅ Oferta publicada e removida com sucesso!")
    else:
        print("❌ Falha ao publicar oferta.")
else:
    print("📭 Fila de ofertas vazia.")
