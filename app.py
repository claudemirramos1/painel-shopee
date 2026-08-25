import io
import json
import urllib.parse
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

st.title("🛍️ Painel de Automação de Ofertas")


# ==========================================
# PROCESSAMENTO E MELHORIA DE FOTO
# ==========================================
def processar_imagem_segura(
    imagem_upload,
    aplicar_melhoria=True,
    target_size=(1080, 1350),
    nitidez_val=1.8,
    contraste_val=1.15,
):
  try:
    imagem_upload.seek(0)
    bytes_data = imagem_upload.getvalue()
    input_buffer = io.BytesIO(bytes_data)

    img = Image.open(input_buffer)
    if img.mode in ("RGBA", "P"):
      img = img.convert("RGB")

    img_ajustada = ImageOps.fit(
        img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)
    )

    if aplicar_melhoria:
      enhancer_sharpness = ImageEnhance.Sharpness(img_ajustada)
      img_ajustada = enhancer_sharpness.enhance(nitidez_val)

      enhancer_contrast = ImageEnhance.Contrast(img_ajustada)
      img_ajustada = enhancer_contrast.enhance(contraste_val)

    output_buffer = io.BytesIO()
    img_ajustada.save(output_buffer, format="JPEG", quality=92)
    output_buffer.seek(0)

    nome_original = getattr(imagem_upload, "name", "oferta_hd.jpg")
    setattr(output_buffer, "name", nome_original)
    setattr(output_buffer, "type", "image/jpeg")
    return output_buffer
  except Exception as e:
    st.warning(
        f"Aviso no processamento da imagem {getattr(imagem_upload, 'name', '')}: {e}"
    )
    return None


# ==========================================
# ENVIO TELEGRAM
# ==========================================
def postar_no_telegram(
    token, chat_id, texto, lista_imagens, aplicar_melhoria, nitidez, contraste
):
  if not token or not chat_id:
    return False, "Token ou Chat ID do Telegram não informados."
  try:
    imagens_processadas = []
    if lista_imagens:
      for img_raw in lista_imagens:
        proc = processar_imagem_segura(
            img_raw,
            aplicar_melhoria=aplicar_melhoria,
            nitidez_val=nitidez,
            contraste_val=contraste,
        )
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
# ENVIO FACEBOOK
# ==========================================
def postar_no_facebook(
    page_id,
    page_token,
    texto_fb,
    lista_imagens,
    link_oferta,
    aplicar_melhoria,
    nitidez,
    contraste,
):
  if not page_id or not page_token:
    return False, "ID da Página ou Token de Acesso do FB não informados."
  try:
    legenda_limpa = (
        texto_fb.replace("<b>", "*")
        .replace("</b>", "*")
        .replace("<code>", "")
        .replace("</code>", "")
    )

    imagens_processadas = []
    if lista_imagens:
      for img_raw in lista_imagens:
        proc = processar_imagem_segura(
            img_raw,
            aplicar_melhoria=aplicar_melhoria,
            nitidez_val=nitidez,
            contraste_val=contraste,
        )
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
                  " em carrossel!"
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
# INTERFACE DA APLICAÇÃO (FORMULÁRIO ALINHADO)
# ==========================================
st.subheader("📝 Preencher Dados da Oferta")

if "preco_por_val" not in st.session_state:
  st.session_state.preco_por_val = ""
if "obs_val" not in st.session_state:
  st.session_state.obs_val = ""

# --- LINHA 1: TÍTULO E LINK ---
col1_left, col1_right = st.columns(2)
with col1_left:
  titulo_produto = st.text_input(
      "Título do Produto", placeholder='Ex: Smart TV 55" 4K'
  )
with col1_right:
  link_afiliado = st.text_input(
      "Link da Oferta / Afiliado", placeholder="https://..."
  )

# --- LINHA 2: PREÇO DE E PREÇO POR ---
col2_left, col2_right = st.columns(2)
with col2_left:
  preco_de = st.text_input("Preço De (R$)", placeholder="Ex: 1000")
