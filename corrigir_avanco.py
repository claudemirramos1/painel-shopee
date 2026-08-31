from pathlib import Path

arquivo = Path("worker.py")
texto = arquivo.read_text(encoding="utf-8")

antigo = 'url = f"{SUPABASE_URL}/rest/v1/controle_divulgacao"'

novo = '''url = (
            f"{SUPABASE_URL}/rest/v1/controle_divulgacao"
            f"?proxima_mensagem=eq.{atual}"
        )'''

if antigo not in texto:
    raise SystemExit("❌ Trecho não encontrado. Nenhuma alteração feita.")

texto = texto.replace(antigo, novo, 1)

arquivo.write_text(texto, encoding="utf-8")

print("✅ Correção do avanço aplicada.")
