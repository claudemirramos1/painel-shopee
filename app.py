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
    