with col2_right:
  preco_por = st.text_input(
      "Preço Por (R$)",
      value=st.session_state.preco_por_val,
      placeholder="Ex: 800",
  )

# --- LINHA 3: PAINEL DE BOTÕES RÁPIDOS LADO A LADO ---
col3_left, col3_right = st.columns(2)

# Esquerda: Descontos
with col3_left:
  st.caption("⚡ Cálculo Rápido de Desconto:")
  cd1, cd2, cd3, cd4, cd5 = st.columns(5)


  def aplicar_desconto(pct):
    try:
      val_de = float(
          preco_de.replace(".", "").replace(",", ".").replace("R$", "").strip()
      )
      val_por = val_de * (1 - pct / 100)
      st.session_state.preco_por_val = f"{val_por:.2f}".replace(".", ",")
    except ValueError:
      st.warning("Preencha o 'Preço De' primeiro.")


  if cd1.button("5%"):
    aplicar_desconto(5)
  if cd2.button("10%"):
    aplicar_desconto(10)
  if cd3.button("25%"):
    aplicar_desconto(25)
  if cd4.button("50%"):
    aplicar_desconto(50)
  if cd5.button("Limpar"):
    st.session_state.preco_por_val = ""

# Direita: Etiquetas
with col3_right:
  st.caption("📌 Etiquetas Rápida:")
  ct1, ct2, ct3 = st.columns(3)


  def adicionar_tag(tag_texto):
    if tag_texto not in st.session_state.obs_val:
      if st.session_state.obs_val.strip():
        st.session_state.obs_val += f" | {tag_texto}"
      else:
        st.session_state.obs_val = tag_texto


  if ct1.button("🚚 Frete Grátis"):
    adicionar_tag("🚚 Frete Grátis")
  if ct2.button("⚡ Relâmpago"):
    adicionar_tag("⚡ Oferta")
  if ct3.button("⭐ Do Dia"):
    adicionar_tag("⭐ Oferta do Dia")

# --- LINHA 4: CUPOM E OBSERVAÇÕES ---
col4_left, col4_right = st.columns(2)
with col4_left:
  cupom = st.text_input("Cupom de Desconto (Opcional)", placeholder="Ex: DESCONTO10")
with col4_right:
  descricao_extra = st.text_area(
      "Observações (Opcional)", value=st.session_state.obs_val, height=68
  )

# --- LINHA 5: UPLOAD DE FOTOS (LARGURA TOTAL) ---
imagens_upload = st.file_uploader(
    "📸 Selecionar Imagens da Galeria",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="uploader_fotos_galeria",
)

if imagens_upload:
  st.info(f"📷 {len(imagens_upload)} imagem(ns) selecionada(s)!")
  cols_img = st.columns(min(len(imagens_upload), 4))
  for idx, img_item in enumerate(imagens_upload):
    cols_img[idx % 4].image(
        img_item, caption=f"Foto {idx+1}", use_container_width=True
    )

st.markdown("---")

# ==========================================
# OPÇÕES DE CANAIS (MARCA TEXTO / CHECKBOXES)
# ==========================================
st.subheader("🎯 Onde deseja postar?")
col_chk1, col_chk2 = st.columns(2)
with col_chk1:
  enviar_telegram = st.checkbox("📢 Postar no Telegram", value=True)
with col_chk2:
  enviar_facebook = st.checkbox("📘 Postar no Facebook", value=True)

# ==========================================
# OPÇÕES DE MELHORIA DE FOTO
# ==========================================
with st.expander("🎨 Configurações de Melhoria de Foto"):
  aplicar_melhoria = st.checkbox(
      "Ativar Auto-Melhoria (Nitidez + Contraste)", value=True
  )
  c_melh1, c_melh2 = st.columns(2)
  with c_melh1:
    val_nitidez = st.slider(
        "Nível de Nitidez",
        min_value=1.0,
        max_value=3.0,
        value=1.8,
        step=0.1,
        disabled=not aplicar_melhoria,
    )
  with c_melh2:
    val_contraste = st.slider(
        "Nível de Contraste",
        min_value=1.0,
        max_value=2.0,
        value=1.15,
        step=0.05,
        disabled=not aplicar_melhoria,
    )

