import streamlit as st
import requests
import json
from gtts import gTTS
from PIL import Image, ImageOps, ImageEnhance
import io

# ==========================================
# 1. CONFIGURAÇÕES FIXAS (SEUS DADOS)
# ==========================================
FB_PAGE_ID_FIXO = "1214303865109377"
FB_PAGE_TOKEN_FIXO = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

TELEGRAM_BOT_TOKEN_FIXO = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TELEGRAM_CHAT_ID_FIXO = "-1004406728710"

# 📸 ID correto da sua Conta Comercial do Instagram integrado!
INSTAGRAM_USER_ID_FIXO = "e734c98074af31033728b42ab51dbe2b"  

# 🔑 Chave do ImgBB integrada
IMGBB_API_KEY_FIXO = "82c69b4736c7793eaab429880014d06c"  

# ==========================================
# 2. CONFIGURAÇÕES DA PÁGINA STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Painel de Ofertas & Redes Sociais",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas (Facebook, Telegram & Instagram)")
st.markdown("Publique ofertas com fotos tratadas em alta resolução (1080x1350) e automação completa.")

# ==========================================
# 3. FUNÇÕES DE SUPORTE (IMAGEM & IMGBB)
# ==========================================
def processar_imagem_automaticamente(imagem_upload, target_size=(1080, 1350)):
    try:
        img = Image.open(imagem_upload)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img_ajustada = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        
        enhancer_sharpness = ImageEnhance.Sharpness(img_ajustada)
        img_nitida = enhancer_sharpness.enhance(1.8)
        
        enhancer_contrast = ImageEnhance.Contrast(img_nitida)
        img_final = enhancer_contrast.enhance(1.15)
        
        output_buffer = io.BytesIO()
        img_final.save(output_buffer, format="JPEG", quality=95)
        output_buffer.seek(0)
        
        output_buffer.name = "oferta_otimizada_hd.jpg"
        output_buffer.type = "image/jpeg"
        return output_buffer
    except Exception as e:
        imagem_upload.seek(0)
        return imagem_upload

def subir_imagem_para_imgbb(img_buffer, api_key):
    """Envia a imagem tratada para o ImgBB e retorna uma URL pública permanente"""
    if not api_key:
        return None
    try:
        img_buffer.seek(0)
        url_api = "https://api.imgbb.com/1/upload"
        payload = {"key": api_key}
        files = {"image": ("oferta.jpg", img_buffer.getvalue(), "image/jpeg")}
        
        response = requests.post(url_api, data=payload, files=files, timeout=20)
        resultado = response.json()
        
        if resultado.get("success"):
            return resultado["data"]["url"]
        return None
    except Exception:
        return None

# ==========================================
# 4. FUNÇÕES DE POSTAGEM (REDES SOCIAIS)
# ==========================================

def postar_no_telegram(token, chat_id, texto, lista_imagens):
    if not token or not chat_id:
        return False, "Token ou Chat ID do Telegram não informados."
    try:
        imagens_processadas = [processar_imagem_automaticamente(img) for img in lista_imagens] if lista_imagens else []

        if not imagens_processadas or len(imagens_processadas) == 0:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
            response = requests.post(url, data=data, timeout=10)
            res_data = response.json()
            return (True, "Publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")
        
        elif len(imagens_processadas) == 1:
            img = imagens_processadas[0]
            img.seek(0)
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            files = {"photo": (img.name, img.getvalue(), img.type)}
            data = {"chat_id": chat_id, "caption": texto, "parse_mode": "HTML"}
            response = requests.post(url, data=data, files=files, timeout=20)
            res_data = response.json()
            return (True, "Publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")
        
        else:
            url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
            media = []
            files = {}
            for idx, img in enumerate(imagens_processadas):
                img.seek(0)
                file_key = f"photo_{idx}"
                files[file_key] = (img.name, img.getvalue(), img.type)
                item = {
                    "type": "photo",
                    "media": f"attach://{file_key}"
                }
                if idx == 0:
                    item["caption"] = texto
                    item["parse_mode"] = "HTML"
                media.append(item)
            
            data = {
                "chat_id": chat_id,
                "media": json.dumps(media)
            }
            response = requests.post(url, data=data, files=files, timeout=30)
            res_data = response.json()
            return (True, "Álbum publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")

    except Exception as e:
        return False, f"Falha no Telegram: {str(e)}"


