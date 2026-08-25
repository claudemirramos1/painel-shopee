import json
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Painel de Ofertas", page_icon="🛍️", layout="centered"
)


def send_album_to_telegram(token, chat_id, text, media_files):
    if len(media_files) == 1:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "caption": text, "parse_mode": "Markdown"}
        files = {"photo": media_files[0].getvalue()}
        response = requests.post(url, data=payload, files=files)
        return response.json()

    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    media = []
    files = {}

    for idx, file in enumerate(media_files):
        field_name = f"photo_{idx}"
        files[field_name] = file.getvalue()
        item = {"type": "photo", "media": f"attach://{field_name}"}

        if idx == 0:
            item["caption"] = text
            item["parse_mode"] = "Markdown"

        media.append(item)

    payload = {"chat_id": chat_id, "media": json.dumps(media)}
    response = requests.post(url, data=payload, files=files)
    return response.json()


st.title("🛍️ Painel de Ofertas")
st.write(
    "Preencha a promoção para publicar no Telegram e compartilhar no WhatsApp."
)

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
    code = st.text_input("Cupom/Código (opcional)", "SHOPEE20")
    affiliate_link = st.text_input("Link de Afiliado", "https://shope.ee/exemplo")

    media_files = st.file_uploader(
        "Selecione a(s) Imagem(ns) da Oferta",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    submit = st.form_submit_button(
        "🚀 Enviar Telegram & Preparar para WhatsApp"
    )

if submit:
    if not media_files:
        st.error("Por favor, selecione pelo menos uma imagem!")
    elif not telegram_token:
        st.error("Cole o seu Bot Token na barra lateral!")
    else:
        # Formatação para o Telegram
        cupom_tg = f"\n🏷️ Cupom: `{code}`" if code else ""
        caption_tg = f"🔥 *{title}*\n\n💰 Por apenas: *R$ {price}*{cupom_tg}\n\n👇 *Compre pelo link:*\n{affiliate_link}"

        # Formatação para o WhatsApp
        cupom_wa = f"\n🏷️ Cupom: *{code}*" if code else ""
        caption_wa = f"🔥 *{title}*\n\n💰 Por apenas: *R$ {price}*{cupom_wa}\n\n👇 *Compre pelo link:*\n{affiliate_link}"

        # Envio automático para o Telegram
        res = send_album_to_telegram(
            telegram_token, telegram_chat_id, caption_tg, media_files
        )

        if res.get("ok"):
            st.success("✅ Enviado para o Telegram com sucesso!")
        else:
            st.error(f"❌ Erro no Telegram: {res.get('description')}")

        st.subheader("📲 Compartilhar no WhatsApp")

        # Preparar os arquivos e script de compartilhamento nativo do celular
        import base64

        js_files = []
        for file in media_files:
            b64_data = base64.b64encode(file.getvalue()).decode()
            mime_type = file.type
            file_name = file.name
            js_files.append(
                f"new File([Uint8Array.from(atob('{b64_data}'), c => c.charCodeAt(0))], '{file_name}', {{ type: '{mime_type}' }})"
            )

        files_array_str = f"[{', '.join(js_files)}]"
        clean_text_wa = (
            caption_wa.replace("\\", "\\\\").replace("`", "\\`").replace("\n", "\\n")
        )

        share_html = f"""
        <button id="shareBtn" style="
            background-color: #25D366;
            color: white;
            border: none;
            padding: 14px 20px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 8px;
            width: 100%;
            cursor: pointer;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        ">📲 Toque aqui para abrir no WhatsApp com Imagens</button>

        <script>
        document.getElementById('shareBtn').addEventListener('click', async () => {{
            try {{
                const files = {files_array_str};
                const text = `{clean_text_wa}`;
                if (navigator.canShare && navigator.canShare({{ files: files }})) {{
                    await navigator.share({{
                        files: files,
                        title: 'Oferta',
                        text: text
                    }});
                }} else if (navigator.share) {{
                    await navigator.share({{
                        title: 'Oferta',
                        text: text
                    }});
                }} else {{
                    alert('O compartilhamento direto não é suportado neste navegador do celular.');
                }}
            }} catch (err) {{
                console.log('Erro ao compartilhar:', err);
            }}
        }});
        </script>
        """

        components.html(share_html, height=70)
        st.info(
            "💡 **Como usar:** Toque no botão verde acima. O celular vai abrir o menu com as imagens e o texto já anexados. Escolha o WhatsApp e selecione o seu Canal!"
                                       )
