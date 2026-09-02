import os
import json
import time
import io
import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageEnhance, ImageOps
from supabase import create_client, Client

SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://ftumdeqziwyljmaehaqk.supabase.co")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "sb_publishable_8qfsBhW22Sx25mvPcxWNvw_4teJRbfu")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

FACEBOOK_PAGE_ID = st.secrets.get("FACEBOOK_PAGE_ID", "1214303865109377")
FACEBOOK_ACCESS_TOKEN = st.secrets.get("FACEBOOK_ACCESS_TOKEN", "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst")
TELEGRAM_CANAL_TOKEN = st.secrets.get("TELEGRAM_CANAL_TOKEN", "8353706833:AAHhyPqgeNezFY1X4NTMegpaPf_UdVOBs04")
TELEGRAM_CANAL_ID = st.secrets.get("TELEGRAM_CANAL_ID", "-1004406728710")

st.set_page_config(page_title="Gerador & Gestão de Ofertas", page_icon="📢", layout="wide")

if "input_titulo" not in st.session_state: st.session_state.input_titulo = ""
if "input_preco" not in st.session_state: st.session_state.input_preco = "0,00"
if "input_link" not in st.session_state: st.session_state.input_link = ""

def carregar_rascunhos():
    try:
        res = supabase.table("ofertas").select("*").order("created_at", desc=False).execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Erro ao buscar ofertas no Supabase: {e}")
        return []

def remover_rascunho(rascunho_id):
    try:
        supabase.table("ofertas").delete().eq("id", rascunho_id).execute()
    except Exception as e:
        st.error(f"Erro ao remover: {e}")

def extrair_dados_do_texto_bruto(texto_bruto):
    if not texto_bruto:
        return "Produto", "0,00", ""
    
    link = ""
    match_link = re.search(r'(https?://\S+)', texto_bruto)
    if match_link: link = match_link.group(1)

    preco = "0,00"
    match_preco = re.search(r'R\$\s*([\d\.,]+)', texto_bruto, re.IGNORECASE)
    if match_preco: preco = match_preco.group(1)

    titulo = re.sub(r'Dê uma olhada em\s*', '', texto_bruto, flags=re.IGNORECASE)
    if match_preco: titulo = re.sub(rf'por\s*R\$\s*{re.escape(preco)}.*', '', titulo, flags=re.IGNORECASE)
    if link: titulo = titulo.replace(link, '')
    titulo = titulo.replace("Compre na Shopee agora!", "").strip()
    titulo = re.sub(r'\s+', ' ', titulo).strip()
    return titulo or "Oferta Imperdível", preco, link

def obter_texto_anuncio(item):
    texto_base = item.get("formatado") or item.get("titulo") or item.get("descricao") or ""
    titulo, preco, link = extrair_dados_do_texto_bruto(texto_base)
    if item.get("titulo") and "Dê uma olhada" not in str(item.get("titulo")): titulo = item.get("titulo")
    if item.get("preco"): preco = item.get("preco")
    if item.get("link"): link = item.get("link")
    
    import re
    palavras = re.findall(r"\w+", titulo)
    palavras_filtradas = [p.capitalize() for p in palavras if len(p) > 3 and p.lower() not in ["para", "com", "uma", "dos", "das"]]
    hashtag_produto = palavras_filtradas[0] if palavras_filtradas else "Utensilios"

    texto_formatado = (
        f"👉🏻 {link} 🔗\n\n"
        f"🍳✨ **{titulo}**! 😍\n\n"
        f"💰 **VALOR: R$ {preco}** (bem destacado)\n\n"
        f"💰 Aproveite e confira a oferta!\n"
        f"🔗 Ou digite o código no link da bio.\n\n"
        f"#CozinhaPratica #DicasDeCozinha #{hashtag_produto} #achadinhosimperdíveis #ofertas"
    )
    return texto_formatado, link

def obter_fotos_lista(item):
    val = item.get("fotos") or item.get("imagem") or item.get("foto") or item.get("img") or item.get("image")
    if not val: return []
    urls = []
    if isinstance(val, list):
        for primeiro in val:
            if isinstance(primeiro, str): urls.append(primeiro)
            elif isinstance(primeiro, dict):
                u = primeiro.get("url") or primeiro.get("link") or primeiro.get("path")
                if u: urls.append(u)
    elif isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                for p in parsed:
                    if isinstance(p, str): urls.append(p)
                    elif isinstance(p, dict):
                        u = p.get("url") or p.get("link")
                        if u: urls.append(u)
            elif isinstance(parsed, dict):
                u = parsed.get("url") or parsed.get("link")
                if u: urls.append(u)
        except:
            urls.append(val)
    return urls

