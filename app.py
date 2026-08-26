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
# PROCESSAMENTO E MELHORIA DE FOTO (SEM DISTORÇÃO)
# ==========================================
def processar_imagem_segura(
    imagem_upload,
    aplicar_melhoria=True,
    modo_redimensionar="Manter Proporção (Fundo Branco)",
    max_dim=1200,
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

    # Tratamento para NÃO DISTORCER
    if modo_redimensionar == "Manter Proporção (Fundo Branco)":
      # Adiciona margem/fundo branco proporcional sem esticar a imagem
      target_size = (max_dim, max_dim)
      img_ajustada = ImageOps.pad(
          img, target_size, color=(255, 255, 255), centering=(0.5, 0.5)
      )
    else:
      # Apenas redimensiona proporcionalmente mantendo formato original
      img_ajustada = img.copy()
      img_ajustada.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

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
    token,
    chat_id,
    texto,
    lista_imagens,
    aplicar_melhoria,
    modo_redim,
    nitidez,
    contraste,
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
            modo_redimensionar=modo_redim,
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
    modo_redim,
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
            modo_redimensionar=modo_redim,
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
# DIVISÃO POR ABAS (PRODUTO E CUPOM)
# ==========================================
tab_produto, tab_cupom = st.tabs(
    ["📦 Oferta de Produto", "🎟️ Divulgação de Cupom"]
)

texto_gerado_html = ""
texto_wpp = ""
link_oferta_envio = ""
imagens_envio = []
titulo_validacao = ""

# ------------------------------------------
# ABA 1: PRODUTO
# ------------------------------------------
with tab_produto:
  st.subheader("📝 Preencher Dados da Oferta de Produto")

  if "preco_por_val" not in st.session_state:
    st.session_state.preco_por_val = ""
  if "obs_val" not in st.session_state:
    st.session_state.obs_val = ""

  col1_left, col1_right = st.columns(2)
  with col1_left:
    titulo_produto = st.text_input(
        "Título do Produto", placeholder='Ex: Smart TV 55" 4K'
    )
  with col1_right:
    link_afiliado = st.text_input(
        "Link da Oferta / Afiliado", placeholder="https://..."
    )

  col2_left, col2_right = st.columns(2)
  with col2_left:
    preco_de = st.text_input("Preço De (R$)", placeholder="Ex: 1000")
  with col2_right:
    preco_por = st.text_input(
        "Preço Por (R$)",
        value=st.session_state.preco_por_val,
        placeholder="Ex: 800",
    )

  col3_left, col3_right = st.columns(2)

  with col3_left:
    st.caption("⚡ Cálculo Rápido de Desconto:")
    cd1, cd2, cd3, cd4, cd5 = st.columns(5)

    def aplicar_desconto(pct):
      try:
        val_de = float(
            preco_de.replace(".", "")
            .replace(",", ".")
            .replace("R$", "")
            .strip()
        )
        val_por = val_de * (1 - pct / 100)
        st.session_state.preco_por_val = f"{val_por:.2f}".replace(".", ",")
      except ValueError:
        st.warning("Preencha o 'Preço De' primeiro.")

    if cd1.button("5%", key="btn_5"):
      aplicar_desconto(5)
    if cd2.button("10%", key="btn_10"):
      aplicar_desconto(10)
    if cd3.button("25%", key="btn_25"):
      aplicar_desconto(25)
    if cd4.button("50%", key="btn_50"):
      aplicar_desconto(50)
    if cd5.button("Limpar", key="btn_limpar_desc"):
      st.session_state.preco_por_val = ""

  with col3_right:
    st.caption("📌 Etiquetas Rápida:")
    ct1, ct2, ct3 = st.columns(3)

    def adicionar_tag(tag_texto):
      if tag_texto not in st.session_state.obs_val:
        if st.session_state.obs_val.strip():
          st.session_state.obs_val += f" | {tag_texto}"
        else:
          st.session_state.obs_val = tag_texto

    if ct1.button("🚚 Frete Grátis", key="btn_frete"):
      adicionar_tag("🚚 Frete Grátis")
    if ct2.button("⚡ Relâmpago", key="btn_relampago"):
      adicionar_tag("⚡ Oferta Relâmpago")
    if ct3.button("⭐ Do Dia", key="btn_dodia"):
      adicionar_tag("⭐ Oferta do Dia")

  col4_left, col4_right = st.columns(2)
  with col4_left:
    cupom = st.text_input(
        "Cupom de Desconto (Opcional)", placeholder="Ex: DESCONTO10"
    )
  with col4_right:
    descricao_extra = st.text_area(
        "Observações (Opcional)", value=st.session_state.obs_val, height=68
    )

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

  # Montagem limpa do texto
  partes_html = []
  partes_wpp = []

  if titulo_produto:
    partes_html.append(f"🔥 <b>{titulo_produto.strip()}</b>")
    partes_wpp.append(f"🔥 *{titulo_produto.strip()}*")

  if preco_de:
    partes_html.append(f"❌ De: R$ {preco_de.strip()}")
    partes_wpp.append(f"❌ De: R$ {preco_de.strip()}")

  if preco_por:
    partes_html.append(f"✅ <b>Por: R$ {preco_por.strip()}</b>")
    partes_wpp.append(f"✅ *Por: R$ {preco_por.strip()}*")

  if cupom:
    partes_html.append(f"🎟️ Cupom: <code>{cupom.strip()}</code>")
    partes_wpp.append(f"🎟️ Cupom: {cupom.strip()}")

  if descricao_extra:
    partes_html.append(f"ℹ️ {descricao_extra.strip()}")
    partes_wpp.append(f"ℹ️ {descricao_extra.strip()}")

  if link_afiliado:
    partes_html.append(f"🛒 <b>Compre Aqui:</b> {link_afiliado.strip()}")
    partes_wpp.append(f"🛒 *Compre Aqui:* {link_afiliado.strip()}")

  texto_gerado_html = "\n\n".join(partes_html)
  texto_wpp = "\n\n".join(partes_wpp)

  link_oferta_envio = link_afiliado
  imagens_envio = imagens_upload
  titulo_validacao = titulo_produto

# ------------------------------------------
# ABA 2: DIVULGAÇÃO DE CUPOM EXCLUSIVO
# ------------------------------------------
texto_cupom_html = ""
texto_cupom_wpp = ""
titulo_cupom = ""
link_cupom = ""
imagens_upload_cupom = []

with tab_cupom:
  st.subheader("🎟️ Gerador de Oferta de Cupom")

  col_c1, col_c2 = st.columns(2)
  with col_c1:
    titulo_cupom = st.text_input(
        "Título da Promoção / Loja",
        placeholder="Ex: CUPOM EXCLUSIVO FOREVER LISS NA SHOPEE!",
    )
    regras_cupom = st.text_input(
        "Regra do Desconto",
        placeholder="Ex: 15% OFF em compras acima de R$ 130",
    )
    codigo_cupom_loja = st.text_input(
        "Código do Cupom / Instrução",
        placeholder="Ex: Aplique o cupom da loja",
    )
    link_cupom = st.text_input(
        "Link do Cupom / Afiliado", placeholder="https://...", key="link_cupom"
    )

  with col_c2:
    st.markdown("### 🧮 Exemplo Prático de Economia")

    carrinho_exemplo = st.text_input(
        "Exemplo - Valor Carrinho (R$)", placeholder="Ex: 130"
    )

    porcentagem_cupom = st.text_input(
        "Desconto em Porcentagem (%)", placeholder="Ex: 15"
    )

    # Cálculo Automático
    pagar_calculado = ""
    if carrinho_exemplo and porcentagem_cupom:
      try:
        val_carrinho = float(
            carrinho_exemplo.replace(".", "").replace(",", ".").strip()
        )
        val_pct = float(
            porcentagem_cupom.replace("%", "").replace(",", ".").strip()
        )
        val_final = val_carrinho * (1 - val_pct / 100)
        pagar_calculado = f"{val_final:.2f}".replace(".", ",")
      except ValueError:
        pass

    pagar_exemplo = st.text_input(
        "Exemplo - Valor Final a Pagar (R$)",
        value=pagar_calculado,
        placeholder="Ex: 110,50",
    )

  imagens_upload_cupom = st.file_uploader(
      "📸 Selecionar Banner/Imagem do Cupom (Opcional)",
      type=["jpg", "jpeg", "png", "webp"],
      accept_multiple_files=True,
      key="uploader_fotos_cupom",
  )

  # Construção Condicional do Texto do Cupom (Só inclui o que for preenchido)
  p_html = []
  p_wpp = []

  if titulo_cupom.strip():
    p_html.append(f"🔥 <b>{titulo_cupom.strip()}</b> 🔥")
    p_wpp.append(f"🔥 *{titulo_cupom.strip()}* 🔥")

  if regras_cupom.strip():
    p_html.append(f"⚡ {regras_cupom.strip()}")
    p_wpp.append(f"⚡ {regras_cupom.strip()}")

  # Bloco de Exemplo de Economia
  bloco_ex_html = []
  bloco_ex_wpp = []

  if carrinho_exemplo.strip():
    bloco_ex_html.append(
        f"🛒 Adicione R$ {carrinho_exemplo.strip()} em produtos no carrinho"
    )
    bloco_ex_wpp.append(
        f"🛒 Adicione R$ {carrinho_exemplo.strip()} em produtos no carrinho"
    )

  if codigo_cupom_loja.strip():
    bloco_ex_html.append(f"🎟️ {codigo_cupom_loja.strip()}")
    bloco_ex_wpp.append(f"🎟️ {codigo_cupom_loja.strip()}")

  if pagar_exemplo.strip():
    bloco_ex_html.append(f"💰 <b>Pague apenas R$ {pagar_exemplo.strip()}!</b>")
    bloco_ex_wpp.append(f"💰 *Pague apenas R$ {pagar_exemplo.strip()}!*")

  if bloco_ex_html:
    p_html.append("💡 <b>Exemplo de economia:</b>\n" + "\n".join(bloco_ex_html))
    p_wpp.append("💡 *Exemplo de economia:*\n" + "\n".join(bloco_ex_wpp))

  if link_cupom.strip():
    p_html.append(
        f"👉 <b>Pegue o cupom e aproveite aqui:</b> {link_cupom.strip()}"
    )
    p_wpp.append(f"👉 *Pegue o cupom e aproveite aqui:* {link_cupom.strip()}")

  texto_cupom_html = "\n\n".join(p_html)
  texto_cupom_wpp = "\n\n".join(p_wpp)

  st.markdown("---")
  st.caption("👁️ **Pré-visualização do Texto Gerado:**")
  st.code(
      texto_cupom_wpp.replace("*", "").replace("<b>", "").replace("</b>", "")
  )

# ==========================================
# SEÇÃO COMUM DE ENVIO E REDES SOCIAIS
# ==========================================
st.markdown("---")
st.subheader("🎯 Onde deseja postar?")
col_chk1, col_chk2 = st.columns(2)
with col_chk1:
  enviar_telegram = st.checkbox(
      "📢 Postar no Telegram", value=True, key="chk_tg"
  )
with col_chk2:
  enviar_facebook = st.checkbox(
      "📘 Postar no Facebook", value=True, key="chk_fb"
  )

# ==========================================
# OPÇÕES DE REDIMENSIONAMENTO E MELHORIA
# ==========================================
with st.expander("🎨 Configurações de Imagem (Ajuste sem Distorcer)"):
  modo_redim = st.radio(
      "Modo de Ajuste de Imagem:",
      [
          "Manter Proporção (Fundo Branco)",
          "Manter Formato Original (Apenas Reduzir)",
      ],
      index=0,
  )

  aplicar_melhoria = st.checkbox(
      "Ativar Nitidez + Contraste", value=True, key="chk_melhoria"
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
        key="sld_nitidez",
    )
  with c_melh2:
    val_contraste = st.slider(
        "Nível de Contraste",
        min_value=1.0,
        max_value=2.0,
        value=1.15,
        step=0.05,
        disabled=not aplicar_melhoria,
        key="sld_contraste",
    )

st.markdown("---")

col_btn1, col_btn2 = st.columns([2, 1])

# Seleção automática de qual aba o usuário está usando
usar_cupom = bool(titulo_cupom or link_cupom)

texto_final_html = texto_cupom_html if usar_cupom else texto_gerado_html
texto_final_wpp = texto_cupom_wpp if usar_cupom else texto_wpp
link_final_envio = link_cupom if usar_cupom else link_oferta_envio
imagens_final_envio = (
    imagens_upload_cupom if usar_cupom else imagens_envio
)
validacao_titulo = titulo_cupom if usar_cupom else titulo_validacao

with col_btn1:
  if st.button(
      "🚀 Postar Oferta nos Canais Selecionados",
      type="primary",
      use_container_width=True,
      key="btn_postar_geral",
  ):
    if not enviar_telegram and not enviar_facebook:
      st.warning("Selecione ao menos um canal (Telegram ou Facebook).")
    elif not 
