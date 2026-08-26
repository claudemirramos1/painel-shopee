import io, json, urllib.parse, requests, logging, streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageEnhance, ImageOps

# Suprime logs internos de requisições HTTP
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("requests").setLevel(logging.CRITICAL)

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
        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
        
        img_a = ImageOps.pad(img, (1200, 1200), color=(255, 255, 255)) if modo == "Manter Proporção (Fundo Branco)" else img.copy()
        if modo != "Manter Proporção (Fundo Branco)": 
            img_a.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        
        if melhoria:
            img_a = ImageEnhance.Sharpness(img_a).enhance(nitidez)
            img_a = ImageEnhance.Contrast(img_a).enhance(contraste)
            
        buf = io.BytesIO()
        img_a.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        buf.name = getattr(img_upload, "name", "foto.jpg")
        return buf
    except:
        return None

def postar_telegram(texto, imagens, melhoria, modo, nitidez, contraste):
    try:
        imgs = [processar_imagem(i, melhoria, modo, nitidez, contraste) for i in (imagens or []) if i]
        imgs = [i for i in imgs if i]
        if not imgs:
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT_ID, "text": texto, "parse_mode": "HTML"}, timeout=15).json()
            return res.get("ok"), "Sucesso!" if res.get("ok") else "Erro no envio."
        elif len(imgs) == 1:
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto", data={"chat_id": TG_CHAT_ID, "caption": texto, "parse_mode": "HTML"}, files={"photo": (imgs[0].name, imgs[0].getvalue(), "image/jpeg")}, timeout=30).json()
            return res.get("ok"), "Sucesso!" if res.get("ok") else "Erro no envio."
        else:
            media = [{"type": "photo", "media": f"attach://photo_{i}", **({"caption": texto, "parse_mode": "HTML"} if i==0 else {})} for i in range(len(imgs))]
            files = {f"photo_{i}": (f"f_{i}.jpg", img.getvalue(), "image/jpeg") for i, img in enumerate(imgs)}
            res = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMediaGroup", data={"chat_id": TG_CHAT_ID, "media": json.dumps(media)}, files=files, timeout=60).json()
            return res.get("ok"), "Sucesso!" if res.get("ok") else "Erro no envio."
    except:
        return False, "Erro de conexão."

def postar_facebook(texto, imagens, link, melhoria, modo, nitidez, contraste):
    try:
        legenda = texto.replace("<b>", "*").replace("</b>", "*").replace("<code>", "").replace("</code>", "")
        imgs = [processar_imagem(i, melhoria, modo, nitidez, contraste) for i in (imagens or []) if i]
        imgs = [i for i in imgs if i]
        
        if not imgs:
            payload = {"message": legenda, "access_token": FB_PAGE_TOKEN, "link": link or ""}
            res = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/feed", data=payload, timeout=20).json()
            return ("id" in res or "post_id" in res), "Sucesso!" if ("id" in res or "post_id" in res) else "Erro no envio."
        elif len(imgs) == 1:
            payload = {"caption": legenda, "access_token": FB_PAGE_TOKEN, "link": link or ""}
            res = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/photos", data=payload, files={"source": (imgs[0].name, imgs[0].getvalue(), "image/jpeg")}, timeout=40).json()
            return ("id" in res or "post_id" in res), "Sucesso!" if ("id" in res or "post_id" in res) else "Erro no envio."
        else:
            media_ids = []
            for idx, img in enumerate(imgs):
                r = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/photos", data={"published": "false", "access_token": FB_PAGE_TOKEN}, files={"source": (f"f_{idx}.jpg", img.getvalue(), "image/jpeg")}, timeout=40).json()
                if "id" in r: 
                    media_ids.append({"media_fbid": r["id"]})
            payload = {"message": legenda, "attached_media": json.dumps(media_ids), "access_token": FB_PAGE_TOKEN, "link": link or ""}
            res = requests.post(f"https://graph.facebook.com/v26.0/{FB_PAGE_ID}/feed", data=payload, timeout=60).json()
            return ("id" in res or "post_id" in res), "Sucesso!" if ("id" in res or "post_id" in res) else "Erro no envio."
    except:
        return False, "Erro de conexão."

# Configurações Globais
with st.expander("⚙️ Configurações de Envio e Imagem", expanded=True):
    c_redes1, c_redes2 = st.columns(2)
    env_tg = c_redes1.checkbox("📢 Postar no Telegram", value=True)
    env_fb = c_redes2.checkbox("📘 Postar no Facebook", value=True)
    
    c_img1, c_img2, c_img3 = st.columns(3)
    modo_r = c_img1.radio("Modo Imagem:", ["Manter Proporção (Fundo Branco)", "Apenas Reduzir"])
    melhorar = c_img2.checkbox("Melhorar Imagem", value=True)
    nit = c_img3.slider("Nitidez", 1.0, 3.0, 1.8)
    cont = c_img3.slider("Contraste", 1.0, 2.0, 1.15)

