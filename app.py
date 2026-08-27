cat << 'EOF' > ~/painel-shopee/app.py
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

def processar_imagem(img_upload):
    try:
        if isinstance(img_upload, str):
            # Se for URL vinda da fila/Supabase
            resp = requests.get(img_upload, timeout=10)
            if resp.status_code != 200: return None
            img = Image.open(io.BytesIO(resp.content))
        else:
            # Se for upload manual do Streamlit
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
# 3. FUNÇÕES DE DISPARO COM FOTO (FB & TG)
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
            # Fallback caso dê erro na imagem: envia só texto
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
        legenda = texto.replace("**", "*") # Ajuste de negrito para o FB
        if link:
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

def disparar_redes_completo(texto_formatado, link, imagem_ref):
    # Envio obrigatório para Telegram e Facebook juntos
    ok_tg, err_tg = enviar_telegram_com_foto(texto_formatado, imagem_ref)
    ok_fb, err_fb = enviar_facebook_com_foto(texto_formatado, link, imagem_ref)
    
    sucesso_geral = ok_tg and ok_fb
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

# --- ABA 1: MANUAL ---
with aba_manual:
    st.subheader("Postagem Manual para Redes Sociais")
    
    tit_def = st.session_state.get("tp", "")
    prc_def = st.session_state.get("ppor", "")
    lnk_def = st.session_state.get("lp", "")

    titulo = st.text_input("Título do Produto", value=tit_def)
    preco = st.text_input("Preço Promocional (R$)", value=prc_def)
    link = st.text_input("Link de Afiliado", value=lnk_def)
    foto_manual = st.file_uploader("📸 Foto do Produto", type=["jpg", "png", "webp"])

    texto_preview = f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{titulo}**\n\n✅ **Por:** R$ {preco}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {link}"
    
    st.markdown("**Pré-visualização do Anúncio:**")
    st.info(texto_preview)

    if st.button("🚀 Disparar Postagem Manual (FB + Telegram)", type="primary"):
        if not foto_manual:
            st.warning("⚠️ O envio manual exige uma foto anexada!")
        else:
            with st.spinner("Enviando para o Telegram e Facebook..."):
                ok, log = disparar_redes_completo(texto_preview, link, foto_manual)
                if ok:
                    st.success("✅ Oferta postada com sucesso em ambas as redes!")
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
        for item in rascunhos:
            with st.expander(f"📦 {item.get('titulo') or 'Oferta sem Título'} - R$ {item.get('preco')}", expanded=False):
                st.markdown(f"**Link:** {item.get('link')}")
                
                # Reconstrói o texto no padrão rigoroso solicitado
                t_item = item.get('titulo', '')
                p_item = item.get('preco', '')
                l_item = item.get('link', '')
                texto_padrao = f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{t_item}**\n\n✅ **Por:** R$ {p_item}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {l_item}"
                
                st.text_area("Texto Formatado:", value=texto_padrao, height=100, key=f"txt_{item['id']}")

                col_b1, col_b2, col_b3 = st.columns(3)
                
                if col_b1.button("📋 Carregar no Form Manual", key=f"load_{item['id']}"):
                    st.session_state["tp"] = t_item
                    st.session_state["ppor"] = p_item
                    st.session_state["lp"] = l_item
                    st.success("Dados copiados para a aba 'Postagem Manual'!")

                if col_b2.button("🚀 Enviar Agora (FB + TG)", key=f"send_{item['id']}"):
                    foto_url = item.get("imagem") or item.get("foto") or item.get("img")
                    ok, log = disparar_redes_completo(texto_padrao, l_item, foto_url)
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
            t_prox = proxima.get('titulo', '')
            p_prox = proxima.get('preco', '')
            l_prox = proxima.get('link', '')
            foto_prox = proxima.get("imagem") or proxima.get("foto") or proxima.get("img")

            texto_auto = f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{t_prox}**\n\n✅ **Por:** R$ {p_prox}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {l_prox}"

            st.info(f"⏳ Processando oferta: **{t_prox}**")

            if not foto_prox:
                st.warning("⚠️ Oferta ignorada pelo piloto automático: Item sem foto na base. Removendo da fila...")
                remover_rascunho(proxima["id"])
                time.sleep(3)
                st.rerun()

            ok, log = disparar_redes_completo(texto_auto, l_prox, foto_prox)
            if ok:
                remover_rascunho(proxima["id"])
                st.success(f"✅ Oferta publicada no Facebook e Telegram! Próximo disparo em {intervalo_minutos} minuto(s)...")
                time.sleep(intervalo_minutos * 60)
                st.rerun()
            else:
                st.error(f"Erro na publicação automática: {log}. Tentando novamente em 30s...")
                time.sleep(30)
                st.rerun()
EOF
