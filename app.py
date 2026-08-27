import os
import json
import time
import io
import re
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

# Inicialização segura do session_state para os inputs manuais
if "input_titulo" not in st.session_state: st.session_state.input_titulo = ""
if "input_preco" not in st.session_state: st.session_state.input_preco = "0,00"
if "input_link" not in st.session_state: st.session_state.input_link = ""

# ==========================================
# 2. FUNÇÕES DE SUPABASE E PROCESSAMENTO INTELIGENTE
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

def extrair_dados_do_texto_bruto(texto_bruto):
    """Lê o texto livre vindo do Telegram e extrai título, preço e link automaticamente"""
    if not texto_bruto:
        return "Produto", "0,00", ""
    
    link = ""
    match_link = re.search(r'(https?://\S+)', texto_bruto)
    if match_link:
        link = match_link.group(1)

    preco = "0,00"
    match_preco = re.search(r'R\$\s*([\d\.,]+)', texto_bruto, re.IGNORECASE)
    if match_preco:
        preco = match_preco.group(1)

    titulo = texto_bruto
    titulo = re.sub(r'Dê uma olhada em\s*', '', titulo, flags=re.IGNORECASE)
    if match_preco:
        titulo = re.sub(rf'por\s*R\$\s*{re.escape(preco)}.*', '', titulo, flags=re.IGNORECASE)
    if match_link:
        titulo = titulo.replace(link, '')
    titulo = titulo.replace("Compre na Shopee agora!", "").strip()
    titulo = re.sub(r'\s+', ' ', titulo).strip()
    
    if not titulo:
        titulo = "Oferta Imperdível"

    return titulo, preco, link

def obter_texto_anuncio(item):
    """Gera o texto rigorosamente formatado no padrão desejado"""
    texto_base = item.get("formatado") or item.get("titulo") or ""
    titulo, preco, link = extrair_dados_do_texto_bruto(texto_base)
    
    if item.get("titulo") and "Dê uma olhada" not in item.get("titulo"):
        titulo = item.get("titulo")
    if item.get("preco"):
        preco = item.get("preco")
    if item.get("link"):
        link = item.get("link")

    return f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{titulo}**\n\n✅ **Por:** R$ {preco}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {link}", link

