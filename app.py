import streamlit as st
import requests
import json

# ==========================================
# CONFIGURAÇÕES INICIAIS DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel de Ofertas",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas")
st.markdown("Publique facilmente em suas redes sociais e canais de transmissão.")

# ==========================================
# BARRA LATERAL - CONFIGURAÇÕES DE API
# ==========================================
st.sidebar.header("⚙️ Configurações das APIs")

# Telegram
st.sidebar.subheader("Telegram")
telegram_bot_token = st.sidebar.text_input("Bot Token (Telegram)", type="password", key="tg_token")
telegram_chat_id = st.sidebar.text_input("Chat ID / Canal (Telegram)", key="tg_chat_id")

# Facebook Page (Valores atualizados com os dados gerados)
st.sidebar.subheader("Facebook Page")
fb_page_id = st.sidebar.text_input(
    "ID da Página FB", 
    value="1283510278175598", 
    key="fb_page_id"
)
fb_page_token = st.sidebar.text_input(
    "Token da Página FB", 
    value="EAAPZAdxais7gBSUWxZCSGOBmtoW0Ni1jiVl7XV2uNY9kdm8vOs9FA0RZB7Y6a8pQGqjeTv2aFKplqMLCHw5oQwIW8HRZCRFroZC36qR3KhkMTer4TkFEeWjSZATj5mft7tZCHWcB0L6NHUkWcYfOZBDmmPPimz9KWqiZA8cyvPGOw5Y5cm15tbpU98hmjZA5MkxbCACVrOmnb9GWvjgseBxWMBgEhFsJdXahcSEHjOzWcY0p7z", 
    type="password", 
    key="fb_page_token"
)

# ==========================================
# FUNÇÕES DE ENVIO DE MENSAGENS
# ==========================================

def postar_no_telegram(token, chat_id, texto, url_imagem=None):
    """Envia texto ou foto + legenda para o canal do Telegram."""
    if not token or not chat_id:
        return False, "Token ou Chat ID do Telegram não informados."
    
    try:
        if url_imagem:
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            payload = {
                "chat_id": chat_id,
                "photo": url_imagem,
                "caption": texto,
                "parse_mode": "HTML"
            }
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": texto,
                "parse_mode": "HTML"
            }
        
        response = requests.post(url, data=payload, timeout=10)
        res_data = response.json()
        
        if res_data.get("ok"):
            return True, "Publicado com sucesso no Telegram!"
        else:
            return False, f"Erro Telegram: {res_data.get('description')}"
    except Exception as e:
        return False, f"Falha na requisição do Telegram: {str(e)}"


def postar_no_facebook(page_id, page_token, texto, url_imagem=None):
    """Envia texto ou foto + mensagem para a Página do Facebook."""
    if not page_id or not page_token:
        return False, "ID da Página ou Token de Acesso não informados."
    
    try:
        if url_imagem:
            # Postagem com Foto
            url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
            payload = {
                "url": url_imagem,
                "caption": texto,
                "access_token": page_token
            }
        else:
            # Postagem apenas com Texto
            url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            payload = {
                "message": texto,
                "access_token": page_token
            }
            
        response = requests.post(url, data=payload, timeout=15)
        res_data = response.json()
        
        if "id" in res_data or "post_id" in res_data:
            return True, "Publicado com sucesso na Página do Facebook!"
        else:
            erro_msg = res_data.get("error", {}).get("message", "Erro desconhecido")
            return False, f"Erro Facebook: {erro_msg}"
    except Exception as e:
        return False, f"Falha na requisição do Facebook: {str(e)}"

# ==========================================
# INTERFACE PRINCIPAL DO USUÁRIO
# ==========================================

st.subheader("📝 Criar Nova Oferta")

col_left, col_right = st.columns([2, 1])

with col_left:
    texto_oferta = st.text_area("Texto / Legenda da Oferta", height=180, placeholder="Digite a chamada da promoção, link de afiliado, cupom...")
    url_imagem = st.text_input("URL da Imagem do Produto (Opcional)", placeholder="https://exemplo.com/imagem.jpg")

with col_right:
    st.markdown("### 🎯 Destinos")
    enviar_tg = st.checkbox("Telegram", value=True)
    enviar_fb = st.checkbox("Facebook Page", value=True)

st.markdown("---")

if st.button("🚀 Postar em Todos os Canais", type="primary", use_container_width=True):
    if not texto_oferta.strip():
        st.warning("Por favor, preencha o texto da oferta antes de enviar.")
    else:
        st.info("Iniciando publicação...")
        
        # Envio Telegram
        if enviar_tg:
            status_tg, msg_tg = postar_no_telegram(telegram_bot_token, telegram_chat_id, texto_oferta, url_imagem if url_imagem.strip() else None)
            if status_tg:
                st.success(f"✅ **Telegram:** {msg_tg}")
            else:
                st.error(f"❌ **Telegram:** {msg_tg}")
                
        # Envio Facebook
        if enviar_fb:
            status_fb, msg_fb = postar_no_facebook(fb_page_id, fb_page_token, texto_oferta, url_imagem if url_imagem.strip() else None)
            if status_fb:
                st.success(f"✅ **Facebook:** {msg_fb}")
            else:
                st.error(f"❌ **Facebook:** {msg_fb}")
