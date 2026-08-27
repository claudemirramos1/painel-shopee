import os
import json
import time
import io
import urllib.parse
import requests
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURAÇÕES E CREDENCIAIS
# ==========================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://ftumdeqziwyljmaehaqk.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_publishable_8qfsBhW22Sx25mvPcxWNvw_4teJRbfu")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FACEBOOK_PAGE_ID = st.secrets.get("FACEBOOK_PAGE_ID", "1214303865109377")
FACEBOOK_ACCESS_TOKEN = st.secrets.get("FACEBOOK_ACCESS_TOKEN", "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst")
TELEGRAM_CANAL_TOKEN = st.secrets.get("TELEGRAM_CANAL_TOKEN", "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04")
TELEGRAM_CANAL_ID = st.secrets.get("TELEGRAM_CANAL_ID", "-1004406728710")

st.set_page_config(page_title="Gestão de Ofertas - FB & Telegram", page_icon="📢", layout="wide")

# ==========================================
# 2. FUNÇÕES DE SUPABASE E PROCESSAMENTO
# ==========================================
def carregar_rascunhos():
    try:
        res = supabase.table("ofertas").select("*").order("created_at", desc=False).execute()
        return res.data
    except Exception:
        return []

def remover_rascunho(rascunho_id):
    try:
        supabase.table("ofertas").delete().eq("id", rascunho_id).execute()
    except Exception as e:
        st.error(f"Erro ao remover: {e}")

def obter_texto_anuncio(item):
    """Pega o texto formatado salvo pelo bot do WhatsApp ou monta se faltar"""
    # Se a coluna 'formatado' já tem o texto pronto do bot, usa ele direto!
    if item.get("formatado"):
        return item.get("formatado")
    
    # Se não tiver, monta utilizando o padrão rigoroso com os dados disponíveis
    t_item = item.get('titulo') or item.get('title') or "Oferta Imperdível"
    p_item = item.get('preco') or item.get('price') or "Consulte"
    l_item = item.get('link') or item.get('url') or ""
    
    return f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{t_item}**\n\n✅ **Por:** R$ {p_item}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {l_item}"

def obter_link_afiliado(item):
    return item.get('link') or item.get('url') or ""

def obter_foto_item(item):
    """Extrai a URL da foto considerando a coluna 'fotos' (tipo jsonb ou texto)"""
    val = item.get("fotos") or item.get("imagem") or item.get("foto") or item.get("img")
    
    if not val:
        return None
    
    if isinstance(val, list) and len(val) > 0:
        primeiro = val[0]
        if isinstance(primeiro, str):
            return primeiro
        elif isinstance(primeiro, dict):
            return primeiro.get("url") or primeiro.get("link") or primeiro.get("path")
            
    if isinstance(val, dict):
        return val.get("url") or val.get("link") or val.get("path")
        
    if isinstance(val, str):
        if val.startswith("[") or val.startswith("{"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list) and len(parsed) > 0:
                    if isinstance(parsed[0], str): return parsed[0]
                    if isinstance(parsed[0], dict): return parsed[0].get("url") or parsed[0].get("link")
                elif isinstance(parsed, dict):
                    return parsed.get("url") or parsed.get("link")
            except:
                pass
        return val
        
    return None

def processar_imagem(img_upload):
    try:
        if isinstance(img_upload, str):
            resp = requests.get(img_upload, timeout=15)
            if resp.status_code != 200: return None
            img = Image.open(io.BytesIO(resp.content))
        else:
            img_upload.seek(0)
            img = Image.open(io.BytesIO(img_upload.getvalue()))

        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
        
        img_a = ImageOps.pad(img, (1200, 1200), color=(255, 255, 255))
        buf = io.BytesIO()
        img_a.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        buf.name = "foto_oferta.jpg"
        return buf
    except Exception:
        return None

# ==========================================
# 3. FUNÇÕES DE DISPARO (FB & TG)
# ==========================================
def enviar_telegram_com_foto(texto, imagem_ref):
    try:
        img_io = processar_imagem(imagem_ref)
        if img_io:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendPhoto"
            files = {'photo': ('foto.jpg', img_io.getvalue(), 'image/jpeg')}
            data = {'chat_id': TELEGRAM_CANAL_ID, 'caption': texto, 'parse_mode': 'Markdown'}
            r = requests.post(url, data=data, files=files, timeout=30)
            res_json = r.json()
            return res_json.get("ok", False), r.text
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMessage"
            data = {'chat_id': TELEGRAM_CANAL_ID, 'text': texto, 'parse_mode': 'Markdown'}
            r = requests.post(url, data=data, timeout=15)
            res_json = r.json()
            return res_json.get("ok", False), r.text
    except Exception as e:
        return False, str(e)

