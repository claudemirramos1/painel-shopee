import streamlit as st
import requests
import json
import os
from gtts import gTTS

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
    page_title="Painel de Ofertas & Vídeo IA",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas & Vídeos IA")
st.markdown("Publique ofertas nas redes sociais e crie vídeos automáticos com inteligência artificial.")

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
tab_redes, tab_ia_video = st.tabs(["📢 Redes Sociais", "🎬 Gerador de Vídeo com IA"])

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

with tab_ia_video:
    st.markdown("### 🤖 Criação de Roteiro e Locução IA para YouTube Shorts / Reels")
    st.markdown("A inteligência artificial prepara o roteiro de vendas persuasivo, gera a locução em áudio profissional e organiza o conteúdo para seu vídeo.")

    api_key_ia = st.text_input("Chave de API (Opcional para serviços externos / Replicate / HeyGen)", type="password", placeholder="Deixe em branco para usar o gerador de voz e roteiro integrado")

    if st.button("✨ Gerar Roteiro e Locução de Vídeo com IA", type="primary", use_container_width=True):
        if not titulo_produto or not preco_por:
            st.warning("Preencha o Título e o Preço Por do produto para criar o vídeo com IA.")
        else:
            with st.spinner("A IA está estruturando o roteiro de alta conversão e gerando a locução..."):
                roteiro_ia = f"""
🎬 **ROTEIRO SUGERIDO PARA SHORTS / REELS:**
- **Gancho (0-3s):** "Você não vai acreditar nesse achado! Olha isso!"
- **Corpo (3-15s):** "Estou falando do incrível {titulo_produto}. Ele de {preco_de if preco_de else 'preço alto'} está saindo por apenas {preco_por} reais!"
- **Chamada para Ação (CTA):** "O link com desconto exclusivo e cupom está na descrição ou nos comentários. Corre que o estoque acaba rápido!"
                """
                st.markdown(roteiro_ia)

                # Gerar locução em áudio profissional via gTTS (IA de Voz)
                texto_locucao = f"Olha que oferta imperdível! {titulo_produto}. Apenas por {preco_por} reais! Corra para garantir o seu no link da descrição!"
                tts = gTTS(text=texto_locucao, lang='pt', tld='com.br')
                audio_path = "locucao_ia.mp3"
                tts.save(audio_path)

                st.success("🎉 Roteiro e Locução gerados com sucesso por Inteligência Artificial!")
                st.audio(audio_path, format="audio/mp3")

                with open(audio_path, "rb") as f:
                    st.download_button(
                        label="📥 Baixar Áudio da Locução (MP3)",
                        data=f,
                        file_name="locucao_oferta.mp3",
                        mime="audio/mp3"
            )