def postar_no_facebook(page_id, page_token, texto_fb, lista_imagens, link_oferta=None):
    if not page_id or not page_token:
        return False, "ID da Página ou Token do FB não informados."
    try:
        legenda_limpa = texto_fb.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
        imagens_processadas = [processar_imagem_automaticamente(img) for img in lista_imagens] if lista_imagens else []
        
        if not imagens_processadas or len(imagens_processadas) == 0:
            url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            payload = {"message": legenda_limpa, "access_token": page_token}
            if link_oferta and link_oferta.strip():
                payload["link"] = link_oferta.strip()
            response = requests.post(url, data=payload, timeout=15)
            res_data = response.json()
            return (True, "Publicado no Facebook!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

        elif len(imagens_processadas) == 1:
            img = imagens_processadas[0]
            img.seek(0)
            url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
            files = {"source": (img.name, img.getvalue(), img.type)}
            payload = {"caption": legenda_limpa, "access_token": page_token}
            if link_oferta and link_oferta.strip():
                payload["link"] = link_oferta.strip()
            response = requests.post(url, data=payload, files=files, timeout=30)
            res_data = response.json()
            return (True, "Publicado no Facebook em HD!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

        else:
            attached_media_list = []
            for img in imagens_processadas:
                img.seek(0)
                url_upload = f"https://graph.facebook.com/v26.0/{page_id}/photos"
                files = {"source": (img.name, img.getvalue(), img.type)}
                payload_upload = {"published": "false", "access_token": page_token}
                resp_upload = requests.post(url_upload, data=payload_upload, files=files, timeout=30)
                data_upload = resp_upload.json()
                if "id" in data_upload:
                    attached_media_list.append({"media_fbid": data_upload["id"]})
                else:
                    return False, f"Erro ao enviar foto: {data_upload.get('error', {}).get('message', 'Erro')}"
            
            url_feed = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            payload_feed = {
                "message": legenda_limpa,
                "attached_media": json.dumps(attached_media_list),
                "access_token": page_token
            }
            if link_oferta and link_oferta.strip():
                payload_feed["link"] = link_oferta.strip()
                
            response = requests.post(url_feed, data=payload_feed, timeout=30)
            res_data = response.json()
            return (True, "Publicado no Facebook com múltiplas fotos!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

    except Exception as e:
        return False, f"Falha no Facebook: {str(e)}"


def postar_no_instagram(ig_user_id, page_token, texto_ig, lista_imagens, api_key_imgbb, link_oferta=None):
    if not ig_user_id or not page_token:
        return False, "ID da Conta do Instagram ou Token não configurados."
    if not lista_imagens:
        return False, "O Instagram exige ao menos uma imagem selecionada."
    if not api_key_imgbb:
        return False, "A chave de API do ImgBB não foi preenchida no código."
    
    try:
        img_processada = processar_imagem_automaticamente(lista_imagens[0])
        
        url_imagem_publica = subir_imagem_para_imgbb(img_processada, api_key_imgbb)
        if not url_imagem_publica:
            return False, "Falha ao gerar URL pública da imagem no ImgBB."

        legenda_limpa = texto_ig.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
        if link_oferta and link_oferta.strip():
            legenda_limpa += f"\n\nLink: {link_oferta.strip()}"

        url_container = f"https://graph.facebook.com/v26.0/{ig_user_id}/media"
        payload_container = {
            "image_url": url_imagem_publica,
            "caption": legenda_limpa,
            "access_token": page_token
        }
        resp_c = requests.post(url_container, data=payload_container, timeout=20)
        data_c = resp_c.json()

        if "id" in data_c:
            creation_id = data_c["id"]
            
            url_publish = f"https://graph.facebook.com/v26.0/{ig_user_id}/media_publish"
            payload_publish = {
                "creation_id": creation_id,
                "access_token": page_token
            }
            resp_p = requests.post(url_publish, data=payload_publish, timeout=20)
            data_p = resp_p.json()

            return (True, "Publicado no Instagram com sucesso!") if "id" in data_p else (False, f"Erro ao publicar: {data_p.get('error', {}).get('message', 'Erro')}")
        else:
            return False, f"Erro ao criar container: {data_c.get('error', {}).get('message', 'Erro')}"

    except Exception as e:
        return False, f"Falha no Instagram: {str(e)}"

# ==========================================
# 5. INTERFACE VISUAL (STREAMLIT)
# ==========================================

st.subheader("📝 Preencher Dados da Oferta")

col1, col2 = st.columns([1, 1])

with col1:
    titulo_produto = st.text_input("Título do Produto", placeholder="Ex: Smart TV 55\" 4K")
    preco_de = st.text_input("Preço De (R$)", placeholder="Ex: 1000")
    preco_por = st.text_input("Preço Por (R$)", placeholder="Ex: 800")
    cupom = st.text_input("Cupom de Desconto (Opcional)", placeholder="Ex: DESCONTO10")

with col2:
    link_afiliado = st.text_input("Link da Oferta / Afiliado", placeholder="https://...")
    
    imagens_upload = st.file_uploader(
        "📸 Selecionar Imagens da Galeria (Facebook, Telegram e Instagram)", 
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )
    
    if imagens_upload:
        st.write(f"📷 {len(imagens_upload)} imagem(ns) selecionada(s)")
        cols_img = st.columns(min(len(imagens_upload), 4))
        for idx, img in enumerate(imagens_upload):
            cols_img[idx % 4].image(img, use_container_width=True)

descricao_extra = st.text_area("Observações / Detalhes Adicionais (Opcional)", placeholder="Ex: Frete Grátis", height=70)

# Montagem do texto base
texto_gerado = f"🔥 <b>{titulo_produto if titulo_produto else 'OFERTA IMPERDÍVEL'}</b>\n\n"
if preco_de:
    texto_gerado += f"❌ De: R$ {preco_de}\n"
if preco_por:
    texto_gerado += f"✅ <b>Por: R$ {preco_por}</b>\n"
if cupom:
    texto_gerado += f"🎟️ Cupom: <code>{cupom}</code>\n"
if descricao_extra:
    texto_gerado += f"\nℹ️ {descricao_extra}\n"
if link_afiliado:
    texto_gerado += f"\n🛒 <b>Compre Aqui:</b> {link_afiliado}"

st.markdown("---")

tab_redes, tab_roteiro_locucao = st.tabs(["📢 Redes Sociais", "🎙️ Roteiro & Locução IA"])

with tab_redes:
    st.markdown("### 🎯 Selecione os Canais de Destino")
    col_check1, col_check2, col_check3 = st.columns(3)
    with col_check1:
        enviar_fb = st.checkbox("Facebook Page (HD)", value=True)
    with col_check2:
        enviar_tg = st.checkbox("Telegram (Álbum)", value=True)
    with col_check3:
        enviar_ig = st.checkbox("Instagram", value=True)

    st.markdown("---")
    if st.button("🚀 Postar Oferta nos Canais Selecionados", type="primary", use_container_width=True):
        if not titulo_produto and not link_afiliado:
            st.warning("Preencha ao menos o Título e o Link do produto antes de postar.")
        else:
            st.info("Processando publicações...")
            
            if enviar_fb:
                st_fb, msg_fb = postar_no_facebook(FB_PAGE_ID_FIXO, FB_PAGE_TOKEN_FIXO, texto_gerado, imagens_upload, link_afiliado)
                if st_fb:
                    st.success(f"✅ **Facebook:** {msg_fb}")
                else:
                    st.error(f"❌ **Facebook:** {msg_fb}")
                    
            if enviar_tg:
                st_tg, msg_tg = postar_no_telegram(TELEGRAM_BOT_TOKEN_FIXO, TELEGRAM_CHAT_ID_FIXO, texto_gerado, imagens_upload)
                if st_tg:
                    st.success(f"✅ **Telegram:** {msg_tg}")
                else:
                    st.error(f"❌ **Telegram:** {msg_tg}")

            if enviar_ig:
                if not IMGBB_API_KEY_FIXO:
                    st.error("❌ **Instagram:** Chave do ImgBB ausente.")
                elif not imagens_upload:
                    st.warning("⚠️ **Instagram:** Selecione ao menos uma imagem para enviar.")
                else:
                    st_ig, msg_ig = postar_no_instagram(INSTAGRAM_USER_ID_FIXO, FB_PAGE_TOKEN_FIXO, texto_gerado, imagens_upload, IMGBB_API_KEY_FIXO, link_afiliado)
                    if st_ig:
                        st.success(f"✅ **Instagram:** {msg_ig}")
                    else:
                        st.error(f"❌ **Instagram:** {msg_ig}")

with tab_roteiro_locucao:
    st.markdown("### 🎙️ Gerador de Roteiro Comercial & Áudio de Locução")
    
    if st.button("✨ Gerar Roteiro e Áudio da Locução", type="primary", use_container_width=True):
        if not titulo_produto or not preco_por:
            st.warning("Preencha ao menos o Título e o Preço Por para gerar o roteiro e a locução.")
        else:
            with st.spinner("Sintetizando locução profissional..."):
                texto_fala = f"Olha que achado absurdo! {titulo_produto}. Ele está saindo por apenas {preco_por} reais! Corre pra garantir o seu no link da descrição!"
                
                tts = gTTS(text=texto_fala, lang='pt', tld='com.br')
                audio_output_path = "locucao_oferta.mp3"
                tts.save(audio_output_path)

                st.markdown("#### 🎧 Ouça a Locução Gerada:")
                st.audio(audio_output_path, format="audio/mp3")

                with open(audio_output_path, "rb") as f:
                    st.download_button(
                        label="📥 Baixar Arquivo de Áudio (MP3)",
                        data=f,
                        file_name="locucao_oferta.mp3",
                        mime="audio/mp3"
                )
