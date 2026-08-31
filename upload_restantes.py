import re
import requests
import os
import time

PASTA = "imagens_divulgacao"

with open("worker.py", "r", encoding="utf-8") as f:
    codigo = f.read()

url_match = re.search(
    r'SUPABASE_URL\s*=\s*["\']([^"\']+)["\']',
    codigo
)

key_match = re.search(
    r'SUPABASE_KEY\s*=\s*["\']([^"\']+)["\']',
    codigo
)

if not url_match or not key_match:
    raise RuntimeError(
        "Não consegui encontrar SUPABASE_URL ou SUPABASE_KEY no worker.py"
    )

SUPABASE_URL = url_match.group(1)
SUPABASE_KEY = key_match.group(1)

headers_base = {
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "apikey": SUPABASE_KEY,
    "Content-Type": "image/jpeg",
    "x-upsert": "false"
}

for numero in range(3, 12):

    arquivo = os.path.join(
        PASTA,
        f"mensagem-{numero:02d}.jpg"
    )

    caminho = f"divulgacao/mensagem-{numero:02d}.jpg"

    url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"ofertas/{caminho}"
    )

    print(f"\n📤 Enviando imagem {numero}...")

    if not os.path.exists(arquivo):
        print(f"❌ Arquivo não encontrado: {arquivo}")
        continue

    try:
        with open(arquivo, "rb") as imagem:
            resposta = requests.post(
                url,
                headers=headers_base,
                data=imagem,
                timeout=60
            )

        print("Status:", resposta.status_code)
        print("Resposta:", resposta.text)

        if resposta.ok:
            print(f"✅ Imagem {numero} enviada!")
        else:
            print(f"❌ Falha na imagem {numero}")

    except Exception as erro:
        print(f"❌ Erro na imagem {numero}: {erro}")

    time.sleep(5)

print("\n================================")
print("✅ UPLOAD DAS IMAGENS 03–11 FINALIZADO")
print("================================")
