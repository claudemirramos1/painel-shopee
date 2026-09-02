import os
import requests
import yt_dlp
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def baixar_midia_instagram(url_insta):
    ydl_opts = {
        "format": "best",
        "outtmpl": "temp_video.mp4",
        "quiet": True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url_insta, download=True)
        legenda_original = info.get("description", "")
    return "temp_video.mp4", legenda_original

def refinar_legenda_ia(legenda_original, link_afiliado):
    prompt = f"""
    Reescreva a seguinte legenda de Instagram para uma postagem vendedora de afiliados.
    Adicione ganchos chamativos, emojis e inclua obrigatoriamente este link de afiliado: {link_afiliado}.
    
    Legenda original:
    {legenda_original}
    """
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

def publicar_video_fb(video_path, descricao):
    page_id = os.environ.get("PAGE_ID")
    token = os.environ.get("PAGE_ACCESS_TOKEN")
    url = f"https://graph-video.facebook.com/v21.0/{page_id}/videos"
    
    payload = {
        "description": descricao,
        "access_token": token
    }
    
    with open(video_path, "rb") as vf:
        files = {"source": vf}
        res = requests.post(url, data=payload, files=files)
    
    return res.json()

if __name__ == "__main__":
    fila_path = "fila_videos.txt"
    if os.path.exists(fila_path):
        with open(fila_path, "r", encoding="utf-8") as f:
            linhas = [l.strip() for l in f if l.strip()]
        if linhas:
            primeira_linha = linhas[0]
            link_insta, link_afiliado = [x.strip() for x in primeira_linha.split(",")]
            
            print("📥 Baixando vídeo e legenda do Instagram...")
            video, legenda = baixar_midia_instagram(link_insta)
            
            print("🤖 Gerando legenda otimizada com Gemini...")
            nova_legenda = refinar_legenda_ia(legenda, link_afiliado)
            
            print("🚀 Publicando vídeo na página do Facebook...")
            resultado = publicar_video_fb(video, nova_legenda)
            print(resultado)
            
            if os.path.exists(video):
                os.remove(video)
                
            with open(fila_path, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas[1:]))
    else:
        print("Crie o arquivo fila_videos.txt com: URL_INSTA, LINK_AFILIADO")