def executar_envio(txt_html, txt_wpp, imgs_fb, imgs_tg, link, titulo):
    if not (env_tg or env_fb): 
        st.warning("Selecione ao menos um canal de envio.")
        return
    if not titulo and not link: 
        st.warning("Preencha ao menos o Título e o Link.")
        return
        
    with st.spinner("Enviando..."):
        if env_fb:
            ok, msg = postar_facebook(txt_html, imgs_fb, link, melhorar, modo_r, nit, cont)
            if ok:
                st.success(f"Facebook: {msg}")
            else:
                st.error(f"Facebook: {msg}")
        if env_tg:
            ok, msg = postar_telegram(txt_html, imgs_tg, melhorar, modo_r, nit, cont)
            if ok:
                st.success(f"Telegram: {msg}")
            else:
                st.error(f"Telegram: {msg}")

tab_prod, tab_cupom = st.tabs(["📦 Oferta de Produto", "🎟️ Divulgação de Cupom"])

# ABA 1: PRODUTO
with tab_prod:
    c1, c2 = st.columns(2)
    titulo_p = c1.text_input("Título do Produto", key="tp")
    link_p = c2.text_input("Link da Oferta", key="lp")
    preco_de = c1.text_input("Preço De (R$)", key="pde")
    preco_por = c2.text_input("Preço Por (R$)", key="ppor")
    cupom_p = c1.text_input("Cupom (Opcional)", key="cp")
    obs_p = c2.text_area("Observações", height=68, key="obsp")
    imgs_p = st.file_uploader("📸 Fotos do Produto", type=["jpg","png","webp"], accept_multiple_files=True, key="up_p")

    col_img_fb_p, col_img_tg_p = st.columns(2)
    enviar_img_fb_p = col_img_fb_p.checkbox("🖼️ Enviar imagem para o Facebook", value=True, key="chk_img_fb_p")
    enviar_img_tg_p = col_img_tg_p.checkbox("🖼️ Enviar imagem para o Telegram", value=True, key="chk_img_tg_p")

    p_wpp_list = []
    if titulo_p: p_wpp_list.append(f"🔥 *{titulo_p}*")
    if preco_de: p_wpp_list.append(f"❌ De: R$ {preco_de}")
    if preco_por: p_wpp_list.append(f"✅ *Por: R$ {preco_por}*")
    if cupom_p: p_wpp_list.append(f"🎟️ Cupom: {cupom_p}")
    if obs_p: p_wpp_list.append(f"ℹ️ {obs_p}")
    if link_p: p_wpp_list.append(f"🛒 *Compre Aqui:* {link_p}")
    txt_p_wpp = "\n\n".join(p_wpp_list)

    st.markdown("---")
    cb1, cb2 = st.columns([2, 1])
    with cb1:
        if st.button("🚀 Postar PRODUTO nas Redes", type="primary", use_container_width=True, key="btn_p"):
            p_html_list = []
            if titulo_p: p_html_list.append(f"🔥 <b>{titulo_p}</b>")
            if preco_de: p_html_list.append(f"❌ De: R$ {preco_de}")
            if preco_por: p_html_list.append(f"✅ <b>Por: R$ {preco_por}</b>")
            if cupom_p: p_html_list.append(f"🎟️ Cupom: <code>{cupom_p}</code>")
            if obs_p: p_html_list.append(f"ℹ️ {obs_p}")
            if link_p: p_html_list.append(f"🛒 <b>Compre Aqui:</b> {link_p}")
            txt_p_html = "\n\n".join(p_html_list)
            
            imgs_fb = imgs_p if enviar_img_fb_p else None
            imgs_tg = imgs_p if enviar_img_tg_p else None

            executar_envio(txt_p_html, txt_p_wpp, imgs_fb, imgs_tg, link_p, titulo_p)
    with cb2:
        wpp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(txt_p_wpp)}"
        st.markdown(f'<a href="{wpp_url}" target="_blank" style="text-decoration:none;"><div style="background:#25D366;color:white;padding:10px;text-align:center;border-radius:8px;font-weight:bold;">🟢 WhatsApp Produto</div></a>', unsafe_allow_html=True)

