from google import genai

# Insira sua API Key do Gemini (começada com AQ...)
GEMINI_API_KEY = "AQ.Ab8RN6LlhLdStch5R9CeKr0Aam13egubrZuj3Cx1868P2flcgw"
client = genai.Client(api_key=GEMINI_API_KEY)

# Lista de 5 ofertas de teste (uma de cada categoria)
exemplo_promocoes = [
    "Carrinho de Bebê Galzerano Reclinável com Bebê Conforto em promoção por R$ 499!",
    "Jogo de Lâmpadas LED H7 para farol automotivo super branca 6000k universal.",
    "Vestido Longo Estampado de Verão tecido leve com fenda lateral - Moda Feminina.",
    "Kit 3 Camisas Polo Masculinas Piquet 100% Algodão com caimento perfeito.",
    "Fone de Ouvido Bluetooth Sem Fio com cancelamento de ruído e bateria de 30h."
]

def classificar_teste(texto):
    prompt = f"""
    Classifique o texto da promoção abaixo em exatamente UMA destas opções:
    - BEBE_INFANTIL (Carrinhos, fraldas, brinquedos, roupas de bebê, crianças ou moda infantil)
    - AUTOMOTIVO (Acessórios para carros, motos, leds, som automotivo, ferramentas de veículos, capas)
    - MODA_FEMININA (Vestidos, saias, bolsas femininas, maquiagem, sutiã, saltos, roupas femininas adultas)
    - MODA_MASCULINA (Camisas masculinas, bermudas masculinas, tênis masculinos, carteiras, barbeadores)
    - ELETRONICOS (Smartphones, fones bluetooth, carregadores, smartwatches, acessórios de PC/TV)

    Regras estritas:
    1. Responda APENAS E EXATAMENTE a palavra da categoria em caixa alta.
    2. NÃO escreva frases, pontuações ou explicações.
    3. Se não se encaixar em nenhuma das 5, responda apenas OUTRO.

    Texto da promoção:
    {texto}
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text.strip().upper()
    except Exception as e:
        return f"ERRO: {e}"

print("--- INICIANDO TESTE DOS 5 NICHOS COM GEMINI --- \n")

for idx, oferta in enumerate(exemplo_promocoes, 1):
    categoria_identificada = classificar_teste(oferta)
    print(f"Oferta {idx}: {oferta}")
    print(f"➜ Categoria Classificada: [{categoria_identificada}]\n")
    print("-" * 50)