def processar_imagem(img_upload):
    try:
        if isinstance(img_upload, str):
            resp = requests.get(img_upload, timeout=15)
            if resp.status_code != 200: return None
            img = Image.open(io.BytesIO(resp.content))
        else:
            img_upload.seek(0)
            img = Image.open(io.BytesIO(img_upload.getvalue()))
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        img_a = ImageOps.pad(img, (1200, 1200), color=(255, 255, 255))
        buf = io.BytesIO()
        img_a.save(buf, format="JPEG", quality=92)
        buf.seek(0)
        buf.name = "foto_oferta.jpg"
        return buf
    except:
        return None

def enviar_telegram_com_foto(texto, imagens_ref):
    try:
        if not imagens_ref:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMessage"
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'text': texto, 'parse_mode': 'Markdown'}, timeout=15)
            return r.json().get("ok", False), r.text

        if isinstance(imagens_ref, (str, io.BytesIO)): imagens_ref = [imagens_ref]
        midia_processada, files_dict = [], {}
        for i, img_ref in enumerate(imagens_ref):
            img_io = processar_imagem(img_ref)
            if img_io:
                file_key = f"photo_{i}"
                files_dict[file_key] = ('foto.jpg', img_io.getvalue(), 'image/jpeg')
                item_midia = {"type": "photo", "media": f"attach://{file_key}"}
                if i == 0 and texto:
                    item_midia["caption"] = texto
                    item_midia["parse_mode"] = "Markdown"
                midia_processada.append(item_midia)

        if len(midia_processada) > 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMediaGroup"
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'media': json.dumps(midia_processada)}, files=files_dict, timeout=40)
            return r.json().get("ok", False), r.text
        elif len(midia_processada) == 1:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendPhoto"
            file_key = list(files_dict.keys())[0]
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'caption': texto, 'parse_mode': 'Markdown'}, files={'photo': files_dict[file_key]}, timeout=30)
            return r.json().get("ok", False), r.text
        else:
            url = f"https://api.telegram.org/bot{TELEGRAM_CANAL_TOKEN}/sendMessage"
            r = requests.post(url, data={'chat_id': TELEGRAM_CANAL_ID, 'text': texto, 'parse_mode': 'Markdown'}, timeout=15)
            return r.json().get("ok", False), r.text
    except Exception as e:
        return False, str(e)

def enviar_facebook_com_foto(texto, link, imagem_ref):
    try:
        img_alvo = imagem_ref[0] if isinstance(imagem_ref, list) and len(imagem_ref) > 0 else imagem_ref
        img_io = processar_imagem(img_alvo) if img_alvo else None
        legenda = texto.replace("**", "*")
        if img_io:
            if link and link not in legenda: legenda += f"\n\n🔗 {link}"
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/photos"
            r = requests.post(url, data={'caption': legenda, 'access_token': FACEBOOK_ACCESS_TOKEN}, files={'source': ('foto.jpg', img_io.getvalue(), 'image/jpeg')}, timeout=40)
            res = r.json()
            return ("id" in res or "post_id" in res), r.text
        else:
            url = f"https://graph.facebook.com/v19.0/{FACEBOOK_PAGE_ID}/feed"
            r = requests.post(url, data={'message': legenda, 'access_token': FACEBOOK_ACCESS_TOKEN, 'link': link or ""}, timeout=20)
            res = r.json()
            return ("id" in res or "post_id" in res), r.text
    except Exception as e:
        return False, str(e)

def disparar_redes_completo(texto_formatado, link, imagem_ref, enviar_fb=True, enviar_tg=True):
    ok_tg, err_tg = (enviar_telegram_com_foto(texto_formatado, imagem_ref) if enviar_tg else (True, "Não selecionado"))
    ok_fb, err_fb = (enviar_facebook_com_foto(texto_formatado, link, imagem_ref) if enviar_fb else (True, "Não selecionado"))
    return (ok_tg and ok_fb), f"TG: {err_tg} | FB: {err_fb}"

st.title("📢 Painel Completo: Gerador & Gestão de Ofertas")