# Montagem dos textos
texto_gerado_html = (
    f"🔥 <b>{titulo_produto if titulo_produto else 'OFERTA IMPERDÍVEL'}</b>\n\n"
)
if preco_de:
  texto_gerado_html += f"❌ De: R$ {preco_de}\n"
if preco_por:
  texto_gerado_html += f"✅ <b>Por: R$ {preco_por}</b>\n"
if cupom:
  texto_gerado_html += f"🎟️ Cupom: <code>{cupom}</code>\n"
if descricao_extra:
  texto_gerado_html += f"\nℹ️ {descricao_extra}\n"
if link_afiliado:
  texto_gerado_html += f"\n🛒 <b>Compre Aqui:</b> {link_afiliado}"

# Texto formatado limpo para WhatsApp
texto_wpp = (
    f"🔥 *{titulo_produto if titulo_produto else 'OFERTA IMPERDÍVEL'}*\n\n"
)
if preco_de:
  texto_wpp += f"❌ De: R$ {preco_de}\n"
if preco_por:
  texto_wpp += f"✅ *Por: R$ {preco_por}*\n"
if cupom:
  texto_wpp += f"🎟️ Cupom: {cupom}\n"
if descricao_extra:
  texto_wpp += f"\nℹ️ {descricao_extra}\n"
if link_afiliado:
  texto_wpp += f"\n🛒 *Compre Aqui:* {link_afiliado}"

st.markdown("---")

col_btn1, col_btn2 = st.columns([2, 1])

with col_btn1:
  if st.button(
      "🚀 Postar Oferta nos Canais Selecionados",
      type="primary",
      use_container_width=True,
  ):
    if not enviar_telegram and not enviar_facebook:
      st.warning("Selecione ao menos um canal (Telegram ou Facebook).")
    elif not titulo_produto and not link_afiliado:
      st.warning("Preencha ao menos o Título e o Link do produto.")
    else:
      st.info("Processando lote de imagens e enviando...")

      if enviar_facebook:
        st_fb, msg_fb = postar_no_facebook(
            FB_PAGE_ID_FIXO,
            FB_PAGE_TOKEN_FIXO,
            texto_gerado_html,
            imagens_upload,
            link_afiliado,
            aplicar_melhoria,
            val_nitidez,
            val_contraste,
        )
        if st_fb:
          st.success(f"✅ **Facebook:** {msg_fb}")
        else:
          st.error(f"❌ **Facebook:** {msg_fb}")

      if enviar_telegram:
        st_tg, msg_tg = postar_no_telegram(
            TELEGRAM_BOT_TOKEN_FIXO,
            TELEGRAM_CHAT_ID_FIXO,
            texto_gerado_html,
            imagens_upload,
            aplicar_melhoria,
            val_nitidez,
            val_contraste,
        )
        if st_tg:
          st.success(f"✅ **Telegram:** {msg_tg}")
        else:
          st.error(f"❌ **Telegram:** {msg_tg}")

with col_btn2:
  # ==========================================
  # COMPARTILHAR NO WHATSAPP
  # ==========================================
  texto_encoded = urllib.parse.quote(texto_wpp)
  link_whatsapp = f"https://api.whatsapp.com/send?text={texto_encoded}"
  st.markdown(
      f"""
      <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
          <div style="
              background-color: #25D366;
              color: white;
              padding: 10px;
              text-align: center;
              border-radius: 8px;
              font-weight: bold;
              display: flex;
              align-items: center;
              justify-content: center;
              gap: 8px;">
              🟢 Compartilhar no WhatsApp
          </div>
      </a>
      """,
      unsafe_allow_html=True,
    )
