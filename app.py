import io
import json
from PIL import Image, ImageEnhance, ImageOps
import requests
import streamlit as st

# ==========================================
# CONFIGURAÇÕES FIXAS
# ==========================================
FB_PAGE_ID_FIXO = "1214303865109377"
FB_PAGE_TOKEN_FIXO = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

TELEGRAM_BOT_TOKEN_FIXO = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TELEGRAM_CHAT_ID_FIXO = "-1004406728710"

st.set_page_config(
    page_title="Painel de Ofertas & Redes Sociais", page_icon="🛍️", layout="wide"
)

st.title(
    "🛍️ Painel de Automação de Ofertas com Múltiplas Fotos & Alta Resolução"
)


# ==========================================
# PROCESSAMENTO DE IMAGEM VIA BUFFER SEGURO
# ==========================================
def processar_imagem_segura(imagem_upload, target_size=(1080, 1350)):
  """Lê os bytes da foto em um buffer em memória para não perder a referência no Streamlit."""
  try:
    bytes_data = imagem_upload.getvalue()
    input_buffer = io.BytesIO(bytes_data)

    img = Image.open(input_buffer)
    if img.mode in ("RGBA", "P"):
      img = img.convert("RGB")

    img_ajustada = ImageOps.fit(
        img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
    )

    enhancer_sharpness = ImageEnhance.Sharpness(img_ajustada)
    img_nitida = enhancer_sharpness.enhance(1.8)

    enhancer_contrast = ImageEnhance.Contrast(img_nitida)
    img_final = enhancer_contrast.enhance(1.15)

    output_buffer = io.BytesIO()
    img_final.save(output_buffer, format="JPEG", quality=92)
    output_buffer.seek(0)

    output_buffer.name = getattr(imagem_upload, "name", "oferta_hd.jpg")
    output_buffer.type = "image/jpeg"
    return output_buffer
  except Exception as e:
    st.warning(
        f"Aviso no processamento da imagem {getattr(imagem_upload, 'name', '')}: {e}"
    )
    return None


# ==========================================
# ENVIO TELEGRAM (LOTE GARANTIDO)
# ==========================================
def postar_no_telegram(token, chat_id, texto, lista_imagens):
  if not token or not chat_id:
    return False, "Token ou Chat ID do Telegram não informados."
  try:
    imagens_processadas = []
    if lista_imagens:
      for img_raw in lista_imagens:
        proc = processar_imagem_segura(img_raw)
        if proc is not None:
          imagens_processadas.append(proc)

    if not imagens_processadas:
      url = f"https://api.telegram.org/bot{token}/sendMessage"
      data = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
      response = requests.post(url, data=data, timeout=15)
      res_data = response.json()
      return (
          (True, "Publicado no Telegram (apenas texto)!")
          if res_data.get("ok")
          else (False, f"Erro Telegram: {res_data.get('description')}")
      )

    elif len(imagens_processadas) == 1:
      img = imagens_processadas[0]
      url = f"https://api.telegram.org/bot{token}/sendPhoto"
      files = {"photo": (img.name, img.getvalue(), "image/jpeg")}
      data = {"chat_id": chat_id, "caption": texto, "parse_mode": "HTML"}
      response = requests.post(url, data=data, files=files, timeout=30)
      res_data = response.json()
      return (
          (True, "Publicado no Telegram com 1 foto!")
          if res_data.get("ok")
          else (False, f"Erro Telegram: {res_data.get('description')}")
      )

    else:
      url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
      media = []
      files = {}
      for idx, img in enumerate(imagens_processadas):
        file_key = f"photo_{idx}"
        files[file_key] = (f"foto_{idx}.jpg", img.getvalue(), "image/jpeg")
        item = {"type": "photo", "media": f"attach://{file_key}"}
        if idx == 0:
          item["caption"] = texto
          item["parse_mode"] = "HTML"
        media.append(item)

      data = {"chat_id": chat_id, "media": json.dumps(media)}
      response = requests.post(url, data=data, files=files, timeout=60)
      res_data = response.json()
      return (
          (
              True,
              (
                  f"Álbum com {len(imagens_processadas)} fotos publicado no"
                  " Telegram!"
              ),
          )
          if res_data.get("ok")
          else (False, f"Erro Telegram: {res_data.get('description')}")
      )

  except Exception as e:
    return False, f"Falha no Telegram: {str(e)}"


