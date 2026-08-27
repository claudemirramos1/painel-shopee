import os
import json
import time
import io
import re
import requests
from PIL import Image, ImageOps
from supabase import create_client, Client

# ==========================================
# CONFIGURAÇÕES E CREDENCIAIS SEGURAS
# ==========================================
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.environ.get("SUPABASE_KEY") or "").strip()

FACEBOOK_PAGE_ID = (os.environ.get("FACEBOOK_PAGE_ID") or "").strip()
FACEBOOK_ACCESS_TOKEN = (os.environ.get("FACEBOOK_ACCESS_TOKEN") or "").strip()
TELEGRAM_CANAL_TOKEN = (os.environ.get("TELEGRAM_CANAL_TOKEN") or "").strip()
TELEGRAM_CANAL_ID = (os.environ.get("TELEGRAM_CANAL_ID") or "").strip()

INTERVALO_MINUTOS = int((os.environ.get("INTERVALO_MINUTOS") or "15").strip())

print("🤖 Iniciando Worker de Piloto Automático...")

# Inicialização segura do cliente Supabase para evitar crash completo
supabase = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conectado ao Supabase com sucesso!")
    else:
        print("❌ ATENÇÃO: As chaves do Supabase não foram encontradas nas variáveis de ambiente.")
except Exception as e:
    print(f"⚠️ Erro ao criar cliente Supabase: {e}")

def carregar_rascunhos():
    if not supabase:
        return []
    try:
        res = supabase.table("ofertas").select("*").order("created_at", desc=False).execute()
        return res.data
    except Exception as e:
        print(f"⚠️ Erro ao buscar rascunhos: {e}")
        return []

def remover_rascunho(rascunho_id):
    if not supabase:
        return
    try:
        supabase.table("ofertas").delete().eq("id", rascunho_id).execute()
    except Exception as e:
        print(f"Erro ao remover rascunho: {e}")

def extrair_dados_do_texto_bruto(texto_bruto):
    if not texto_bruto:
        return "Produto", "0,00", ""
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
    texto_base = item.get("formatado") or item.get("titulo") or ""
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
    if not TELEGRAM_CANAL_TOKEN or not TELEGRAM_CANAL_ID:
        return False
    try:
        if isinstance(imagens_ref, str): imagens_ref = [imagens_ref]
        midia_processada = []
        files_dict = {}

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

def enviar_facebook(texto, link, imagem_url):
    if not FACEBOOK_PAGE_ID or not FACEBOOK_ACCESS_TOKEN:
        return False
    try:
        img_io = processar_imagem(imagem_url)
        legenda = texto.replace("**", "*")
        if link and link not in legenda: legenda += f"\n\n🔗 {link}"
        if img_io:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            r = requests.post(url, data={'caption': legenda, 'access_token': FACEBOOK_ACCESS_TOKEN}, files={'source': ('foto.jpg', img_io.getvalue(), 'image/jpeg')}, timeout=40)
            return "id" in r.json() or "post_id" in r.json()
        return False
    except:
        return False

# Loop principal seguro
while True:
    try:
        if not supabase:
            print("⏳ Aguardando conexão válida com o Supabase...")
            time.sleep(15)
            continue

        rascunhos = carregar_rascunhos()
        if rascunhos:
            proxima = rascunhos[0]
            texto, link = obter_texto_anuncio(proxima)
            fotos = obter_fotos_lista(proxima)

            if not fotos:
                print(f"⚠️ Oferta {proxima.get('id')} sem fotos. Removendo da fila.")
                remover_rascunho(proxima["id"])
                continue

            print(f"🚀 Publicando oferta: {proxima.get('titulo')}")
            ok_tg = enviar_telegram(texto, fotos)
            ok_fb = enviar_facebook(texto, link, fotos[0])

            if ok_tg or ok_fb:
                remover_rascunho(proxima["id"])
                print(f"✅ Publicado com sucesso! Aguardando {INTERVALO_MINUTOS} min para o próximo...")
            else:
                print("❌ Erro ao disparar nas redes. Tentando novamente em 1 minuto...")
                time.sleep(60)
                continue
        else:
            print("⏳ Fila vazia. Verificando novamente em 30 segundos...")
        
        time.sleep(INTERVALO_MINUTOS * 60)
    except Exception as e:
        print(f"⚠️ Erro no loop geral: {e}")
        time.sleep(30)
