import logging
import re
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from supabase import create_client, Client

# --- SUAS CREDENCIAIS DO SUPABASE ---
SUPABASE_URL = "https://ftumdeqziwyljmaehaqk.supabase.co"
SUPABASE_KEY = "sb_publishable_8qfsBhW22Sx25mvPcxWNvw_4teJRbfu"

# --- SEU TOKEN DO BOT E ID DO GRUPO DO TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8997755956:AAGW29WiWbZCpfoTGh-6m-a1qdYnfze5e_k"
RASCUNHO_GROUP_ID = -1004471689668

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def extrair_dados(texto):
    if not texto:
        return {"titulo": "", "preco": "", "link": "", "formatado": ""}

    link_match = re.search(r'https?://[^\s]+', texto)
    link = link_match.group(0) if link_match else ""

    preco_match = re.search(r'R\$\s?\d+[\.,]?\d*', texto, re.IGNORECASE)
    preco = preco_match.group(0) if preco_match else ""

    titulo = texto
    if link:
        titulo = titulo.replace(link, "")
    if preco:
        titulo = titulo.replace(preco, "")
    
    frases_remover = ["Dê uma olhada em", "Compre na Shopee agora!", "por", ":"]
    for frase in frases_remover:
        titulo = titulo.replace(frase, "")
    
    titulo = titulo.strip(" .-\n")

    formatado = "⚡ **OFERTA IMPERDÍVEL!**\n\n"
    if titulo: 
        formatado += f"🔥 **{titulo}**\n\n"
    if preco: 
        formatado += f"✅ **Por:** {preco}\n\n"
    
    formatado += "👇 **Garantia de menor preço no link abaixo**\n\n"
    if link: 
        formatado += f"🔗 {link}"

    return {
        "titulo": titulo,
        "preco": preco.replace("R$", "").strip(),
        "link": link,
        "formatado": formatado
    }

async def processar_rascunho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != RASCUNHO_GROUP_ID:
        return

    message = update.effective_message
    texto_bruto = message.text or message.caption or ""
    dados = extrair_dados(texto_bruto)

    item = {
        "titulo": dados["titulo"],
        "preco": dados["preco"],
        "link": dados["link"],
        "formatado": dados["formatado"],
        "fotos": []
    }

    try:
        supabase.table("ofertas").insert(item).execute()
        await message.reply_text("📥 Salvo na nuvem com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar: {e}")

def main():
    print("🤖 Bot Ativo (Enviando para o Supabase)...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, processar_rascunho))
    app.run_polling()

if __name__ == "__main__":
    main()
