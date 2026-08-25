import streamlit as st
import requests

# ==========================================
# CONFIGURAÇÕES INICIAIS DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Painel de Ofertas",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas")
st.markdown("Crie promoções completas e publique no Facebook, Telegram e WhatsApp.")

# ==========================================
# BARRA LATERAL - CONFIGURAÇÕES DE API
# ==========================================
st.sidebar.header("⚙️ Configurações das APIs")

# Telegram
st.sidebar.subheader("Telegram")
telegram_bot_token = st.sidebar.text_input("Bot Token (Telegram)", type="password", key="tg_token")
telegram_chat_id = st.sidebar.text_input("Chat ID / Canal (Telegram)", key="tg_chat_id")

# Facebook Page (Configurado com seus dados da PromoMania)
st.sidebar.subheader("Facebook Page")
fb_page_id = st.sidebar.text_input("ID da Página FB", value="1283510278175598", key="fb_page_id")
fb_page_token = st.sidebar.text_input(
    "Token da Página FB", 
    value="EAAPZAdxais7gBSUWxZCSGOBmtoW0Ni1jiVl7XV2uNY9kdm8vOs9FA0RZB7Y6a8pQGqjeTv2aFKplqMLCHw5oQwIW8HRZCRFroZC36qR3KhkMTer4TkFEeWjSZATj5mft7tZCHWcB0L6NHUkWcYfOZBDmmPPimz9KWqiZA8cyvPGOw5Y5cm15tbpU98hmjZA5MkxbCACVrOmnb9GWvjgseBxWMBgEhFsJdXahcSEHjOzWcY0p7z", 
    type="password", 
    key="fb_page_token"
)

# WhatsApp (Webhook ou API)
st.sidebar.subheader("WhatsApp")
wsp_webhook_url = st.sidebar.text_input("URL do Webhook / API WhatsApp", key="wsp_url", placeholder="https://sua-api-whatsapp.com/send")

# ==========================================
# FUNÇÕES DE ENVIO
# ==========================================

def postar_no_telegram(token, chat_id, texto, arquivo_imagem):
    if not token or not chat_id:
        return False, "Token ou Chat ID do Telegram não informados."
    try:
        if arquivo_imagem:
            arquivo_imagem.seek(0)
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            files = {"photo": (arquivo_imagem.name, arquivo_imagem, arquivo_imagem.type)}
            data = {"chat_id": chat_id, "caption": texto, "parse_mode": "HTML"}
            response = requests.post(url, data=data, files=files, timeout=15)
        else:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
            response = requests.post(url, data=data, timeout=10)
        
        res_data = response.json()
        return (True, "Publicado no Telegram!") if res_data.get("ok") else (False, f"Erro Telegram: {res_data.get('description')}")
    except Exception as e:
        return False, f"Falha no Telegram: {str(e)}"


def postar_no_facebook(page_id, page_token, texto, arquivo_imagem):
    if not page_id or not page_token:
        return False, "ID da Página ou Token de Acesso do FB não informados."
    try:
        if arquivo_imagem:
            arquivo_imagem.seek(0)
            url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
            files = {"source": (arquivo_imagem.name, arquivo_imagem, arquivo_imagem.type)}
            data = {"caption": texto, "access_token": page_token}
            response = requests.post(url, data=data, files=files, timeout=20)
        else:
            url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            data = {"message": texto, "access_token": page_token}
            response = requests.post(url, data=data, timeout=10)
            
        res_data = response.json()
        if "id" in res_data or "post_id" in res_data:
            return True, "Publicado na Página do Facebook!"
        else:
            return False, f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro desconhecido')}"
    except Exception as e:
        return False, f"Falha no Facebook: {str(e)}"


def postar_no_whatsapp(webhook_url, texto):
    if not webhook_url:
        return False, "URL de API/Webhook do WhatsApp não configurada."
    try:
        payload = {"message": texto}
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Enviado para o WhatsApp!"
        else:
            return False, f"Erro WhatsApp (Status {response.status_code})"
    except Exception as e:
        return False, f"Falha no WhatsApp: {str(e)}"

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================

st.subheader("📝 Preencher Dados da Oferta")

col1, col2 = st.columns([1, 1])

with col1:
    titulo_produto = st.text_input("Título do Produto", placeholder="Ex: Smart TV 55\" 4K")
    preco_de = st.text_input("Preço De (R$)", placeholder="Ex: 2.999,00")
    preco_por = st.text_input("Preço Por (R$)", placeholder="Ex: 1.899,00")
    cupom = st.text_input("Cupom de Desconto (Opcional)", placeholder="Ex: DESCONTO10")

with col2:
    link_afiliado = st.text_input("Link da Oferta / Afiliado", placeholder="https://...")
    
    # Upload direto da galeria/arquivo
    imagem_upload = st.file_uploader(
        "📸 Selecionar Imagem da Galeria", 
        type=["jpg", "jpeg", "png", "webp"]
    )
    
    if imagem_upload:
        st.image(imagem_upload, caption="Pré-visualização da imagem", width=150)

# Descrição adicional opcional
descricao_extra = st.text_area("Observações / Detalhes Adicionais (Opcional)", placeholder="Ex: Frete Grátis para assinantes Prime", height=70)

# Montagem automática da mensagem
texto_gerado = f"🔥 **{titulo_produto if titulo_produto else 'OFERTA IMPERDÍVEL'}**\n\n"
if preco_de:
    texto_gerado += f"❌ De: R$ {preco_de}\n"
if preco_por:
    texto_gerado += f"✅ **Por: R$ {preco_por}**\n"
if cupom:
    texto_gerado += f"🎟️ Cupom: `{cupom}`\n"
if descricao_extra:
    texto_gerado += f"\nℹ️ {descricao_extra}\n"
if link_afiliado:
    texto_gerado += f"\n🛒 **Compre Aqui:** {link_afiliado}"

st.markdown("---")
st.subheader("👀 Pré-visualização da Mensagem")
st.info(texto_gerado)

st.markdown("---")
st.markdown("### 🎯 Selecione os Destinos")
col_check1, col_check2, col_check3 = st.columns(3)

with col_check1:
    enviar_fb = st.checkbox("Facebook Page", value=True)
with col_check2:
    enviar_tg = st.checkbox("Telegram", value=True)
with col_check3:
    enviar_wsp = st.checkbox("WhatsApp", value=False)

st.markdown("---")

if st.button("🚀 Postar Oferta em Todos os Canais", type="primary", use_container_width=True):
    if not titulo_produto and not link_afiliado:
        st.warning("Preencha ao menos o Título e o Link do produto antes de postar.")
    else:
        st.info("Enviando publicações...")
        
        # Facebook
        if enviar_fb:
            st_fb, msg_fb = postar_no_facebook(fb_page_id, fb_page_token, texto_gerado, imagem_upload)
            if st_fb:
                st.success(f"✅ **Facebook:** {msg_fb}")
            else:
                st.error(f"❌ **Facebook:** {msg_fb}")
                
        # Telegram
        if enviar_tg:
            st_tg, msg_tg = postar_no_telegram(telegram_bot_token, telegram_chat_id, texto_gerado, imagem_upload)
            if st_tg:
                st.success(f"✅ **Telegram:** {msg_tg}")
            else:
                st.error(f"❌ **Telegram:** {msg_tg}")
                
        # WhatsApp
        if enviar_wsp:
            st_wsp, msg_wsp = postar_no_whatsapp(wsp_webhook_url, texto_gerado)
            if st_wsp:
                st.success(f"✅ **WhatsApp:** {msg_wsp}")
            else:
                st.error(f"❌ **WhatsApp:** {msg_wsp}")