# ABA 2: CUPOM
with tab_cupom:
    c1, c2 = st.columns(2)
    titulo_c = c1.text_input("Título / Loja", key="tc")
    pct_desc = c1.text_input("Desconto (%)", placeholder="Ex: 15", key="pctc")
    val_min = c1.text_input("Valor Mínimo Compras (R$)", placeholder="Ex: 130", key="minc")
    cod_c = c1.text_input("Código do Cupom", key="cc")
    link_c = c1.text_input("Link do Cupom", key="lc")
    imgs_c = st.file_uploader("📸 Banner Cupom", type=["jpg","png","webp"], accept_multiple_files=True, key="up_c")

    col_img_fb_c, col_img_tg_c = st.columns(2)
    enviar_img_fb_c = col_img_fb_c.checkbox("🖼️ Enviar imagem para o Facebook", value=True, key="chk_img_fb_c")
    enviar_img_tg_c = col_img_tg_c.checkbox("🖼️ Enviar imagem para o Telegram", value=True, key="chk_img_tg_c")

    regra_auto = ""
    pagar_calc = ""
    try:
        if pct_desc and val_min:
            p_val = float(pct_desc.replace("%", "").replace(",", "."))
            v_val = float(val_min.replace(".", "").replace(",", "."))
            regra_auto = f"{pct_desc}% OFF em compras acima de R$ {val_min}"
            res_pagar = v_val * (1 - (p_val / 100.0))
            pagar_calc = f"{res_pagar:.2f}".replace(".", ",")
    except:
        pass

    c2.info(f"📋 **Regra Gerada:** {regra_auto if regra_auto else 'Preencha % e Mínimo'}")
    c2.success(f"💰 **Pague Apenas (Exemplo):** R$ {pagar_calc if pagar_calc else '0,00'}")

    cw = []
    if titulo_c: cw.append(f"🔥 *{titulo_c}* 🔥")
    if regra_auto: cw.append(f"⚡ {regra_auto}")
    ex_w = []
    if val_min: ex_w.append(f"🛒 Adicione R$ {val_min} no carrinho")
    if cod_c: ex_w.append(f"🎟️ Cupom: {cod_c}")
    if pagar_calc: ex_w.append(f"💰 *Pague apenas R$ {pagar_calc}!*")
    if ex_w: cw.append("💡 *Exemplo:*\n" + "\n".join(ex_w))
    if link_c: cw.append(f"👉 *Pegue aqui:* {link_c}")
    txt_c_wpp = "\n\n".join(cw)

    st.markdown("---")
    cb1, cb2 = st.columns([2, 1])
    with cb1:
        if st.button("🚀 Postar CUPOM nas Redes", type="primary", use_container_width=True, key="btn_c"):
            ch = []
            if titulo_c: ch.append(f"🔥 <b>{titulo_c}</b> 🔥")
            if regra_auto: ch.append(f"⚡ {regra_auto}")
            ex_h = []
            if val_min: ex_h.append(f"🛒 Adicione R$ {val_min} no carrinho")
            if cod_c: ex_h.append(f"🎟️ Cupom: <code>{cod_c}</code>")
            if pagar_calc: ex_h.append(f"💰 <b>Pague apenas R$ {pagar_calc}!</b>")
            if ex_h: ch.append("💡 <b>Exemplo:</b>\n" + "\n".join(ex_h))
            if link_c: ch.append(f"👉 <b>Pegue aqui:</b> {link_c}")
            txt_c_html = "\n\n".join(ch)

            imgs_fb_c = imgs_c if enviar_img_fb_c else None
            imgs_tg_c = imgs_c if enviar_img_tg_c else None

            executar_envio(txt_c_html, txt_c_wpp, imgs_fb_c, imgs_tg_c, link_c, titulo_c)
    with cb2:
        wpp_url_c = f"https://api.whatsapp.com/send?text={urllib.parse.quote(txt_c_wpp)}"
        st.markdown(f'<a href="{wpp_url_c}" target="_blank" style="text-decoration:none;"><div style="background:#25D366;color:white;padding:10px;text-align:center;border-radius:8px;font-weight:bold;">🟢 WhatsApp Cupom</div></a>', unsafe_allow_html=True)

