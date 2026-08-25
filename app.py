import os
import requests
import streamlit as st

# =====================================================================
# CONFIGURAÇÕES DE PÁGINA E CREDENCIAIS DEFINITIVAS
# =====================================================================
st.set_page_config(
    page_title="PromoMania - Painel de Automação de Ofertas",
    page_icon="🔥",
    layout="wide",
)

# Credenciais oficiais atualizadas
FB_PAGE_ID = "1214303865109377"
FB_PAGE_TOKEN = "EAAPFihJ9FJcBSXlCY8NHrjBgIddLj2fjMYC81P05TCduabZCZAS8sOTOAXGFC5WViZBoKw7VuL0sBCibDRJIG0HUVpUSYtIkUAxZCx7Gi6mqigDd3RI4QD6oEXtDlGKJGTfvDt7RJwSGaODZAQF2PpT1NYLCz0F1Jd3ZAQZCBB8GudUGsKCTRGRwHFsQVbVZCDQt65yMnQ3HTublKjVfcCeig9mBALbutKvZCokwlhuv82GlewG7WMEUowAZDZD"
INSTAGRAM_BUSINESS_ID = (
    "1759076875129450"  # ID atual do Instagram (ou substituto se necessário)
)

TELEGRAM_BOT_TOKEN = "8353706833:AAEx..."  # Insira seu token do Telegram aqui se usar
TELEGRAM_CHAT_ID = "-1004406728710"  # Insira o ID do seu chat/canal do Telegram
IMGBB_API_KEY = (
    "82c69b4736c7793eaab429880014d06c"  # Chave ImgBB para upload de imagens
)

# =====================================================================
# INTERFACE DO USUÁRIO (STREAMLIT)
# =====================================================================
st.title("🔥 PromoMania - Painel de Ofertas e Automação")
st.markdown(
    "Publique suas ofertas simultaneamente no **Facebook, Instagram e Telegram** com apenas um clique."
)

st.markdown("---")

# Layout em colunas para melhor organização visual
col1, col2 = st.columns([1, 1])

with col1:
  st.subheader("📝 Dados da Oferta")
  titulo_produto = st.text_input(
      "Nome do Produto:", "Ex: Smartphone Gamer em Promoção"
  )
  preco_antigo = st.text_input("Preço Antigo (R$):", "R$ 1.500,00")
  preco_novo = st.text_input("Preço Atual (R$):", "R$ 999,99")
  link_afiliado = st.text_input(
      "Link de Afiliado / Compra:", "https://suaurl.com/produto"
  )

  # Montagem automática da legenda padrão
  legenda_sugerida = (
      f"🔥 *{titulo_produto}* 🔥\n\n"
      f"De: ~{preco_antigo}~\n"
      f"Por apenas: *{preco_novo}* 💰\n\n"
      f"Run! Corre que vai acabar:\n🔗 {link_afiliado}\n\n"
      f"#promomaniofertas #ofertas #desconto #promocao"
  )

  legenda = st.text_area(
      "Legenda Final (Editável):", value=legenda_sugerida, height=200
  )

with col2:
  st.subheader("🖼️ Imagem do Produto")
  tipo_imagem = st.radio(
      "Como deseja inserir a imagem?",
      ["Colar URL da Imagem", "Fazer Upload do Computador"],
  )

  imagem_url_final = ""

  if tipo_imagem == "Colar URL da Imagem":
    imagem_url_final = st.text_input(
        "URL Direta da Imagem:", "https://i.ibb.co/exemplo/produto.jpg"
    )
  else:
    arquivo_upload = st.file_uploader(
        "Escolha a imagem (JPG/PNG)", type=["jpg", "jpeg", "png"]
    )
    if arquivo_upload is not None:
      st.image(
          arquivo_upload,
          caption="Pré-visualização da imagem",
          use_container_width=True,
      )
      # Envio automático para o ImgBB para gerar link público acessível pela Meta
      if st.button("Hospedar Imagem no ImgBB"):
        with st.spinner("Enviando imagem..."):
          try:
            url_imgbb = "https://api.imgbb.com/1/upload"
            payload = {"key": IMGBB_API_KEY}
            files = {"image": arquivo_upload.getvalue()}
            resp = requests.post(url_imgbb, data=payload, files=files, timeout=30)
            resultado_json = resp.json()
            if resultado_json.get("success"):
              imagem_url_final = resultado_json["data"]["url"]
              st.success(f"Imagem hospedada com sucesso!")
              st.code(imagem_url_final)
            else:
              st.error(f"Erro ao hospedar no ImgBB: {resultado_json}")
          except Exception as e:
            st.error(f"Erro de conexão com o ImgBB: {e}")

  # Campo caso o usuário já tenha o link direto do ImgBB gerado
  if tipo_imagem == "Fazer Upload do Computador":
    imagem_url_final = st.text_input(
        "Ou cole o link direto da imagem gerada:", value=imagem_url_final
    )