def enviar_facebook_com_foto(texto, link, imagem_ref):
    try:
        img_io = processar_imagem(imagem_ref)
        legenda = texto.replace("**", "*")
        if link and link not in legenda:
            legenda += f"\n\n🔗 {link}"

        if img_io:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            files = {'source': ('foto.jpg', img_io.getvalue(), 'image/jpeg')}
            data = {'caption': legenda, 'access_token': FACEBOOK_ACCESS_TOKEN}
            r = requests.post(url, data=data, files=files, timeout=40)
            res_json = r.json()
            sucesso = "id" in res_json or "post_id" in res_json
            return sucesso, r.text
        else:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
            data = {'message': legenda, 'access_token': FACEBOOK_ACCESS_TOKEN, 'link': link or ""}
            r = requests.post(url, data=data, timeout=20)
            res_json = r.json()
            sucesso = "id" in res_json or "post_id" in res_json
            return sucesso, r.text
    except Exception as e:
        return False, str(e)

def disparar_redes_completo(texto_formatado, link, imagem_ref, enviar_fb=True, enviar_tg=True):
    ok_tg, err_tg = True, "Não selecionado"
    ok_fb, err_fb = True, "Não selecionado"

    if enviar_tg:
        ok_tg, err_tg = enviar_telegram_com_foto(texto_formatado, imagem_ref)
    if enviar_fb:
        ok_fb, err_fb = enviar_facebook_com_foto(texto_formatado, link, imagem_ref)
    
    sucesso_geral = (ok_tg if enviar_tg else True) and (ok_fb if enviar_fb else True)
    logs = f"TG: {err_tg} | FB: {err_fb}"
    return sucesso_geral, logs

# ==========================================
# 4. INTERFACE PRINCIPAL (STREAMLIT)
# ==========================================
st.title("📢 Painel de Gestão e Disparo de Ofertas")

aba_manual, aba_fila, aba_auto = st.tabs([
    "✍️ Postagem Manual", 
    "📥 Fila de Rascunhos", 
    "🤖 Piloto Automático"
])

if "val_titulo" not in st.session_state: st.session_state.val_titulo = ""
if "val_preco" not in st.session_state: st.session_state.val_preco = ""
if "val_link" not in st.session_state: st.session_state.val_link = ""

# --- ABA 1: MANUAL ---
with aba_manual:
    st.subheader("Postagem Manual para Redes Sociais")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        titulo = st.text_input("Título do Produto", value=st.session_state.val_titulo, key="input_titulo")
        preco = st.text_input("Preço Promocional (R$)", value=st.session_state.val_preco, key="input_preco")
        link = st.text_input("Link de Afiliado", value=st.session_state.val_link, key="input_link")
    
    with col_m2:
        st.markdown("**Canais de Envio:**")
        manual_fb = st.checkbox("Publicar no Facebook", value=True, key="m_fb")
        manual_tg = st.checkbox("Publicar no Telegram", value=True, key="m_tg")

    foto_manual = st.file_uploader("📸 Foto do Produto", type=["jpg", "png", "webp"])

    texto_preview = f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{titulo}**\n\n✅ **Por:** R$ {preco}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {link}"
    
    st.markdown("**Pré-visualização do Anúncio:**")
    st.info(texto_preview)

    if st.button("🚀 Disparar Postagem Manual", type="primary"):
        if not foto_manual:
            st.warning("⚠️ O envio manual exige uma foto anexada!")
        elif not (manual_fb or manual_tg):
            st.warning("⚠️ Selecione pelo menos uma rede social para enviar!")
        else:
            with st.spinner("Enviando..."):
                ok, log = disparar_redes_completo(texto_preview, link, foto_manual, manual_fb, manual_tg)
                if ok:
                    st.success("✅ Oferta postada com sucesso!")
                else:
                    st.error(f"❌ Erro no disparo: {log}")

