import os
import requests
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def pegar_ultimo_video_pagina_principal():
    page_id = os.environ.get("MAIN_PAGE_ID")
    token = os.environ.get("PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v21.0/{page_id}/videos?fields=source,description,id&access_token={token}&limit=1"
    response = requests.get(url)
    data = response.json()
    if "data" in data and len(data["data"]) > 0:
        v = data["data"][0]
        return {"id": v.get("id"), "source": v.get("source"), "description": v.get("description", "")}
    return None

def categorizar_com_gemini(descricao):
    prompt = f"""
    Analise a legenda abaixo de um produto de afiliado e determine a categoria exata:
    - PROMONOMIA_OFERTAS
    Se não conseguir identificar claramente nenhuma categoria específica, responda estritamente com: MANTER
    Legenda:
    {descricao}
    """
    response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
    return response.text.strip()

def publicar_em_outra_pagina(video_url, descricao, target_page_id, token):
    url = f"https://graph-video.facebook.com/v21.0/{target_page_id}/videos"
    payload = {'file_url': video_url, 'description': descricao, 'access_token': token}
    return requests.post(url, data=payload).json()

if __name__ == "__main__":
    token = os.environ.get("PAGE_ACCESS_TOKEN")
    default_page_id = os.environ.get("PAGE_ID")
    
    ultimo_video = pegar_ultimo_video_pagina_principal()
    if ultimo_video:
        categoria = categorizar_com_gemini(ultimo_video["description"])
        pagina_alvo = default_page_id if categoria == "MANTER" else default_page_id
        resultado = publicar_em_outra_pagina(ultimo_video["source"], ultimo_video["description"], pagina_alvo, token)
        print("Resultado da triagem e postagem:", resultado)
    else:
        print("Nenhum vídeo encontrado na página principal.")