def obter_fotos_lista(item):
    """Retorna uma lista limpa com todas as URLs de fotos disponíveis no item"""
    val = item.get("fotos") or item.get("imagem") or item.get("foto") or item.get("img")
    if not val:
        return []
    
    urls = []
    if isinstance(val, list):
        for primeiro in val:
            if isinstance(primeiro, str):
                urls.append(primeiro)
            elif isinstance(primeiro, dict):
                u = primeiro.get("url") or primeiro.get("link") or primeiro.get("path") or primeiro.get("fileUrl")
                if u: urls.append(u)
    elif isinstance(val, str):
        if val.startswith("[") or val.startswith("{"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    for p in parsed:
                        if isinstance(p, str): urls.append(p)
                        elif isinstance(p, dict):
                            u = p.get("url") or p.get("link")
                            if u: urls.append(u)
                elif isinstance(parsed, dict):
                    u = parsed.get("url") or parsed.get("link")
                    if u: urls.append(u)
            except:
                pass
        else:
            urls.append(val)
    return urls

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
def enviar_telegram_com_foto(texto, imagens_ref):
    """Envia uma ou várias fotos como álbum (media group) para o Telegram"""
    try:
        if isinstance(imagens_ref, (str, io.BytesIO)):
            imagens_ref = [imagens_ref]
        elif not isinstance(imagens_ref, list):
            imagens_ref = [imagens_ref]

        midia_processada = []
        files_dict = {}

        for i, img_ref in enumerate(imagens_ref):
            img_io = processar_imagem(img_ref)
            if img_io:
                file_key = f"photo_{i}"
                files_dict[file_key] = ('foto.jpg', img_io.getvalue(), 'image/jpeg')
                
                item_midia = {
                    "type": "photo",
                    "media": f"attach://{file_key}"
                }
                if i == 0 and texto:
                    item_midia["caption"] = texto
                    item_midia["parse_mode"] = "Markdown"
                
                midia_processada.append(item_midia)

        if len(midia_processada) > 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMediaGroup"
            data = {
                'chat_id': TELEGRAM_CANAL_ID,
                'media': json.dumps(midia_processada)
            }
            r = requests.post(url, data=data, files=files_dict, timeout=40)
            res_json = r.json()
            return res_json.get("ok", False), r.text

        elif len(midia_processada) == 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendPhoto"
            file_key = list(files_dict.keys())[0]
            files = {'photo': files_dict[file_key]}
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
        # Pega a primeira foto caso seja uma lista (o Facebook postará a principal)
        img_alvo = imagem_ref[0] if isinstance(imagem_ref, list) and len(imagem_ref) > 0 else imagem_ref
        
        img_io = processar_imagem(img_alvo)
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

# --- ABA 1: MANUAL ---
with aba_manual:
    st.subheader("Postagem Manual para Redes Sociais")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        titulo = st.text_input("Título do Produto", key="input_titulo")
        preco = st.text_input("Preço Promocional (R$)", key="input_preco")
        link = st.text_input("Link de Afiliado", key="input_link")
    
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
            fotos_item_lista = obter_fotos_lista(item)
            texto_item, link_item = obter_texto_anuncio(item)
            tem_foto_status = f"🖼️ {len(fotos_item_lista)} Foto(s)" if fotos_item_lista else "⚠️ Sem Foto"
            
            with st.expander(f"📦 {item.get('titulo') or 'Oferta'} | {tem_foto_status}", expanded=False):
                if fotos_item_lista:
                    cols_imgs = st.columns(min(len(fotos_item_lista), 4))
                    for idx, img_url in enumerate(fotos_item_lista):
                        with cols_imgs[idx % len(cols_imgs)]:
                            st.image(img_url, width=120)
                
                st.text_area("Texto Formatado:", value=texto_item, height=130, key=f"txt_{item['id']}")

                col_b1, col_b2, col_b3 = st.columns(3)
                
                if col_b1.button("📋 Carregar no Form Manual", key=f"load_{item['id']}"):
                    t_ext, p_ext, l_ext = extrair_dados_do_texto_bruto(item.get("formatado") or item.get("titulo") or "")
                    
                    st.session_state.input_titulo = item.get("titulo") or t_ext
                    st.session_state.input_preco = item.get("preco") or p_ext
                    st.session_state.input_link = item.get("link") or l_ext
                    
                    st.success("✅ Dados carregados na aba 'Postagem Manual'! Vá até lá.")
                    st.rerun()

                if col_b2.button("🚀 Enviar Agora", key=f"send_{item['id']}"):
                    # Envia a LISTA COMPLETA de fotos para o Telegram (criando o álbum)
                    ok, log = disparar_redes_completo(texto_item, link_item, fotos_item_lista, fila_fb, fila_tg)
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
            texto_auto, link_auto = obter_texto_anuncio(proxima)
            fotos_auto_lista = obter_fotos_lista(proxima)

            st.info(f"⏳ Processando oferta da fila...")

            if not fotos_auto_lista:
                st.warning("⚠️ Oferta ignorada pelo piloto automático: Item sem foto na base. Removendo da fila...")
                remover_rascunho(proxima["id"])
                time.sleep(3)
                st.rerun()

            # Envia a LISTA COMPLETA de fotos no piloto automático
            ok, log = disparar_redes_completo(texto_auto, link_auto, fotos_auto_lista, enviar_fb=True, enviar_tg=True)
            if ok:
                remover_rascunho(proxima["id"])
                st.success(f"✅ Oferta publicada! Próximo disparo em {intervalo_minutos} minuto(s)...")
                time.sleep(intervalo_minutos * 60)
                st.rerun()
            else:
                st.error(f"Erro na publicação automática: {log}. Tentando novamente em 30s...")
                time.sleep(30)
                st.rerun()
