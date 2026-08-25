import requests
import streamlit as st

st.set_page_config(
    page_title="Painel de Ofertas Shopee", page_icon="🛍️", layout="centered"
)


def send_to_telegram(token, chat_id, text, media_file):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
    files = {"photo": media_file.getvalue()}
    response = requests.post(url, data=payload, files=files)
    return response.json()


st.title("🛍️ Painel Automático de Ofertas")
st.write("Preencha os dados da promoção para publicar no Telegram.")

# Credenciais preenchidas automaticamente
st.sidebar.header("🔑 Configurações do Telegram")
telegram_token = st.sidebar.text_input(
    "Telegram Bot Token",
    value="8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04",
    type="password",
)
telegram_chat_id = st.sidebar.text_input(
    "Telegram Chat ID", value="-1004406728710"
)

with st.form("offer_form"):
    title = st.text_input("Nome do Produto", "Fone Bluetooth Sem Fio")
    price = st.text_input("Preço (R$)", "49,90")
    code = st.text_input("Cupom/Código", "SHOPEE20")
    affiliate_link = st.text_input("Link de Afiliado", "https://shope.ee/exemplo")

    media_file = st.file_uploader(
        "Selecione a Imagem da Oferta", type=["jpg", "jpeg", "png"]
    )

    submit = st.form_submit_button("🚀 Enviar para o Telegram")

if submit:
    if not media_file:
        st.error("Por favor, selecione uma imagem!")
    elif not telegram_token:
        st.error("Cole o seu Bot Token na barra lateral!")
    else:
        caption_tg = f"🔥 *{title}*\n\n💰 Por apenas: *R$ {price}*\n🏷️ Cupom: `{code}`\n\n👇 *Compre pelo link:*\n{affiliate_link}"

        res = send_to_telegram(
            telegram_token, telegram_chat_id, caption_tg, media_file
        )

        if res.get("ok"):
            st.success("✅ Enviado para o Telegram com sucesso!")
        else:
            st.error(f"❌ Erro ao enviar: {res.get('description')}")
