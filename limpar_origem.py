import requests

PAGINA_ORIGEM_ID = "1214303865109377"
PAGINA_ORIGEM_TOKEN = "EAAPFihJ9FJcBSWSZBdne8dP0ngvvIbl91jPCzrVi7Ub7HdOIMK6guYcr3ZAA58x2ppYVZBSuwZC9IMx1wMPpBKyAtTkSz5uqi8O4B6VCGKa943WRBVclQNizD2gbKUkckX5TIU3KonoYk7ecTwTpuZARrXd5m1ur14hxYf5qGjNYOw8L53ELcVqdCPr5jFeZCfC7w1dZAst"

def limpar_posts_origem():
    print("🧹 Buscando posts na página promomaniaofertas para limpeza...")
    
    url_posts = f"https://graph.facebook.com/v20.0/{PAGINA_ORIGEM_ID}/posts"
    # Pega até 25 posts recentes da origem
    params = {"access_token": PAGINA_ORIGEM_TOKEN, "limit": 25}
    
    try:
        resp = requests.get(url_posts, params=params, timeout=10)
        data = resp.json()
        
        if "data" in data and data["data"]:
            posts = data["data"]
            print(f"📂 Encontrados {len(posts)} posts na origem. Apagando...")
            
            for post in posts:
                post_id = post["id"]
                url_delete = f"https://graph.facebook.com/v20.0/{post_id}"
                del_resp = requests.delete(url_delete, data={"access_token": PAGINA_ORIGEM_TOKEN}, timeout=10)
                del_data = del_resp.json()
                
                if del_data.get("success") is True:
                    print(f"  🗑️ Apagado da origem: {post_id}")
                else:
                    print(f"  ❌ Erro ao apagar {post_id}: {del_data}")
        else:
            print("📭 Nenhum post encontrado na página de origem.")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

    print("\n✨ Limpeza da origem concluída!")

if __name__ == "__main__":
    limpar_posts_origem()
    # Remove o arquivo temporário após uso
    import os
    if os.path.exists("limpar_origem.py"):
        os.remove("limpar_origem.py")
