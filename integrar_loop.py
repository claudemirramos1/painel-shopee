from pathlib import Path

arquivo = Path("worker.py")
texto = arquivo.read_text(encoding="utf-8")

antigo = '''        else:
            print("⏳ Fila vazia. Verificando novamente em 30 segundos...")
            time.sleep(30)
            continue
'''

novo = '''        else:
            print("📭 Fila de ofertas vazia.")
            print("📢 Verificando próxima mensagem de divulgação...")

            ok_divulgacao = executar_divulgacao()

            if ok_divulgacao:
                print(
                    f"✅ Divulgação enviada. "
                    f"Aguardando {INTERVALO_MINUTOS} min para o próximo ciclo..."
                )
                time.sleep(INTERVALO_MINUTOS * 60)
            else:
                print("⚠️ Nenhuma divulgação enviada. Tentando novamente em 30 segundos...")
                time.sleep(30)

            continue
'''

if antigo not in texto:
    raise SystemExit("❌ Não encontrei o bloco esperado. Nenhuma alteração foi feita.")

texto = texto.replace(antigo, novo, 1)

arquivo.write_text(texto, encoding="utf-8")

print("✅ Loop de divulgação integrado com sucesso.")