# --- ABA 2: FILA DE RASCUNHOS ---
with aba_fila:
    st.subheader("Fila de Ofertas Capturadas pelo Bot")
    rascunhos = carregar_rascunhos()

    if not rascunhos:
        st.info("Nenhuma oferta pendente no momento.")
    else:
        st.write(f"Total na fila: **{len(rascunhos)}** oferta(s)")
        
        col_opt1, col_opt2 = st.columns(2)
        fila_fb = col_opt1.checkbox("Enviar para Facebook na Fila", value=True, key="f_fb_global")
        fila_tg = col_opt2.checkbox("Enviar para Telegram na Fila", value=True, key="f_tg_global")

        for item in rascunhos:
            foto_item_url = obter_foto_item(item)
            texto_item = obter_texto_anuncio(item)
            link_item = obter_link_afiliado(item)
            tem_foto_status = "🖼️ Com Foto" if foto_item_url else "⚠️ Sem Foto"
            
            with st.expander(f"📦 {item.get('titulo') or 'Oferta'} - R$ {item.get('preco')} | {tem_foto_status}", expanded=False):
                if foto_item_url:
                    st.image(foto_item_url, width=150)
                
                st.text_area("Texto Formatado:", value=texto_item, height=120, key=f"txt_{item['id']}")

                col_b1, col_b2, col_b3 = st.columns(3)
                
                if col_b1.button("📋 Carregar no Form Manual", key=f"load_{item['id']}"):
                    st.session_state.val_titulo = item.get('titulo', '')
                    st.session_state.val_preco = item.get('preco', '')
                    st.session_state.val_link = link_item
                    st.success("✅ Dados carregados na aba 'Postagem Manual'! Vá até lá.")
                    st.rerun()

                if col_b2.button("🚀 Enviar Agora", key=f"send_{item['id']}"):
                    ok, log = disparar_redes_completo(texto_item, link_item, foto_item_url, fila_fb, fila_tg)
                    if ok:
                        remover_rascunho(item["id"])
                        st.success("Publicado e removido da fila!")
                        st.rerun()
                    else:
                        st.error(f"Erro: {log}")

                if col_b3.button("🗑️ Descartar", key=f"del_{item['id']}"):
                    remover_rascunho(item["id"])
                    st.rerun()

# --- ABA 3: PILOTO AUTOMÁTICO ---
with aba_auto:
    st.subheader("⚙️ Configuração do Disparo Automático em Fila")

    if "auto_rodando" not in st.session_state:
        st.session_state.auto_rodando = False

    intervalo_minutos = st.number_input(
        "Intervalo entre postagens (em minutos):", 
        min_value=1, 
        max_value=180, 
        value=15
    )

    col_p1, col_p2 = st.columns(2)
    if col_p1.button("▶️ Ligar Piloto Automático", type="primary"):
        st.session_state.auto_rodando = True

    if col_p2.button("⏸️ Pausar Piloto Automático"):
        st.session_state.auto_rodando = False

    if st.session_state.auto_rodando:
        st.success(f"🟢 **PILOTO AUTOMÁTICO ATIVO** — Intervalo: {intervalo_minutos} min.")
    else:
        st.warning("🔴 **PILOTO AUTOMÁTICO PAUSADO**")

    if st.session_state.auto_rodando:
        rascunhos = carregar_rascunhos()
        
        if not rascunhos:
            st.info("Aguardando novas ofertas entrarem na fila...")
            time.sleep(10)
            st.rerun()
        else:
            proxima = rascunhos[0] 
            texto_auto = obter_texto_anuncio(proxima)
            link_auto = obter_link_afiliado(proxima)
            foto_prox = obter_foto_item(proxima)

            st.info(f"⏳ Processando oferta da fila...")

            if not foto_prox:
                st.warning("⚠️ Oferta ignorada pelo piloto automático: Item sem foto na base. Removendo da fila...")
                remover_rascunho(proxima["id"])
                time.sleep(3)
                st.rerun()

            ok, log = disparar_redes_completo(texto_auto, link_auto, foto_prox, enviar_fb=True, enviar_tg=True)
            if ok:
                remover_rascunho(proxima["id"])
                st.success(f"✅ Oferta publicada! Próximo disparo em {intervalo_minutos} minuto(s)...")
                time.sleep(intervalo_minutos * 60)
                st.rerun()
            else:
                st.error(f"Erro na publicação automática: {log}. Tentando novamente em 30s...")
                time.sleep(30)
                st.rerun()
