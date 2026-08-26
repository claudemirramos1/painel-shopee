import io, json, urllib.parse, requests, streamlit as st
from PIL import Image, ImageEnhance, ImageOps

# Configurações
FB_PAGE_ID = "1214303865109377"
FB_PAGE_TOKEN = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"
TG_TOKEN = "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04"
TG_CHAT_ID = "-1004406728710"

st.set_page_config(page_title="Painel de Ofertas", page_icon="🛍️", layout="wide")
st.title("🛍️ Painel de Automação de Ofertas")

def processar_imagem(img_upload, melhoria=True, modo="Manter Proporção (Fundo Branco)", nitidez=1.8, contraste=1.15):
    try:
        img_upload.seek(0)
        img = Image.open(io.BytesIO(img_upload.getvalue()))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        
        img_a = ImageOps.pad(img, (1200, 1200), color=(255, 255, 255)) if modo == "Manter Proporção (Fundo Branco)" else img.copy()
        if modo != "Manter Proporção (Fundo Branco)": img_a.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        if melhoria:
            img_a = ImageEnhance.Sharpness(img_a).enhance(nitidez)
            img_a = ImageEnhance.Contrast(img_a).enhance(contraste)
            
        buf = io.BytesIO()
        img_a.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        buf.name = getattr(img_upload, "name", "foto.jpg")
        return buf
    except Exception as e:
        st.warning(f"Erro na imagem: {e}")
        return None

def postar_telegram(texto, imagens, melhoria, modo, nitidez, contraste):
    try:
        imgs = [processar_imagem(i, melhoria, modo, nitidez, contraste) for i in (imagens or []) if i]
        imgs = [i for i in imgs if i]
        if not imgs:
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT_ID, "text": texto, "parse_mode": "HTML"}, timeout=15).json()
            return res.get("ok"), res.get("description", "Sucesso")
        elif len(imgs) == 1:
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": texto, "parse_mode": "HTML"}, files={"photo": (imgs[0].name, imgs[0].getvalue(), "image/jpeg")}, timeout=30).json()
            return res.get("ok"), res.get("description", "Sucesso")
        else:
            media = [{"type": "photo", "media": f"attach://photo_{i}", **({"caption": texto, "parse_mode": "HTML"} if i==0 else {})} for i in range(len(imgs))]
            files = {f"photo_{i}": (f"f_{i}.jpg", img.getvalue(), "image/jpeg") for i, img in enumerate(imgs)}
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMediaGroup", data={"chat_id": TG_CHAT_ID, "media": json.dumps(media)}, files=files, timeout=60).json()
            return res.get("ok"), res.get("description", "Sucesso")
    except Exception as e: return False, str(e)

def postar_facebook(texto, imagens, link, melhoria, modo, nitidez, contraste):
    try:
        legenda = texto.replace("<b>", "*").replace("</b>", "*").replace("<code>", "").replace("</code>", "")
        imgs = [processar_imagem(i, melhoria, modo, nitidez, contraste) for i in (imagens or []) if i]
        imgs = [i for i in imgs if i]
        
        if not imgs:
            payload = {"message": legenda, "access_token": FB_PAGE_TOKEN, "link": link or ""}
            res = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/feed", data=payload, timeout=20).json()
            return ("id" in res or "post_id" in res), res.get("error", {}).get("message", "Sucesso")
        elif len(imgs) == 1:
            payload = {"caption": legenda, "access_token": FB_PAGE_TOKEN, "link": link or ""}
            res = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/photos", data=payload, files={"source": (imgs[0].name, imgs[0].getvalue(), "image/jpeg")}, timeout=40).json()
            return ("id" in res or "post_id" in res), res.get("error", {}).get("message", "Sucesso")
        else:
            media_ids = []
            for idx, img in enumerate(imgs):
                r = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/photos", data={"published": "false", "access_token": FB_PAGE_TOKEN}, files={"source": (f"f_{idx}.jpg", img.getvalue(), "image/jpeg")}, timeout=40).json()
                if "id" in r: media_ids.append({"media_fbid": r["id"]})
            payload = {"message": legenda, "attached_media": json.dumps(media_ids), "access_token": FB_PAGE_TOKEN, "link": link or ""}
            res = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/feed", data=payload, timeout=60).json()
            return ("id" in res or "post_id" in res), res.get("error", {}).get("message", "Sucesso")
    except Exception as e: return False, str(e)

tab_prod, tab_cupom = st.tabs(["📦 Oferta de Produto", "🎟️ Divulgação de Cupom"])

