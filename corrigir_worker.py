from pathlib import Path

arquivo = Path("worker.py")
texto = arquivo.read_text(encoding="utf-8")

# Remove a dependência do pacote supabase
texto = texto.replace(
    "from supabase import create_client, Client\n",
    ""
)

texto = texto.replace(
    "supabase = None\ntry:\n    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)\n    print(\"✅ Conectado ao Supabase com sucesso!\")\nexcept Exception as e:\n    print(f\"⚠️ Erro ao criar cliente Supabase: {e}\")\n",
    """supabase = True
print("✅ Supabase configurado via REST API!")
"""
)

arquivo.write_text(texto, encoding="utf-8")

print("✅ Worker ajustado para usar REST API.")
