import os
import json
import time
import requests
import streamlit as st
from supabase import create_client, Client

# ==========================================
# 1. CONFIGURAÇÕES E SUPABASE
# ==========================================
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://ftumdeqziwyljmaehaqk.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_publishable_8qfsBhW22Sx25mvPcxWNvw_4teJRbfu")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FACEBOOK_PAGE_ID = st.secrets.get("FACEBOOK_PAGE_ID", "SUA_PAGE_ID_AQUI")
FACEBOOK_ACCESS_TOKEN = st.secrets.get("FACEBOOK_ACCESS_TOKEN", "SEU_FB_TOKEN_AQUI")
TELEGRAM_CANAL_TOKEN = st.secrets.get("TELEGRAM_CANAL_TOKEN", "8997755956:AAGW29WiWbZCpfoTGh-6m-a1qdYnfze5e_k")
TELEGRAM_CANAL_ID = st.secrets.get("TELEGRAM_CANAL_ID", "-100XXXXXXXXXX")

st.set_page_config(page_title="Gestão de Ofertas - FB & Telegram", page_icon="📢", layout="wide")

# ==========================================
# 2. FUNÇÕES DE BANCO DE DADOS (SUPABASE)
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

# ==========================================
# 3. FUNÇÕES DE DISPARO (FACEBOOK E TELEGRAM)
# ==========================================
def enviar_para_telegram_oficial(texto):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CANAL_ID, 'text': texto, 'parse_mode': 'Markdown'}
        r = requests.post(url, data=payload)
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

def enviar_para_facebook(texto):
    try:
        url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
        payload = {'message': texto, 'access_token': FACEBOOK_ACCESS_TOKEN}
        r = requests.post(url, data=payload)
        return r.status_code in [200, 201], r.text
    except Exception as e:
        return False, str(e)

def disparar_redes(texto_formatado, enviar_fb=True, enviar_tg=True):
    res_tg, res_fb = True, True
    err_tg, err_fb = "", ""
    if enviar_tg:
        res_tg, err_tg = enviar_para_telegram_oficial(texto_formatado)
    if enviar_fb:
        res_fb, err_fb = enviar_para_facebook(texto_formatado)
    return res_tg and res_fb, f"TG: {err_tg} | FB: {err_fb}"

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

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        titulo = st.text_input("Título do Produto", value=tit_def)
        preco = st.text_input("Preço Promocional (R$)", value=prc_def)
        link = st.text_input("Link de Afiliado", value=lnk_def)
    
    with col_m2:
        dest_fb = st.checkbox("Publicar no Facebook", value=True)
        dest_tg = st.checkbox("Publicar no Telegram Oficial", value=True)

    texto_preview = f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{titulo}**\n\n✅ **Por:** R$ {preco}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {link}"
    st.markdown("**Pré-visualização da Legenda:**")
    st.info(texto_preview)

    if st.button("🚀 Disparar Postagem Manual", type="primary"):
        ok, log = disparar_redes(texto_preview, dest_fb, dest_tg)
        if ok:
            st.success("✅ Oferta enviada com sucesso!")
        else:
            st.error(f"❌ Erro ao enviar: {log}")

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
                st.text_area("Texto Formatado:", value=item.get('formatado', ''), height=100, key=f"txt_{item['id']}")

                col_b1, col_b2, col_b3 = st.columns(3)
                
                if col_b1.button("📋 Carregar no Form Manual", key=f"load_{item['id']}"):
                    st.session_state["tp"] = item.get("titulo", "")
                    st.session_state["ppor"] = item.get("preco", "")
                    st.session_state["lp"] = item.get("link", "")
                    st.success("Dados copiados para a aba 'Postagem Manual'!")

                if col_b2.button("🚀 Enviar Agora (FB + TG)", key=f"send_{item['id']}"):
                    ok, log = disparar_redes(item.get("formatado"))
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
            st.info(f"⏳ Processando oferta: **{proxima.get('titulo')}**")

            ok, log = disparar_redes(proxima.get("formatado"))
            if ok:
                remover_rascunho(proxima["id"])
                st.success(f"✅ Oferta publicada! Próximo disparo em {intervalo_minutos} minuto(s)...")
                time.sleep(intervalo_minutos * 60)
                st.rerun()
            else:
                st.error(f"Erro na publicação automática: {log}. Tentando novamente em 30s...")
                time.sleep(30)
                st.rerun()
