import os
import requests
import time

# ATENÇÃO: esta chave foi exposta na conversa.
# Troque por uma nova chave depois dos testes.
API_KEY = "57327689-bceece724c728989e0b032374"

PASTA = "imagens_divulgacao"
os.makedirs(PASTA, exist_ok=True)

temas = {
    2: "sunrise hope",
    3: "success perseverance mountain",
    4: "faith light sunrise",
    5: "faith courage sunrise",
    6: "rainbow after rain hope",
    7: "new beginning adventure",
    8: "adventure mountain traveler",
    9: "peace nature reflection",
    10: "prayer sunrise",
    11: "determination road sunrise"
}

for numero, tema in temas.items():

    print(f"\n🔎 Procurando imagem {numero}: {tema}")

    parametros = {
        "key": API_KEY,
        "q": tema,
        "image_type": "photo",
        "orientation": "horizontal",
        "safesearch": "true",
        "per_page": 10,
        "order": "popular"
    }

    try:
        resposta = requests.get(
            "https://pixabay.com/api/",
            params=parametros,
            timeout=30
        )

        resposta.raise_for_status()
        dados = resposta.json()

        if not dados.get("hits"):
            print(f"❌ Nenhuma imagem encontrada para {numero}")
            continue

        imagem = dados["hits"][0]

        url = imagem.get("largeImageURL") or imagem.get("webformatURL")

        if not url:
            print(f"❌ URL da imagem não encontrada para {numero}")
            continue

        arquivo = os.path.join(
            PASTA,
            f"mensagem-{numero:02d}.jpg"
        )

        img = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        img.raise_for_status()

        with open(arquivo, "wb") as f:
            f.write(img.content)

        print(f"✅ Salva: {arquivo}")
        print(f"   Fonte: {imagem.get('pageURL')}")

        time.sleep(2)

    except requests.exceptions.RequestException as erro:
        print(f"❌ Erro de conexão na imagem {numero}: {erro}")

    except Exception as erro:
        print(f"❌ Erro na imagem {numero}: {erro}")

print("\n================================")
print("✅ DOWNLOAD FINALIZADO")
print("================================")
	