aba_gerador, aba_manual, aba_fila, aba_auto = st.tabs([
    "✨ Gerador HTML (Planilha)", 
    "✍️ Postagem Manual", 
    "📥 Fila de Rascunhos", 
    "🤖 Piloto Automático"
])

with aba_gerador:
    st.subheader("Gerador de Divulgação Inteligente")
    st.caption("Esta é a interface do seu arquivo HTML incorporada diretamente no Streamlit, mantendo o envio integrado para a sua planilha via Web App.")

    html_gerador = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <style>
            * { box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 10px; background-color: #f0f2f5; color: #1c1e21; margin: 0; }
            .container { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); max-width: 100%; margin: 0 auto; }
            h2 { margin-top: 0; font-size: 20px; color: #111; text-align: center; }
            label { font-weight: 600; display: block; margin-top: 15px; font-size: 14px; color: #444; }
            input[type="text"] { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #ccc; border-radius: 8px; font-size: 15px; outline: none; }
            input[type="text"]:focus { border-color: #007bff; }
            button { margin-top: 18px; width: 100%; padding: 14px; background-color: #28a745; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
            button:active { background-color: #218838; }
            .result-box { margin-top: 22px; padding: 16px; background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; }
            .code-row { display: flex; align-items: center; justify-content: space-between; background: #fff3cd; padding: 10px 14px; border-radius: 6px; border: 1px solid #ffeeba; }
            .code-highlight { font-size: 20px; font-weight: 800; color: #856404; letter-spacing: 1px; }
            .copy-btn { padding: 6px 12px; font-size: 12px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .section-title { font-weight: bold; margin-top: 15px; font-size: 14px; color: #555; }
            pre { white-space: pre-wrap; word-wrap: break-word; font-family: inherit; font-size: 14px; line-height: 1.5; background: #ffffff; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0; margin-top: 5px; }
            .btn-copy-all { margin-top: 10px; width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 14px; cursor: pointer; }
            .sheet-box { margin-top: 20px; padding: 15px; background: #e7f5ff; border: 1px solid #b3d7ff; border-radius: 8px; }
            .btn-sheet { background-color: #17a2b8; margin-top: 10px; }
            .btn-sheet:active { background-color: #138496; }
        </style>
    </head>
    <body>
    <div class="container">
        <h2>✨ Gerador de Post & Código</h2>
        <label for="productName">Cole a oferta ou nome do produto:</label>
        <input type="text" id="productName" placeholder="Cole o título ou anúncio completo aqui">
        <button onclick="generateContent()">Gerar Divulgação</button>
        <div class="result-box" id="output" style="display:none;">
            <div class="section-title">1. Código Único (Curto):</div>
            <div class="code-row">
                <span class="code-highlight" id="uniqueCode"></span>
                <button class="copy-btn" onclick="copyCode()">Copiar Código</button>
            </div>
            <div class="section-title">2. Texto Completo para o Post:</div>
            <pre id="postText"></pre>
            <button class="btn-copy-all" onclick="copyPost()">Copiar Texto Completo</button>
            <div class="sheet-box">
                <div class="section-title" style="margin-top:0;">3. Salvar na Planilha:</div>
                <label for="productLink" style="margin-top:5px;">Link do Produto / Afiliado:</label>
                <input type="text" id="productLink" placeholder="https://shopee.com.br/...">
                <button class="btn-sheet" onclick="sendToSheet()">📊 Salvar Código e Link na Planilha</button>
            </div>
        </div>
    </div>
    <script>
    const SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzzhTgatVKIUrpE6wVUSYfivNjuJ99RLfuRvISQX1PPZhCypcByxzXcac-bx2y0hg/exec";
    const categoryTemplates = {
        cafe: { header: "☕✨ Café fresquinho de um jeito prático!", body: "Perfeito para preparar seu café ou chá onde estiver. Compacto, fácil de usar e sem complicação! 😍", tags: ['#Cafe', '#CafeEmCasa', '#HoraDoCafe'] },
        infantil: { header: "🚲💖 Diversão garantida para a criançada!", body: "Perfeita para os primeiros passos e momentos inesquecíveis. Super segura, confortável e estilosa! 😍", tags: ['#MundoInfantil', '#Brinquedos', '#Kids'] },
        cozinha: { header: "🍳✨ Praticidade total na sua cozinha!", body: "O item que faltava para facilitar a sua rotina diária com muito mais eficiência e estilo! 😍", tags: ['#CozinhaPratica', '#DicasDeCozinha', '#Utensilios'] },
        beleza: { header: "✨💖 Seu momento de autocuidado ainda melhor!", body: "Ideal para manter sua rotina de beleza impecável todos os dias com facilidade! 😍", tags: ['#Beleza', '#Skincare', '#AutoCuidado'] },
        tecnologia: { header: "⚡🔌 Praticidade e tecnologia no seu dia a dia!", body: "Mais facilidade e eficiência para a sua rotina com qualidade surpreendente! 😍", tags: ['#Tecnologia', '#Gadgets', '#SmartHome'] },
        casa: { header: "🏠✨ Sua casa ainda mais prática e bonita!", body: "Um item essencial para facilitar a organização e o dia a dia do seu lar! 😍", tags: ['#CasaEOrganizacao', '#Utilidades', '#DicasParaCasa'] },
        geral: { header: "🔥✨ Olha esse achadinho incrível!", body: "Perfeito para facilitar sua rotina com muita praticidade e qualidade! 😍", tags: ['#Achadinhos', '#Shopee', '#Promoção'] }
    };
    const stopWords = ['confira', 'com', 'para', 'rosa', 'azul', 'preto', 'verde', 'amarelo', 'aro', 'desconto', 'somente', 'freio', 'tambor', 'rodas', 'treinamento', 'bicicleta', 'infantil', 'nathor', 'charm'];
    function cleanProductName(input) {
        return input.replace(/^confira\s+/i, '').replace(/com\s+\d+%\s+de\s+desconto.*/i, '').replace(/somente\s+r\$\s*[\d.,]+/i, '').trim();
    }
    function detectCategory(title) {
        const t = title.toLowerCase();
        if (t.includes('café') || t.includes('cafe') || t.includes('coador') || t.includes('xícara')) return 'cafe';
        if (t.includes('bicicleta') || t.includes('infantil') || t.includes('brinquedo') || t.includes('boneca') || t.includes('bebê') || t.includes('bebe')) return 'infantil';
        if (t.includes('panela') || t.includes('cozinha') || t.includes('airfryer') || t.includes('faca') || t.includes('prato')) return 'cozinha';
        if (t.includes('batom') || t.includes('maquiagem') || t.includes('cabelo') || t.includes('pele') || t.includes('sabonete')) return 'beleza';
        if (t.includes('fone') || t.includes('celular') || t.includes('carregador') || t.includes('led') || t.includes('bluetooth')) return 'tecnologia';
        if (t.includes('organizador') || t.includes('toalha') || t.includes('almofada') || t.includes('mop')) return 'casa';
        return 'geral';
    }
    function generateShortCode() {
        const now = Date.now().toString(36).slice(-3).toUpperCase();
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
        return (chars.charAt(Math.floor(Math.random() * chars.length)) + now).slice(0, 4);
    }
    function generateContent() {
        const rawInput = document.getElementById("productName").value.trim();
        if (!rawInput) { alert("Por favor, digite ou cole o nome do produto!"); return; }
        const cleanTitle = cleanProductName(rawInput);
        const category = detectCategory(cleanTitle);
        const template = categoryTemplates[category];
        const code = generateShortCode();

        const linkMatch = rawInput.match(/https?:\/\/(?:s\.shopee\.com\.br|shopee\.com\.br|www\.shopee\.com\.br)\/\S+/i);
        const extractedLink = linkMatch ? linkMatch[0].replace(/[.,!?;:)\\]}]+$/, "") : "";
        document.getElementById("productLink").value = extractedLink;

        let description = "";
        if (extractedLink) {
            description += `👉🏻 ${extractedLink} 🔗

`;
        }
        
        let precoMatch = rawInput.match(/R\$\s*([\d\.,]+)/i);
        let precoStr = precoMatch ? precoMatch[0] : "R$ 0,00";

        description += `${template.header}

${cleanTitle}! 😍

`;
        description += `💰 **VALOR: ${precoStr}**

`;
        description += `💰 Aproveite e confira a oferta!
🔗 Ou digite o código ${code} no link da bio.

`;
        
        let tagProd = template.tags.length > 0 ? template.tags[0] : "#Utensilios";
        description += `#CozinhaPratica #DicasDeCozinha ${tagProd} #achadinhosimperdíveis #ofertas`;

        document.getElementById("uniqueCode").innerText = code;
        document.getElementById("postText").innerText = description;
        document.getElementById("output").style.display = "block";
    }
    function copyCode() { navigator.clipboard.writeText(document.getElementById('uniqueCode').innerText); alert('Código copiado!'); }
    function copyPost() { navigator.clipboard.writeText(document.getElementById('postText').innerText); alert('Texto completo copiado!'); }
    function sendToSheet() {
        const code = document.getElementById('uniqueCode').innerText;
        const link = document.getElementById('productLink').value.trim();
        if (!link) { alert('Por favor, cole o link do produto antes de enviar!'); return; }
        const formData = new URLSearchParams();
        formData.append('code', code);
        formData.append('link', link);
        fetch(SCRIPT_URL, { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formData.toString() })
        .then(() => { alert(`✅ Salvo na planilha!\nCódigo: ${code}`); document.getElementById('productLink').value = ''; })
        .catch(err => alert('❌ Erro: ' + err));
    }
    </script>
    </body>
    </html>
    """
    components.html(html_gerador, height=650, scrolling=True)

with aba_manual:
    st.subheader("Postagem Manual para Redes Sociais")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        titulo = st.text_input("Título do Produto", value=st.session_state.input_titulo)
        preco = st.text_input("Preço Promocional (R$)", value=st.session_state.input_preco)
        link = st.text_input("Link de Afiliado", value=st.session_state.input_link)
    with col_m2:
        st.markdown("**Canais de Envio:**")
        manual_fb = st.checkbox("Publicar no Facebook", value=True, key="m_fb")
        manual_tg = st.checkbox("Publicar no Telegram", value=True, key="m_tg")
    foto_manual = st.file_uploader("📸 Foto do Produto (Opcional)", type=["jpg", "png", "webp"])
    texto_preview = f"⚡ **OFERTA IMPERDÍVEL!**\n\n🔥 **{titulo}**\n\n✅ **Por:** R$ {preco}\n\n👇 **Garantia de menor preço no link abaixo**\n\n🔗 {link}"
    st.info(texto_preview)
    if st.button("🚀 Disparar Postagem Manual", type="primary"):
        if not (manual_fb or manual_tg): st.warning("⚠️ Selecione pelo menos uma rede social!")
        else:
            with st.spinner("Enviando..."):
                ok, log = disparar_redes_completo(texto_preview, link, foto_manual, manual_fb, manual_tg)
                if ok: st.success("✅ Oferta postada com sucesso!")
                else: st.error(f"❌ Erro no disparo: {log}")

with aba_fila:
    st.subheader("Fila de Ofertas Capturadas pelo Bot")
    @st.fragment(run_every=10)
    def renderizar_fila_rascunhos():
        if st.button("🔄 Atualizar Fila"): st.rerun()
        rascunhos = carregar_rascunhos()
        if not rascunhos:
            st.info("Nenhuma oferta pendente no momento.")
            return
        st.write(f"Total na fila: **{len(rascunhos)}** oferta(s)")
        col_opt1, col_opt2 = st.columns(2)
        fila_fb = col_opt1.checkbox("Enviar para Facebook", value=True, key="f_fb_global")
        fila_tg = col_opt2.checkbox("Enviar para Telegram", value=True, key="f_tg_global")

        for item in rascunhos:
            fotos_item_lista = obter_fotos_lista(item)
            texto_item, link_item = obter_texto_anuncio(item)
            titulo_card = item.get('titulo') or item.get('formatado') or 'Oferta'
            with st.expander(f"📦 {titulo_card[:50]}...", expanded=False):
                if fotos_item_lista:
                    cols_imgs = st.columns(min(len(fotos_item_lista), 4))
                    for idx, img_url in enumerate(fotos_item_lista):
                        with cols_imgs[idx % len(cols_imgs)]:
                            try: st.image(img_url, width=120)
                            except: pass
                st.text_area("Texto Formatado:", value=texto_item, height=130, key=f"txt_{item.get('id')}")
                col_b1, col_b2, col_b3 = st.columns(3)
                if col_b1.button("📋 Carregar no Manual", key=f"load_{item.get('id')}"):
                    t_ext, p_ext, l_ext = extrair_dados_do_texto_bruto(item.get("formatado") or "")
                    st.session_state.input_titulo = item.get("titulo") or t_ext
                    st.session_state.input_preco = item.get("preco") or p_ext
                    st.session_state.input_link = item.get("link") or l_ext
                    st.success("✅ Carregado na aba Manual!")
                    time.sleep(0.3)
                    st.rerun()
                if col_b2.button("🚀 Enviar Agora", key=f"send_{item.get('id')}"):
                    ok, log = disparar_redes_completo(texto_item, link_item, fotos_item_lista, fila_fb, fila_tg)
                    if ok:
                        remover_rascunho(item.get("id"))
                        st.success("Publicado e removido!")
                        st.rerun()
                    else: st.error(f"Erro: {log}")
                if col_b3.button("🗑️ Descartar", key=f"del_{item.get('id')}"):
                    remover_rascunho(item.get("id"))
                    st.rerun()
    renderizar_fila_rascunhos()

with aba_auto:
    st.subheader("⚙️ Configuração do Disparo Automático")
    if "auto_rodando" not in st.session_state: st.session_state.auto_rodando = False
    intervalo = st.number_input("Intervalo entre postagens (minutos):", min_value=1, max_value=180, value=15)
    col_p1, col_p2 = st.columns(2)
    if col_p1.button("▶️ Ligar Piloto Automático", type="primary"): st.session_state.auto_rodando = True
    if col_p2.button("⏸️ Pausar Piloto Automático"): st.session_state.auto_rodando = False
    
    if st.session_state.auto_rodando: st.success(f"🟢 **ATIVO** — Intervalo: {intervalo} min.")
    else: st.warning("🔴 **PAUSADO**")

    if st.session_state.auto_rodando:
        rascunhos = carregar_rascunhos()
        if not rascunhos:
            st.info("Aguardando novas ofertas...")
            time.sleep(10)
            st.rerun()
        else:
            proxima = rascunhos[0]
            texto_auto, link_auto = obter_texto_anuncio(proxima)
            fotos_auto_lista = obter_fotos_lista(proxima)
            ok, log = disparar_redes_completo(texto_auto, link_auto, fotos_auto_lista, enviar_fb=True, enviar_tg=True)
            if ok:
                remover_rascunho(proxima.get("id"))
                st.success(f"✅ Publicado! Próximo em {intervalo} min...")
                time.sleep(intervalo * 60)
                st.rerun()
            else:
                st.error(f"Erro: {log}. Tentando em 30s...")



def formatar_texto_anuncio(texto_bruto):
    if not texto_bruto:
        return "Oferta Imperdível", "0,00", "", ""
    
    import re
    
    link = ""
    match_link = re.search(r"(https?://\S+)", texto_bruto)
    if match_link:
        link = match_link.group(1)
        
    preco = "0,00"
    match_preco = re.search(r"R\$\s*([\d\.,]+)", texto_bruto, re.IGNORECASE)
    if match_preco:
        preco = match_preco.group(1)
        
    titulo = texto_bruto
    if match_link:
        titulo = titulo.replace(link, "")
    titulo = re.sub(r"Dê uma olhada em\s*", "", titulo, flags=re.IGNORECASE)
    if match_preco:
        titulo = re.sub(rf"por\s*R\$\s*{re.escape(preco)}.*", "", titulo, flags=re.IGNORECASE)
        titulo = re.sub(rf"R\$\s*{re.escape(preco)}", "", titulo, flags=re.IGNORECASE)
    titulo = titulo.replace("Compre na Shopee agora!", "").strip()
    titulo = re.sub(r"\s+", " ", titulo).strip()
    
    if not titulo:
        titulo = "Oferta Imperdível"

    # Gera exatamente 1 hashtag personalizada baseada no nome do produto
    palavras = re.findall(r"\w+", titulo)
    palavras_filtradas = [p.capitalize() for p in palavras if len(p) > 3 and p.lower() not in ["para", "com", "uma", "dos", "das"]]
    hashtag_produto = "".join(palavras_filtradas[:1]) if palavras_filtradas else "Utensilios"

    # Monta exatamente no padrão que você exigiu
    texto_formatado = (
        f"👉🏻 {link} 🔗\n\n"
        f"🍳✨ **{titulo}**! 😍\n\n"
        f"💰 **VALOR: R$ {preco}** (bem destacado)\n\n"
        f"💰 Aproveite e confira a oferta!\n"
        f"🔗 Ou digite o código no link da bio.\n\n"
        f"#CozinhaPratica #DicasDeCozinha #{hashtag_produto} #achadinhosimperdíveis #ofertas"
    )
    
    return texto_formatado, titulo, preco, link
