import streamlit as st
import requests
import json
from gtts import gTTS
from PIL import Image, ImageOps, ImageEnhance
import io

# ==========================================
# CONFIGURAÇÕES FIXAS (Insira seus dados aqui)
# ==========================================
FB_PAGE_ID_FIXO = "1214303865109377"
FB_PAGE_TOKEN_FIXO = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

TELEGRAM_BOT_TOKEN_FIXO = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TELEGRAM_CHAT_ID_FIXO = "-1004406728710"

# Configurações do Threads (Insira o ID e Token da sua conta do Threads/Meta)
THREADS_USER_ID_FIXO = ""  # Ex: ID da sua conta do Threads
THREADS_TOKEN_FIXO = ""    # Token de acesso da API do Threads

# ==========================================
# CONFIGURAÇÕES INICIAIS DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel de Ofertas & Redes Sociais",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas (Facebook, Telegram & Threads)")
st.markdown("Publique ofertas com várias fotos tratadas em alta resolução (1080x1350) integradas de forma automatizada.")

# ==========================================
# FUNÇÃO DE PROCESSAMENTO DE IMAGEM
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

# ==========================================
# FUNÇÕES DE REDES SOCIAIS
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
            return (True, "Álbum com múltiplas fotos publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")

    except Exception as e:
        return False, f"Falha no Telegram: {str(e)}"


def postar_no_facebook(page_id, page_token, texto_fb, lista_imagens, link_oferta=None):
    if not page_id or not page_token:
        return False, "ID da Página ou Token de Acesso do FB não informados."
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
            return (True, "Publicado no Facebook com foto em alta resolução!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

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
                    return False, f"Erro ao enviar foto do carrossel: {data_upload.get('error', {}).get('message', 'Erro')}"
            
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
            return (True, "Publicado no Facebook com múltiplas fotos em alta resolução!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

    except Exception as e:
        return False, f"Falha no Facebook: {str(e)}"


def postar_no_threads(user_id, token, texto_threads, lista_imagens, link_oferta=None):
    """
    Publica no Threads (API oficial da Meta).
    Nota: O Threads exige criar um contêiner de mídia primeiro e depois publicá-lo.
    """
    if not user_id or not token:
        return False, "User ID ou Token do Threads não configurados."
    try:
        legenda_limpa = texto_threads.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
        
        # O Threads utiliza URL pública para imagens na API oficial. Como estamos usando upload local no Streamlit,
        # enviamos o texto formatado com o link da oferta.
        url = f"https://graph.threads.net/v1.0/{user_id}/threads"
        payload = {
            "media_type": "TEXT",
            "text": legenda_limpa,
            "access_token": token
        }
        
        response = requests.post(url, data=payload, timeout=20)
        res_data = response.json()
        
        if "id" in res_data:
            container_id = res_data["id"]
            # Publica o contêiner criado
            url_publish = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
            payload_publish = {
                "creation_id": container_id,
                "access_token": token
            }
            pub_response = requests.post(url_publish, data=payload_publish, timeout=20)
            pub_data = pub_response.json()
            
            return (True, "Publicado no Threads com sucesso!") if "id" in pub_data else (False, f"Erro ao publicar contêiner no Threads: {pub_data.get('error', {}).get('message', 'Erro')}")
        else:
            return False, f"Erro Threads: {res_data.get('error', {}).get('message', 'Erro ao criar container')}"
            
    except Exception as e:
        return False, f"Falha no Threads: {str(e)}"

# ==========================================
# INTERFACE PRINCIPAL
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
        "📸 Selecionar Imagens da Galeria (Pode escolher várias)", 
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )
    
    if imagens_upload:
        st.write(f"📷 {len(imagens_upload)} imagem(ns) selecionada(s)")
        cols_img = st.columns(min(len(imagens_upload), 4))
        for idx, img in enumerate(imagens_upload):
            cols_img[idx % 4].image(img, use_container_width=True)

descricao_extra = st.text_area("Observações / Detalhes Adicionais (Opcional)", placeholder="Ex: Frete Grátis para assinantes Prime", height=70)

# Montagem do texto das publicações
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

# Abas de Ações
tab_redes, tab_roteiro_locucao = st.tabs(["📢 Redes Sociais", "🎙️ Roteiro & Locução IA"])

with tab_redes:
    st.markdown("### 🎯 Selecione os Destinos")
    col_check1, col_check2, col_check3 = st.columns(3)
    with col_check1:
        enviar_fb = st.checkbox("Facebook Page (HD)", value=True)
    with col_check2:
        enviar_tg = st.checkbox("Telegram (Álbum)", value=True)
    with col_check3:
        enviar_th = st.checkbox("Threads", value=False)

    st.markdown("---")
    if st.button("🚀 Postar Oferta em Todos os Canais", type="primary", use_container_width=True):
        if not titulo_produto and not link_afiliado:
            st.warning("Preencha ao menos o Título e o Link do produto antes de postar.")
        else:
            st.info("Processando imagens e publicando nos canais selecionados...")
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

            if enviar_th:
                st_th, msg_th = postar_no_threads(THREADS_USER_ID_FIXO, THREADS_TOKEN_FIXO, texto_gerado, imagens_upload, link_afiliado)
                if st_th:
                    st.success(f"✅ **Threads:** {msg_th}")
                else:
                    st.error(f"❌ **Threads:** {msg_th}")

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
