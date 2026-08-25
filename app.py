import json
import requests
import streamlit as st

st.set_page_config(
    page_title="Painel de Ofertas", page_icon="🛍️", layout="centered"
)


# Função para enviar foto/álbum para o Telegram
def send_album_to_telegram(token, chat_id, text, media_files):
    if len(media_files) == 1:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
        files = {"photo": media_files[0].getvalue()}
        response = requests.post(url, data=payload, files=files)
        return response.json()

    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    media = []
    files = {}

    for idx, file in enumerate(media_files):
        field_name = f"photo_{idx}"
        files[field_name] = file.getvalue()
        item = {"type": "photo", "media": f"attach://{field_name}"}

        if idx == 0:
            item["caption"] = text
            item["parse_mode"] = "Markdown"

        media.append(item)

    payload = {"chat_id": chat_id, "media": json.dumps(media)}
    response = requests.post(url, data=payload, files=files)
    return response.json()


# Função para enviar foto + legenda para a Página do Facebook
def send_to_facebook_page(page_id, page_token, text, media_file):
    url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    payload = {"message": text, "access_token": page_token}
    files = {"source": media_file.getvalue()}
    response = requests.post(url, data=payload, files=files)
    return response.json()


st.title("🛍️ Painel de Ofertas Automático")

st.sidebar.header("🔑 Configurações do Telegram")
telegram_token = st.sidebar.text_input(
    "Telegram Bot Token",
    value="8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04",
    type="password",
)
telegram_chat_id = st.sidebar.text_input(
    "Telegram Chat ID", value="-1004406728710"
)

st.sidebar.header("📘 Configurações do Facebook")
fb_page_id = st.sidebar.text_input("ID da Página do FB", value="61593393377161")
fb_page_token = st.sidebar.text_input(
    "Token da Página do FB",
    value="EAAPZAdxais7gBSfB59U8h4QebaHJbtYuZA7m2H70QC3bRYcEnge4kUBIrKc30CPPow7XbYPg4jCcUgfvhf6ygqgthhfp0boakczZCMZAZAy7Rt1ZAcO7NcRSZBZBL53XolDYgZCDKpdyEMFjZB35e10liFkNcF5i4JxwbBZB2hUiHCbJAYyZC1DRi4IODG7IJIxs82cwFRZAQwYftrOQZBrKfNvkb0KhqXKvKRLrnICSqudKQGWr9sYn2IUPizgSciSkB8Y8PJROdh9CPtBuyWluAO9SkSxLgcGAZDZD",
    type="password",
)

with st.form("offer_form"):
    title = st.text_input("Nome do Produto", "Fone Bluetooth Sem Fio")
    price = st.text_input("Preço (R$)", "49,90")
    code = st.text_input("Cupom/Código (opcional)", "SHOPEE20")
    affiliate_link = st.text_input("Link de Afiliado", "https://shope.ee/exemplo")

    media_files = st.file_uploader(
        "Selecione a(s) Imagem(ns) da Oferta",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    submit = st.form_submit_button("🚀 Postar em Todos os Canais")

if submit:
    if not media_files:
        st.error("Por favor, selecione pelo menos uma imagem!")
    else:
        # Formatação para o Telegram
        cupom_tg = f"\n🏷️ Cupom: `{code}`" if code else ""
        caption_tg = f"🔥 *{title}*\n\n💰 Por apenas: *R$ {price}*{cupom_tg}\n\n👇 *Compre pelo link:*\n{affiliate_link}"

        # Formatação para o Facebook (texto limpo)
        cupom_fb = f"\n🏷️ Cupom: {code}" if code else ""
        caption_fb = f"🔥 {title}\n\n💰 Por apenas: R$ {price}{cupom_fb}\n\n👇 Compre pelo link:\n{affiliate_link}"

        # 1. Enviar para Telegram
        if telegram_token and telegram_chat_id:
            res_tg = send_album_to_telegram(
                telegram_token, telegram_chat_id, caption_tg, media_files
            )
            if res_tg.get("ok"):
                st.success("✅ Publicado no Telegram!")
            else:
                st.error(
                    f"❌ Erro no Telegram: {res_tg.get('description')}"
                )

        # 2. Enviar para o Facebook
        if fb_page_id and fb_page_token:
            res_fb = send_to_facebook_page(
                fb_page_id, fb_page_token, caption_fb, media_files[0]
            )
            if "id" in res_fb:
                st.success("✅ Publicado na Página do Facebook!")
            else:
                st.error(
                    f"❌ Erro no Facebook: {res_fb.get('error', {}).get('message')}"
                )

        st.divider()
        st.subheader("📲 Texto Formatado (WhatsApp)")
        cupom_wa = f"\n🏷️ Cupom: *{code}*" if code else ""
        caption_wa = f"🔥 *{title}*\n\n💰 Por apenas: *R$ {price}*{cupom_wa}\n\n👇 *Compre pelo link:*\n{affiliate_link}"
        st.code(caption_wa, language="markdown")