# ---------------------------------------------------------------------
# CAIXA DE RASCUNHO FLUTUANTE - COM PINÇA, TOUCH E RECUPERAÇÃO
# ---------------------------------------------------------------------
components.html(r'''
<script>
    (function() {
        const parentDoc = window.parent.document;
        
        if (parentDoc.getElementById("rascunho-box")) return;

        // 1. Criar Botão Flutuante de Recuperação (Minimizado)
        const fab = parentDoc.createElement("button");
        fab.id = "rascunho-fab";
        fab.title = "Abrir Rascunho";
        fab.innerText = "📝";
        fab.style.cssText = `
            position: fixed;
            bottom: 25px;
            right: 25px;
            width: 52px;
            height: 52px;
            border-radius: 50%;
            background: #007bff;
            color: white;
            border: none;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3);
            font-size: 22px;
            cursor: pointer;
            z-index: 9999998;
            display: none;
            align-items: center;
            justify-content: center;
            user-select: none;
            touch-action: manipulation;
        `;
        parentDoc.body.appendChild(fab);

        // 2. Criar Container Principal da Caixa
        const box = parentDoc.createElement("div");
        box.id = "rascunho-box";
        box.style.cssText = `
            position: fixed;
            top: 70px;
            right: 25px;
            width: 320px;
            height: 250px;
            background: #ffffff;
            border: 2px solid #007bff;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.25);
            z-index: 9999999;
            display: flex;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            resize: both;
            overflow: hidden;
            min-width: 220px;
            min-height: 150px;
            touch-action: none;
        `;

        box.innerHTML = `
            <div id="rascunho-header" style="
                background: #007bff;
                color: white;
                padding: 8px 12px;
                cursor: grab;
                font-weight: 600;
                font-size: 13px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                user-select: none;
                touch-action: none;
            ">
                <span>📝 Rascunho Flutuante</span>
                <div style="display: flex; gap: 6px; align-items: center;">
                    <button id="rascunho-copy" style="
                        background: rgba(255,255,255,0.2);
                        border: none;
                        color: white;
                        font-size: 11px;
                        padding: 3px 6px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">📋 Copiar</button>
                    <button id="rascunho-clear" style="
                        background: rgba(255,255,255,0.2);
                        border: none;
                        color: white;
                        font-size: 11px;
                        padding: 3px 6px;
                        border-radius: 4px;
                        cursor: pointer;
                    ">🗑️</button>
                    <button id="rascunho-close" style="
                        background: transparent;
                        border: none;
                        color: white;
                        font-size: 16px;
                        cursor: pointer;
                        margin-left: 4px;
                        font-weight: bold;
                    ">✕</button>
                </div>
            </div>
            <textarea id="rascunho-text" placeholder="Cole aqui seus textos ou rascunhos..." style="
                flex: 1;
                width: 100%;
                padding: 10px;
                border: none;
                outline: none;
                resize: none;
                font-size: 13px;
                line-height: 1.4;
                box-sizing: border-box;
                background: #fdfdfd;
                color: #222;
                touch-action: pan-y;
            "></textarea>
        `;

        parentDoc.body.appendChild(box);

        const header = parentDoc.getElementById("rascunho-header");
        const textarea = parentDoc.getElementById("rascunho-text");
        const closeBtn = parentDoc.getElementById("rascunho-close");
        const copyBtn = parentDoc.getElementById("rascunho-copy");
        const clearBtn = parentDoc.getElementById("rascunho-clear");

        let isDragging = false;
        let offsetX = 0, offsetY = 0;
        let initialPinchDist = null;
        let initialSize = { w: 0, h: 0 };

        // --- ARRASTAR (Mouse e Toque) ---
        function startDrag(e) {
            if (e.target.tagName === "BUTTON") return;
            isDragging = true;
            header.style.cursor = "grabbing";
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            offsetX = clientX - box.offsetLeft;
            offsetY = clientY - box.offsetTop;
        }

        function moveDrag(e) {
            if (!isDragging) return;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;

            let left = clientX - offsetX;
            let top = clientY - offsetY;

            left = Math.max(0, Math.min(left, window.parent.innerWidth - box.offsetWidth));
            top = Math.max(0, Math.min(top, window.parent.innerHeight - box.offsetHeight));

            box.style.left = left + "px";
            box.style.top = top + "px";
            box.style.right = "auto";
        }

        function stopDrag() {
            isDragging = false;
            header.style.cursor = "grab";
        }

        header.addEventListener("mousedown", startDrag);
        parentDoc.addEventListener("mousemove", moveDrag);
        parentDoc.addEventListener("mouseup", stopDrag);

        header.addEventListener("touchstart", startDrag, { passive: true });
        parentDoc.addEventListener("touchmove", moveDrag, { passive: true });
        parentDoc.addEventListener("touchend", stopDrag);

        // --- MODO PINÇA / REDIMENSIONAR COM 2 DEDOS (Pinch-to-Resize) ---
        function getDistance(t1, t2) {
            const dx = t1.clientX - t2.clientX;
            const dy = t1.clientY - t2.clientY;
            return Math.hypot(dx, dy);
        }

        box.addEventListener("touchstart", (e) => {
            if (e.touches.length === 2) {
                initialPinchDist = getDistance(e.touches[0], e.touches[1]);
                initialSize = { w: box.offsetWidth, h: box.offsetHeight };
            }
        }, { passive: true });

        box.addEventListener("touchmove", (e) => {
            if (e.touches.length === 2 && initialPinchDist) {
                const currentDist = getDistance(e.touches[0], e.touches[1]);
                const scale = currentDist / initialPinchDist;

                const newW = Math.max(220, Math.min(initialSize.w * scale, window.parent.innerWidth - 20));
                const newH = Math.max(150, Math.min(initialSize.h * scale, window.parent.innerHeight - 20));

                box.style.width = newW + "px";
                box.style.height = newH + "px";
            }
        }, { passive: true });

   