# ==========================================
# ENVIO FACEBOOK (MULTIPLICIDADE / CARROSSEL)
# ==========================================
def postar_no_facebook(
    page_id, page_token, texto_fb, lista_imagens, link_oferta=None
):
  if not page_id or not page_token:
    return False, "ID da Página ou Token de Acesso do FB não informados."
  try:
    legenda_limpa = (
        texto_fb.replace("<b>", "")
        .replace("</b>", "")
        .replace("<code>", "")
        .replace("</code>", "")
    )

    imagens_processadas = []
    if lista_imagens:
      for img_raw in lista_imagens:
        proc = processar_imagem_segura(img_raw)
        if proc is not None:
          imagens_processadas.append(proc)

    if not imagens_processadas:
      url = f"https://graph.facebook.com/v26.0/{page_id}/feed"
      payload = {"message": legenda_limpa, "access_token": page_token}
      if link_oferta and link_oferta.strip():
        payload["link"] = link_oferta.strip()
      response = requests.post(url, data=payload, timeout=20)
      res_data = response.json()
      return (
          (True, "Publicado no Facebook (sem fotos)!")
          if ("id" in res_data or "post_id" in res_data)
          else (
              False,
              f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}",
          )
      )

    elif len(imagens_processadas) == 1:
      img = imagens_processadas[0]
      url = f"https://graph.facebook.com/v26.0/{page_id}/photos"
      files = {"source": (img.name, img.getvalue(), "image/jpeg")}
      payload = {"caption": legenda_limpa, "access_token": page_token}
      if link_oferta and link_oferta.strip():
        payload["link"] = link_oferta.strip()
      response = requests.post(url, data=payload, files=files, timeout=40)
      res_data = response.json()
      return (
          (True, "Publicado no Facebook com 1 foto!")
          if ("id" in res_data or "post_id" in res_data)
          else (
              False,
              f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}",
          )
      )

    else:
      attached_media_list = []
      for idx, img in enumerate(imagens_processadas):
        url_upload = f"https://graph.facebook.com/v26.0/{page_id}/photos"
        files = {"source": (f"foto_{idx}.jpg", img.getvalue(), "image/jpeg")}
        payload_upload = {"published": "false", "access_token": page_token}
        resp_upload = requests.post(
            url_upload, data=payload_upload, files=files, timeout=40
        )
        data_upload = resp_upload.json()
        if "id" in data_upload:
          attached_media_list.append({"media_fbid": data_upload["id"]})
        else:
          return (
              False,
              f"Erro ao subir foto #{idx+1} para o carrossel FB:"
              f" {data_upload.get('error', {}).get('message', 'Erro')}",
          )

      url_feed = f"https://graph.facebook.com/v26.0/{page_id}/feed"
      payload_feed = {
          "message": legenda_limpa,
          "attached_media": json.dumps(attached_media_list),
          "access_token": page_token,
      }
      if link_oferta and link_oferta.strip():
        payload_feed["link"] = link_oferta.strip()

      response = requests.post(url_feed, data=payload_feed, timeout=60)
      res_data = response.json()
      return (
          (
              True,
              (
                  f"Publicado no Facebook com {len(attached_media_list)} fotos"
                  " em alta resolução!"
              ),
          )
          if ("id" in res_data or "post_id" in res_data)
          else (
              False,
              f"Erro Facebook: {res_data.get('error', {}).get('message', 'Erro')}",
          )
      )

  except Exception as e:
    return False, f"Falha no Facebook: {str(e)}"


# ==========================================
# INTERFACE DA APLICAÇÃO (COM SESSION STATE FIX)
# ==========================================
st.subheader("📝 Preencher Dados da Oferta")
col1, col2 = st.columns([1, 1])

with col1:
  titulo_produto = st.text_input(
      "Título do Produto", placeholder='Ex: Smart TV 55" 4K'
  )
  preco_de = st.text_input("Preço De (R$)", placeholder="Ex: 1000")
  preco_por = st.text_input("Preço Por (R$)", placeholder="Ex: 800")
  cupom = st.text_input("Cupom de Desconto (Opcional)", placeholder="Ex: DESCONTO10")

with col2:
  link_afiliado = st.text_input(
      "Link da Oferta / Afiliado", placeholder="https://..."
  )

  # FILE UPLOADER COM KEY E LIMITE CORRIGIDOS
  imagens_upload = st.file_uploader(
      "📸 Selecionar Imagens da Galeria",
      type=["jpg", "jpeg", "png", "webp"],
      accept_multiple_files=True,
      key="uploader_fotos_galeria",
      max_upload_size=500,
  )

  if imagens_upload:
    st.info(f"📷 {len(imagens_upload)} imagem(ns) selecionada(s)!")
    cols_img = st.columns(min(len(imagens_upload), 4))
    for idx, img_item in enumerate(imagens_upload):
      cols_img[idx % 4].image(
          img_item, caption=f"Foto {idx+1}", use_container_width=True
      )

descricao_extra = st.text_area("Observações (Opcional)", height=70)

# Montagem do texto final
texto_gerado = (
    f"🔥 <b>{titulo_produto if titulo_produto else 'OFERTA IMPERDÍVEL'}</b>\n\n"
)
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

if st.button(
    "🚀 Postar Oferta em Todos os Canais", type="primary", use_container_width=True
):
  if not titulo_produto and not link_afiliado:
    st.warning("Preencha ao menos o Título e o Link do produto.")
  else:
    st.info("Processando lote de imagens e enviando...")

    st_fb, msg_fb = postar_no_facebook(
        FB_PAGE_ID_FIXO,
        FB_PAGE_TOKEN_FIXO,
        texto_gerado,
        imagens_upload,
        link_afiliado,
    )
    if st_fb:
      st.success(f"✅ **Facebook:** {msg_fb}")
    else:
      st.error(f"❌ **Facebook:** {msg_fb}")

    st_tg, msg_tg = postar_no_telegram(
        TELEGRAM_BOT_TOKEN_FIXO,
        TELEGRAM_CHAT_ID_FIXO,
        texto_gerado,
        imagens_upload,
    )
    if st_tg:
      st.success(f"✅ **Telegram:** {msg_tg}")
    else:
      st.error(f"❌ **Telegram:** {msg_tg}")