st.markdown("---")

# =====================================================================
# BOTÃO DE DISPARO DAS PUBLICAÇÕES
# =====================================================================
if st.button(
    "🚀 Publicar em Todas as Redes Agora",
    type="primary",
    use_container_width=True,
):
  if not imagem_url_final:
    st.warning("⚠️ Por favor, insira ou envie uma imagem válida antes de publicar.")
  else:
    with st.spinner("⏳ Processando publicações nas redes sociais..."):

      # 1. PUBLICAÇÃO NO FACEBOOK
      with st.expander("📘 Status do Facebook", expanded=True):
        try:
          fb_url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"
          fb_payload = {
              "url": imagem_url_final,
              "caption": legenda,
              "access_token": FB_PAGE_TOKEN,
          }
          resp_fb = requests.post(fb_url, data=fb_payload, timeout=20)
          if resp_fb.status_code == 200:
            st.success("✅ Publicado com sucesso no Facebook!")
          else:
            st.error(f"Erro no Facebook: {resp_fb.text}")
        except Exception as e:
          st.error(f"Erro de conexão com o Facebook: {e}")

      # 2. PUBLICAÇÃO NO INSTAGRAM
      with st.expander("📸 Status do Instagram", expanded=True):
        try:
          # Passo A: Criar Container de Mídia
          ig_container_url = (
              f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media"
          )
          ig_payload = {
              "image_url": imagem_url_final,
              "caption": legenda,
              "access_token": FB_PAGE_TOKEN,
          }
          resp_container = requests.post(
              ig_container_url, data=ig_payload, timeout=20
          )
          container_data = resp_container.json()

          if "id" in container_data:
            creation_id = container_data["id"]

            # Passo B: Publicar o Container criado
            ig_publish_url = f"https://graph.facebook.com/v18.0/{INSTAGRAM_BUSINESS_ID}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": FB_PAGE_TOKEN,
            }
            resp_publish = requests.post(
                ig_publish_url, data=publish_payload, timeout=20
            )

            if resp_publish.status_code == 200:
              st.success("✅ Publicado com sucesso no Instagram!")
            else:
              st.error(
                  f"Erro ao publicar container no Instagram:"
                  f" {resp_publish.text}"
              )
          else:
            st.error(f"Erro ao criar container no Instagram: {container_data}")
        except Exception as e:
          st.error(f"Erro de conexão com o Instagram: {e}")

      # 3. PUBLICAÇÃO NO TELEGRAM
      with st.expander("✈️ Status do Telegram", expanded=True):
        try:
          tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
          tg_payload = {
              "chat_id": TELEGRAM_CHAT_ID,
              "photo": imagem_url_final,
              "caption": legenda,
              "parse_mode": "Markdown",
          }
          resp_tg = requests.post(tg_url, data=tg_payload, timeout=20)
          if resp_tg.status_code == 200:
            st.success("✅ Publicado com sucesso no Telegram!")
          else:
            st.error(f"Erro no Telegram: {resp_tg.text}")
        except Exception as e:
          st.error(f"Erro de conexão com o Telegram: {e}")

    st.success(
        "🎉 Processo de publicação concluído! Verifique os status acima."
    )
