import sys
import requests
from bs4 import BeautifulSoup
import time

def buscar_precos(termo):
    url = f"https://precodahora.ba.gov.br/produtos/?item={termo.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    while True:
        print(f"\n🔍 Buscando por: {termo}")
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print("❌ Erro ao acessar o site. Tente novamente mais tarde.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        produtos = soup.select(".produto")

        if not produtos:
            print("⚠️ Nenhum produto encontrado.")
            break

        for produto in produtos:
            descricao = produto.select_one(".descricao").text.strip()
            preco = produto.select_one(".preco").text.strip()
            estabelecimento = produto.select_one(".estabelecimento").text.strip()
            endereco = produto.select_one(".endereco").text.strip()
            telefone = produto.select_one(".telefone").text.strip() if produto.select_one(".telefone") else "Não informado"

            print(f"🛒 Produto: {descricao}")
            print(f"💰 Preço: {preco}")
            print(f"🏬 Estabelecimento: {estabelecimento}")
            print(f"📍 Endereço: {endereco}")
            print(f"📞 Telefone: {telefone}")
            print("-" * 40)

        time.sleep(60)  # Aguarda 1 minuto antes de buscar novamente

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python teste_precodahora.py <nome do produto>")
    else:
        termo_busca = " ".join(sys.argv[1:])
        buscar_precos(termo_busca)

