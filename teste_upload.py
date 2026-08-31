import re
import requests

ARQUIVO = "imagens_divulgacao/mensagem-02.jpg"
CAMINHO = "divulgacao/mensagem-02.jpg"

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

url = (
    f"{SUPABASE_URL}/storage/v1/object/"
    f"ofertas/{CAMINHO}"
)

headers = {
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "apikey": SUPABASE_KEY,
    "Content-Type": "image/jpeg",
    "x-upsert": "false",
}

with open(ARQUIVO, "rb") as arquivo:
    resposta = requests.post(
        url,
        headers=headers,
        data=arquivo,
        timeout=60
    )

print("Status:", resposta.status_code)
print("Resposta:", resposta.text)

if resposta.ok:
    print("✅ Imagem 02 enviada com sucesso!")
    print(
        "URL pública:",
        f"{SUPABASE_URL}/storage/v1/object/public/"
        f"ofertas/{CAMINHO}"
    )
else:
    print("❌ Upload falhou.")
