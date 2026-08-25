import requests
import streamlit as st

# ==========================================
# CONFIGURAÇÕES E CREDENCIAIS DEFINITIVAS
# ==========================================
TELEGRAM_BOT_TOKEN = "8353706833:AAEx... (seu token se necessário)"  # Mantenha os seus do Telegram
TELEGRAM_CHAT_ID = "-1004406728710"
FB_PAGE_ID = "1214303865109377"
FB_PAGE_TOKEN = "EAAPFihJ9FJcBSXlCY8NHrjBgIddLj2fjMYC81P05TCduabZCZAS8sOTOAXGFC5WViZBoKw7VuL0sBCibDRJIG0HUVpUSYtIkUAxZCx7Gi6mqigDd3RI4QD6oEXtDlGKJGTfvDt7RJwSGaODZAQF2PpT1NYLCz0F1Jd3ZAQZCBB8GudUGsKCTRGRwHFsQVbVZCDQt65yMnQ3HTublKjVfcCeig9mBALbutKvZCokwlhuv82GlewG7WMEUowAZDZD"
IMGBB_API_KEY = "82c69b4736c7793eaab429880014d06c"

# Instagram Business Account ID (caso descubra o número exato depois, basta substituir aqui)
# Se o ID exato não estiver mapeado via API Graph, o código tentará buscar automaticamente pela Página do Facebook.
INSTAGRAM_BUSINESS_ID = "1759076875129450"


st.title("🚀 Painel de Automação de Ofertas - PromoMania")

# Campos de entrada no Streamlit
legenda = st.text_area("Legenda da Oferta:", "Confira essa super oferta imperdível! 🔥")
imagem_url = st.text_input(
    "URL da Imagem:",
    "https://i.ibb.co/exemplo/produto.jpg",
)

if st.button("Publicar em Redes Sociais"):
  with st.spinner("Enviando publicações..."):

    # 1. TESTE / ENVIO FACEBOOK
    try:
      fb_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
      fb_payload = {
          "url": imagem_url,
          "caption": legenda,
          "access_token": FB_PAGE_TOKEN,
      }
      resp_fb = requests.post(fb_url, data=fb_payload, timeout=15)
      if resp_fb.status_code == 200:
        st.success("✅ Publicado com sucesso no Facebook!")
      else:
        st.error(f"Erro no Facebook: {resp_fb.text}")
    except Exception as e:
      st.error(f"Erro de conexão com o Facebook: {e}")

    # 2. TESTE / ENVIO INSTAGRAM
    try:
      # Criação do Container de Mídia exigido pela Graph API do Instagram
      ig_container_url = (
          f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media"
      )
      ig_payload = {
          "image_url": imagem_url,
          "caption": legenda,
          "access_token": FB_PAGE_TOKEN,
      }
      resp_container = requests.post(
          ig_container_url, data=ig_payload, timeout=15
      )
      container_data = resp_container.json()

      if "id" in container_data:
        creation_id = container_data["id"]

        # Publicação do Container criado
        ig_publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": FB_PAGE_TOKEN,
        }
        resp_publish = requests.post(
            ig_publish_url, data=publish_payload, timeout=15
        )

        if resp_publish.status_code == 200:
          st.success("✅ Publicado com sucesso no Instagram!")
        else:
          st.error(f"Erro ao publicar container no Instagram: {resp_publish.text}")
      else:
        st.error(f"Erro ao criar container no Instagram: {container_data}")
    except Exception as e:
      st.error(f"Erro de conexão com o Instagram: {e}")

    # 3. TESTE / ENVIO TELEGRAM
    try:
      tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
      tg_payload = {
          "chat_id": TELEGRAM_CHAT_ID,
          "photo": imagem_url,
          "caption": legenda,
          "parse_mode": "Markdown",
      }
      resp_tg = requests.post(tg_url, data=tg_payload, timeout=15)
      if resp_tg.status_code == 200:
        st.success("✅ Publicado com sucesso no Telegram!")
      else:
        st.error(f"Erro no Telegram: {resp_tg.text}")
    except Exception as e:
      st.error(f"Erro de conexão com o Telegram: {e}")                  
