import requests
from bs4 import BeautifulSoup
import sys

def buscar_produto(nome_produto):
    url = f"https://precodahora.ba.gov.br/produtos/?item={nome_produto}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erro ao acessar o site: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    blocos = soup.find_all("div", class_="card-produto")

    if not blocos:
        print("⚠️ Nenhum produto encontrado.")
        return

    for bloco in blocos:
        linhas = bloco.get_text(separator="\n").split("\n")
        linhas = [linha.strip() for linha in linhas if linha.strip()]
        if len(linhas) >= 8:
            print("🧼 Produto encontrado:")
            print(f"{linhas[0]}")  # Nome do produto
            if "De R$" in linhas[1]:
                print(f"{linhas[1]}")  # Preço original
                print(f"{linhas[2]}")  # Preço com desconto
                preco_index = 3
            else:
                print(f"{linhas[1]}")  # Preço direto
                preco_index = 2
            print(f"Código de barras: {linhas[preco_index]}")
            print(f"{linhas[preco_index + 1]}")  # Tempo desde venda
            print(f"{linhas[preco_index + 2]}")  # Nome do estabelecimento
            print(f"{linhas[preco_index + 3]}")  # Endereço
            print(f"{linhas[preco_index + 4]} Km")
            if len(linhas) > preco_index + 5:
                print(f"{linhas[preco_index + 5]}")  # Telefone
            print("-" * 60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Informe o nome do produto. Exemplo: python consulta_precodahora.py sabao")
    else:
        nome = sys.argv[1]
        buscar_produto(nome)
