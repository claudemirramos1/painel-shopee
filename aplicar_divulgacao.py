from pathlib import Path

arquivo = Path("worker.py")
texto = arquivo.read_text(encoding="utf-8")

marcador = "# Loop principal do robô"

if marcador not in texto:
    raise SystemExit("❌ Não encontrei o marcador do loop principal.")

funcoes = r'''
# ==========================================
# DIVULGAÇÕES AUTOMÁTICAS
# ==========================================

def obter_numero_divulgacao():
    try:
        url = (
            f"{SUPABASE_URL}/rest/v1/controle_divulgacao"
            "?select=proxima_mensagem&limit=1"
        )

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code != 200:
            print(f"⚠️ Erro no controle: {r.status_code} - {r.text}")
            return 1

        dados = r.json()

        if not dados:
            return 1

        numero = int(dados[0].get("proxima_mensagem", 1))

        if numero < 1 or numero > 11:
            numero = 1

        return numero

    except Exception as e:
        print(f"⚠️ Erro ao ler controle: {e}")
        return 1


def buscar_proxima_divulgacao():
    try:
        numero = obter_numero_divulgacao()

        url = (
            f"{SUPABASE_URL}/rest/v1/mensagens_divulgacao"
            f"?id=eq.{numero}"
            "&select=id,mensagem,imagem"
        )

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }

        r = requests.get(url, headers=headers, timeout=20)

        if r.status_code != 200:
            print(
                f"⚠️ Erro ao buscar divulgação: "
                f"{r.status_code} - {r.text}"
            )
            return None

        dados = r.json()

        if not dados:
            print(f"⚠️ Mensagem {numero} não encontrada.")
            return None

        return dados[0]

    except Exception as e:
        print(f"⚠️ Erro ao buscar divulgação: {e}")
        return None


def avancar_divulgacao():
    try:
        atual = obter_numero_divulgacao()
        proxima = atual + 1

        if proxima > 11:
            proxima = 1

        url = f"{SUPABASE_URL}/rest/v1/controle_divulgacao"

        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        r = requests.patch(
            url,
            headers=headers,
            json={"proxima_mensagem": proxima},
            timeout=20
        )

        if r.status_code not in (200, 204):
            print(
                f"⚠️ Erro ao avançar divulgação: "
                f"{r.status_code} - {r.text}"
            )
            return False

        print(f"🔄 Próxima divulgação: mensagem {proxima}")
        return True

    except Exception as e:
        print(f"⚠️ Erro ao atualizar controle: {e}")
        return False


def executar_divulgacao():
    mensagem = buscar_proxima_divulgacao()

    if not mensagem:
        return False

    numero = mensagem.get("id")
    texto = mensagem.get("mensagem") or ""
    imagem = mensagem.get("imagem") or ""

    if not texto:
        print(f"⚠️ Divulgação {numero} está sem texto.")
        return False

    if not imagem:
        print(f"⚠️ Divulgação {numero} está sem imagem.")
        return False

    print(f"📢 Enviando divulgação {numero}/11...")
    print(f"🖼️ Imagem: {imagem}")

    sucesso = enviar_facebook(
        texto=texto,
        link="",
        imagem_url=imagem
    )

    if sucesso:
        print(f"✅ Divulgação {numero} publicada no Facebook!")
        avancar_divulgacao()
        return True

    print(f"❌ Falha ao publicar divulgação {numero}.")
    return False


# ==========================================
# FIM DAS DIVULGAÇÕES AUTOMÁTICAS
# ==========================================

'''

texto = texto.replace(
    marcador,
    funcoes + "\n" + marcador,
    1
)

arquivo.write_text(texto, encoding="utf-8")

print("✅ Alteração aplicada ao worker.py")