with tab_prod:
    c1, c2 = st.columns(2)
    titulo_p = c1.text_input("Título do Produto")
    link_p = c2.text_input("Link da Oferta")
    preco_de = c1.text_input("Preço De (R$)")
    preco_por = c2.text_input("Preço Por (R$)")
    cupom_p = c1.text_input("Cupom (Opcional)")
    obs_p = c2.text_area("Observações", height=68)
    imgs_p = st.file_uploader("📸 Fotos do Produto", type=["jpg","png","webp"], accept_multiple_files=True, key="up_p")

    p_html, p_wpp = [], []
    if titulo_p: p_html.append(f"🔥 <b>{titulo_p}</b>"); p_wpp.append(f"🔥 *{titulo_p}*")
    if preco_de: p_html.append(f"❌ De: R$ {preco_de}"); p_wpp.append(f"❌ De: R$ {preco_de}")
    if preco_por: p_html.append(f"✅ <b>Por: R$ {preco_por}</b>"); p_wpp.append(f"✅ *Por: R$ {preco_por}*")
    if cupom_p: p_html.append(f"🎟️ Cupom: <code>{cupom_p}</code>"); p_wpp.append(f"🎟️ Cupom: {cupom_p}")
    if obs_p: p_html.append(f"ℹ️ {obs_p}"); p_wpp.append(f"ℹ️ {obs_p}")
    if link_p: p_html.append(f"🛒 <b>Compre Aqui:</b> {link_p}"); p_wpp.append(f"🛒 *Compre Aqui:* {link_p}")
    
    txt_p_html, txt_p_wpp = "\n\n".join(p_html), "\n\n".join(p_wpp)

with tab_cupom:
    c1, c2 = st.columns(2)
    titulo_c = c1.text_input("Título / Loja")
    regras_c = c1.text_input("Regra do Desconto")
    cod_c = c1.text_input("Código do Cupom")
    link_c = c1.text_input("Link do Cupom")
    carrinho = c2.text_input("Exemplo - Carrinho (R$)")
    pagar = c2.text_input("Exemplo - Pagar (R$)")
    imgs_c = st.file_uploader("📸 Banner Cupom", type=["jpg","png","webp"], accept_multiple_files=True, key="up_c")

    ch, cw = [], []
    if titulo_c: ch.append(f"🔥 <b>{titulo_c}</b> 🔥"); cw.append(f"🔥 *{titulo_c}* 🔥")
    if regras_c: ch.append(f"⚡ {regras_c}"); cw.append(f"⚡ {regras_c}")
    ex_h, ex_w = [], []
    if carrinho: ex_h.append(f"🛒 Adicione R$ {carrinho} no carrinho"); ex_w.append(f"🛒 Adicione R$ {carrinho} no carrinho")
    if cod_c: ex_h.append(f"🎟️ {cod_c}"); ex_w.append(f"🎟️ {cod_c}")
    if pagar: ex_h.append(f"💰 <b>Pague apenas R$ {pagar}!</b>"); ex_w.append(f"💰 *Pague apenas R$ {pagar}!*")
    if ex_h: ch.append("💡 <b>Exemplo:</b>\n" + "\n".join(ex_h)); cw.append("💡 *Exemplo:*\n" + "\n".join(ex_w))
    if link_c: ch.append(f"👉 <b>Pegue aqui:</b> {link_c}"); cw.append(f"👉 *Pegue aqui:* {link_c}")

    txt_c_html, txt_c_wpp = "\n\n".join(ch), "\n\n".join(cw)

st.markdown("---")
env_tg = st.checkbox("📢 Postar no Telegram", value=True)
env_fb = st.checkbox("📘 Postar no Facebook", value=True)

with st.expander("🎨 Ajuste de Imagem"):
    modo_r = st.radio("Modo:", ["Manter Proporção (Fundo Branco)", "Apenas Reduzir"])
    melhorar = st.checkbox("Melhorar Imagem", value=True)
    nit, cont = st.slider("Nitidez", 1.0, 3.0, 1.8), st.slider("Contraste", 1.0, 2.0, 1.15)

is_cupom = bool(titulo_c or link_c)
txt_html = txt_c_html if is_cupom else txt_p_html
txt_wpp = txt_c_wpp if is_cupom else txt_p_wpp
link_envio = link_c if is_cupom else link_p
imgs_envio = imgs_c if is_cupom else imgs_p
valid_tit = titulo_c if is_cupom else titulo_p

col_b1, col_b2 = st.columns([2, 1])
with col_b1:
    if st.button("🚀 Postar Oferta", type="primary", use_container_width=True):
        if not (env_tg or env_fb): st.warning("Selecione um canal.")
        elif not valid_tit and not link_envio: st.warning("Preencha o Título e o Link.")
        else:
            if env_fb:
                ok, msg = postar_facebook(txt_html, imgs_envio, link_envio, melhorar, modo_r, nit, cont)
                st.success(f"FB: {msg}") if ok else st.error(f"FB: {msg}")
            if env_tg:
                ok, msg = postar_telegram(txt_html, imgs_envio, melhorar, modo_r, nit, cont)
                st.success(f"TG: {msg}") if ok else st.error(f"TG: {msg}")

with col_b2:
    wpp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(txt_wpp)}"
    st.markdown(f'<a href="{wpp_url}" target="_blank" style="text-decoration:none;"><div style="background:#25D366;color:white;padding:10px;text-align:center;border-radius:8px;font-weight:bold;">🟢 Compartilhar WhatsApp</div></a>', unsafe_allow_html=True)      
