import streamlit as st
import requests
import json
import os
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# ==========================================
# CONFIGURAÇÕES FIXAS
# ==========================================
FB_PAGE_ID_FIXO = "1214303865109377"
FB_PAGE_TOKEN_FIXO = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

TELEGRAM_BOT_TOKEN_FIXO = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TELEGRAM_CHAT_ID_FIXO = "-1004406728710"

# ==========================================
# CONFIGURAÇÕES INICIAIS DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel de Ofertas & Vídeos",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas & Vídeos")
st.markdown("Publique ofertas nas redes e crie vídeos automáticos para o YouTube Shorts de forma gratuita.")

# ==========================================
# FUNÇÕES DE REDES SOCIAIS
# ==========================================

def postar_no_telegram(token, chat_id, texto, lista_imagens):
    if not token or not chat_id:
        return False, "Token ou Chat ID do Telegram não informados."
    try:
        if lista_imagens and len(lista_imagens) == 1:
            img = lista_imagens[0]
            img.seek(0)
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            files = {"photo": (img.name, img.getvalue(), img.type)}
            data = {"chat_id": chat_id, "caption": texto, "parse_mode": "HTML"}
            response = requests.post(url, data=data, files=files, timeout=20)
            res_data = response.json()
            return (True, "Publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")
        
        elif lista_imagens and len(lista_imagens) > 1:
            url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
            media = []
            files = {}
            for idx, img in enumerate(lista_imagens):
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
        
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
            response = requests.post(url, data=data, timeout=10)
            res_data = response.json()
            return (True, "Publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")

    except Exception as e:
        return False, f"Falha no Telegram: {str(e)}"


def postar_no_facebook(page_id, page_token, texto_fb, lista_imagens, link_oferta=None):
    if not page_id or not page_token:
        return False, "ID da Página ou Token de Acesso do FB não informados."
    try:
        legenda_limpa = texto_fb.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
        
        if not lista_imagens or len(lista_imagens) == 0:
            url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            payload = {"message": legenda_limpa, "access_token": page_token}
            if link_oferta and link_oferta.strip():
                payload["link"] = link_oferta.strip()
            response = requests.post(url, data=payload, timeout=15)
            res_data = response.json()
            return (True, "Publicado no Facebook!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

        elif len(lista_imagens) == 1:
            img = lista_imagens[0]
            img.seek(0)
            url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
            files = {"source": (img.name, img.getvalue(), img.type)}
            payload = {"caption": legenda_limpa, "access_token": page_token}
            response = requests.post(url, data=payload, files=files, timeout=30)
            res_data = response.json()
            return (True, "Publicado no Facebook com foto!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

        else:
            attached_media_list = []
            for img in lista_imagens:
                img.seek(0)
                url_upload = f"https://graph.facebook.com/v26.0/{page_id}/photos"
                files = {"source": (img.name, img.getvalue(), img.type)}
                payload_upload = {"published": "false", "access_token": page_token}
                resp_upload = requests.post(url_upload, data=payload_upload, files=files, timeout=30)
                data_upload = resp_upload.json()
                if "id" in data_upload:
                    attached_media_list.append({"media_fbid": data_upload["id"]})
                else:
                    return False, f"Erro ao enviar foto para o álbum: {data_upload.get('error', {}).get('message', 'Erro')}"
            
            url_feed = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            payload_feed = {
                "message": legenda_limpa,
                "attached_media": json.dumps(attached_media_list),
                "access_token": page_token
            }
            response = requests.post(url_feed, data=payload_feed, timeout=30)
            res_data = response.json()
            return (True, "Álbum publicado no Facebook com sucesso!") if ("id" in res_data or "post_id" in res_data) else (False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}")

    except Exception as e:
        return False, f"Falha no Facebook: {str(e)}"

# ==========================================
# FUNÇÃO DE GERAÇÃO DE VÍDEO AUTOMÁTICO
# ==========================================

def gerar_video_shorts(titulo, preco_por, lista_imagens):
    try:
        texto_fala = f"Olha que oferta imperdível! {titulo}. Apenas por {preco_por} reais! Corra para garantir o seu!"
        
        # 1. Gerar Áudio com gTTS
        tts = gTTS(text=texto_fala, lang='pt', tld='com.br')
        audio_path = "temp_audio.mp3"
        tts.save(audio_path)
        
        audio_clip = AudioFileClip(audio_path)
        duracao_total = audio_clip.duration
        
        # 2. Processar imagens
        temp_img_paths = []
        num_imagens = len(lista_imagens)
        duracao_por_foto = max(duracao_total / num_imagens, 2.0)
        
        image_clips = []
        for idx, img in enumerate(lista_imagens):
            img_path = f"temp_img_{idx}.jpg"
            with open(img_path, "wb") as f:
                f.write(img.getbuffer())
            temp_img_paths.append(img_path)
            
            clip = ImageClip(img_path).set_duration(duracao_por_foto).resize(height=1920)
            image_clips.append(clip)
            
        video_base = concatenate_videoclips(image_clips, method="compose")
        video_final = video_base.set_audio(audio_clip)
        
        output_video_path = "shorts_oferta.mp4"
        video_final.write_videofile(
            output_video_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            logger=None
        )
        
        audio_clip.close()
        video_final.close()
        
        for p in temp_img_paths:
            if os.path.exists(p):
                os.remove(p)
                
        return True, output_video_path
        
    except Exception as e:
        return False, str(e)

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
st.subheader("👀 Pré-visualização da Mensagem")
st.info(texto_gerado)

st.markdown("---")

tab_redes, tab_shorts = st.tabs(["📢 Redes Sociais", "🎬 Gerador de Shorts"])

with tab_redes:
    st.markdown("### 🎯 Selecione os Destinos")
    col_check1, col_check2 = st.columns(2)
    with col_check1:
        enviar_fb = st.checkbox("Facebook Page", value=True)
    with col_check2:
        enviar_tg = st.checkbox("Telegram", value=True)

    st.markdown("---")
    if st.button("🚀 Postar Oferta em Todos os Canais", type="primary", use_container_width=True):
        if not titulo_produto and not link_afiliado:
            st.warning("Preencha ao menos o Título e o Link do produto antes de postar.")
        else:
            st.info("Enviando publicações...")
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

with tab_shorts:
    st.markdown("### 🎬 Criador Automático de Vídeo para YouTube Shorts / Reels")
    st.markdown("Transforme as fotos e o preço do produto em um vídeo narrado automaticamente.")
    
    if st.button("⚡ Gerar Vídeo para Shorts Agora", type="primary", use_container_width=True):
        if not titulo_produto or not preco_por or not imagens_upload:
            st.warning("Para gerar o vídeo, preencha ao menos o Título, o Preço Por e selecione ao menos 1 imagem.")
        else:
            with st.spinner("Criando áudio falado, organizando fotos e renderizando o vídeo... Aguarde alguns segundos."):
                sucesso, resultado = gerar_video_shorts(titulo_produto, preco_por, imagens_upload)
                if sucesso:
                    st.success("🎉 Vídeo gerado com sucesso!")
                    st.video(resultado)
                    
                    with open(resultado, "rb") as file:
                        st.download_button(
                            label="📥 Baixar Vídeo MP4",
                            data=file,
                            file_name="shorts_oferta.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error(f"❌ Erro ao gerar vídeo: {resultado}")
