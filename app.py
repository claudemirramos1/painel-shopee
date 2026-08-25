import streamlit as st
import requests

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
    page_title="Painel de Ofertas",
    page_icon="🛍️",
    layout="wide"
)

st.title("🛍️ Painel de Automação de Ofertas")
st.markdown("Crie promoções completas e publique no Facebook, Telegram e WhatsApp de forma automática.")

# ==========================================
# FUNÇÕES DE ENVIO
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
                "media": requests.compat.json.dumps(media)
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
        # Remove tags HTML para enviar texto limpo ao Facebook
        legenda_limpa = texto_fb.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
        
        # Se houver imagem anexada, publica na rota /photos
        if lista_imagens and len(lista_imagens) > 0:
            img = lista_imagens[0]
            img.seek(0)
            url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
            
            files = {
                "source": (img.name, img.getvalue(), img.type)
            }
            payload = {
                "caption": legenda_limpa,
                "access_token": page_token
            }
            if link_oferta and link_oferta.strip():
                # Nota: Na API de fotos do FB, o link opcional pode ir na legenda ou não ser aceito simultaneamente dependendo da regra, mas a caption já tem o link.
                pass
                
            response = requests.post(url, data=payload, files=files, timeout=30)
        else:
            # Caso não tenha imagem, posta como texto/link normal no /feed
            url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
            payload = {
                "message": legenda_limpa,
                "access_token": page_token
            }
            if link_oferta and link_oferta.strip():
                payload["link"] = link_oferta.strip()
            response = requests.post(url, data=payload, timeout=15)
            
        res_data = response.json()
        
        if "id" in res_data or "post_id" in res_data:
            return True, "Publicado no Facebook com foto!" if (lista_imagens and len(lista_imagens) > 0) else "Publicado no Facebook!"
        else:
            err = res_data.get("error", {})
            return False, f"Erro Facebook: {err.get('message', 'Erro desconhecido')}"
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
st.markdown("### 🎯 Selecione os Destinos")
col_check1, col_check2, col_check3 = st.columns(3)

with col_check1:
    enviar_fb = st.checkbox("Facebook Page", value=True)
with col_check2:
    enviar_tg = st.checkbox("Telegram", value=True)
with col_check3:
    enviar_wsp = st.checkbox("WhatsApp", value=False)

if enviar_wsp:
    wsp_webhook_url = st.text_input("URL do Webhook / API WhatsApp", placeholder="https://sua-api-whatsapp.com/send")
else:
    wsp_webhook_url = ""

st.markdown("---")

if st.button("🚀 Postar Oferta em Todos os Canais", type="primary", use_container_width=True):
    if not titulo_produto and not link_afiliado:
        st.warning("Preencha ao menos o Título e o Link do produto antes de postar.")
    else:
        st.info("Enviando publicações...")
        
        # Facebook
        if enviar_fb:
            st_fb, msg_fb = postar_no_facebook(FB_PAGE_ID_FIXO, FB_PAGE_TOKEN_FIXO, texto_gerado, imagens_upload, link_afiliado)
            if st_fb:
                st.success(f"✅ **Facebook:** {msg_fb}")
            else:
                st.error(f"❌ **Facebook:** {msg_fb}")
                
        # Telegram
        if enviar_tg:
            st_tg, msg_tg = postar_no_telegram(TELEGRAM_BOT_TOKEN_FIXO, TELEGRAM_CHAT_ID_FIXO, texto_gerado, imagens_upload)
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
