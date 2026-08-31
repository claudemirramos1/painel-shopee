from google import genai

GEMINI_API_KEY = "AQ.Ab8RN6LlhLdStch5R9CeKr0Aam13egubrZuj3Cx1868P2flcgw"

client = genai.Client(api_key=GEMINI_API_KEY)

prompt = "Classifique esta oferta em uma categoria [BEBE, AUTOMOTIVO, MODA]: Carrinho de bebê dobrável com berço."

try:
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )
    print("--- RESPOSTA DA IA ---")
    print(response.text.strip())
    print("----------------------")
except Exception as e:
    print(f"Erro no teste: {e}")
