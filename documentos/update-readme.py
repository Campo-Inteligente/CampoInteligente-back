import os
from datetime import datetime
import pytz
import shutil

# Caminho base para o diretório onde estão os arquivos do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constantes usadas no script
README_FILE = os.path.join(BASE_DIR, "README.md")
VERSAO_FILE = os.path.join(BASE_DIR, "versao.txt")
UPDATE_FILE = os.path.basename(__file__)  # Apenas o nome do script
FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")

def inicializar_versao():
    if not os.path.exists(VERSAO_FILE):
        with open(VERSAO_FILE, "w") as file:
            file.write("1")
        return 1
    with open(VERSAO_FILE, "r") as file:
        try:
            return int(file.read().strip())
        except ValueError:
            return 1

def incrementar_versao(versao_atual):
    nova_versao = versao_atual + 1
    with open(VERSAO_FILE, "w") as file:
        file.write(str(nova_versao))
    return nova_versao

def obter_data_hora_brasilia():
    agora = datetime.now(FUSO_HORARIO_BRASIL)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

def listar_arquivos():
    ignorar = {os.path.basename(README_FILE), os.path.basename(VERSAO_FILE), UPDATE_FILE, ".gitignore"}
    return sorted([
        f for f in os.listdir(BASE_DIR)
        if os.path.isfile(os.path.join(BASE_DIR, f)) and f not in ignorar
    ])

def gerar_arvore(path, prefixo="", ignorar=None):
    if ignorar is None:
        ignorar = {os.path.basename(README_FILE), os.path.basename(VERSAO_FILE), UPDATE_FILE, ".gitignore"}

    linhas = []
    try:
        itens = sorted([item for item in os.listdir(path) if item not in ignorar])
    except FileNotFoundError:
        return f"Diretório não encontrado: {path}"
    except PermissionError:
        return f"Permissão negada: {path}"

    total = len(itens)
    for i, item in enumerate(itens):
        caminho_item = os.path.join(path, item)
        ultimo = (i == total - 1)
        ponteiro = "└── " if ultimo else "├── "
        linhas.append(f"{prefixo}{ponteiro}{item}")
        if os.path.isdir(caminho_item):
            extensao_prefixo = "    " if ultimo else "│   "
            linhas.append(gerar_arvore(caminho_item, prefixo + extensao_prefixo, ignorar))

    return "\n".join(linhas)

def gerar_readme(versao, data_hora, arquivos):
    with open(README_FILE, "w", encoding="utf-8") as readme:
        readme.write("# Bem-vindo à **WeaveTrip**\n\n")
        readme.write(
            "A **WeaveTrip** é um sistema B2C, com arquitetura baseada em APIs, que integra serviços de passagens, hospedagem e eventos em uma única interface. Diferencial marcante: Montagem de viagens totalmente sob demanda em um só lugar, com UX centrada no usuário e arquitetura API-first que permite integrações futuras com marketplaces e apps de experiência — indo além das agências tradicionais.\n\n"
        )

        readme.write("<br /><br />")
        readme.write("\n## ℹ️ Importante \n\n")
        readme.write("```ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN ```\n\n")
        readme.write("**Sistema:** [WeaveTrip](https://www.WeaveTrip.tours.br/)\n\n")
        readme.write(f"**Versão:** {versao} (AUTO-INCREMENTO)\n\n")
        readme.write(f"**URL:** https://www.WeaveTrip.tours.br/\n\n")
        readme.write(f"**Data de Atualização:** {data_hora}\n\n")
        readme.write("**Responsável:** Marcos Morais\n\n")
        
        readme.write("<br /><br />")
        readme.write("\n## 🧩 Tecnologias Utilizadas \n\n")
        readme.write("<p align='left'> \n")
        readme.write("  <img src='https://img.shields.io/badge/Next.js-13.x-black?logo=next.js&logoColor=white' alt='Next.js' />\n")
        readme.write("  <img src='https://img.shields.io/badge/React-18.x-61DAFB?logo=react&logoColor=white' alt='React' />\n")
        readme.write("  <img src='https://img.shields.io/badge/TypeScript-4.x-3178c6?logo=typescript&logoColor=white' alt='TypeScript' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC?logo=tailwindcss&logoColor=white' alt='Tailwind CSS' />\n")
        readme.write("  <img src='https://img.shields.io/badge/GraphQL-2023E7?logo=graphql&logoColor=white' alt='GraphQL' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Apollo_Client-311C87?logo=apollo-graphql&logoColor=white' alt='Apollo Client' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Figma-F24E1E?logo=figma&logoColor=white' alt='Figma' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Axios-5A29E4?logo=axios&logoColor=white' alt='Axios' />\n")
        readme.write("<p /> \n")

        readme.write("<br /><br />")
        readme.write("\n## 🎨 Protótipo no Figma \n\n")
        readme.write("O design da interface do usuário está disponível no Figma. Ele foi pensado para proporcionar uma experiência fluida, acessível e agradável.\n\n")
        readme.write("🔗 Link do protótipo: [Figma - WeaveTrip](https://www.figma.com/design/i8ipqOKX0czzeilS9JsMR3/MVP----Restic36?node-id=1-2&t=QV1Mwbs9NK1MDy6H-1)\n\n")

        readme.write("<br /><br />")
        readme.write("\n## 📂 Documentos\n\n")
        readme.write("Lista de arquivos da pasta `documentos/`, atualizada automaticamente.\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(BASE_DIR))
        readme.write("\n```\n")

        readme.write("<br /><br />")
        readme.write("\n## 🌳 Estrutura do Repositório\n\n")
        readme.write("Lista de arquivos no `repositório`, atualizada automaticamente.\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(os.path.abspath(os.path.join(BASE_DIR, ".."))))
        readme.write("\n```\n")

        readme.write("<br /><br />")
        readme.write("\n## 🚀 Como rodar o projeto\n\n")
        readme.write("Clone este repositório:\n\n")
        readme.write("```bash\n")
        readme.write("git clone https://github.com/seu-usuario/weavetrip-frontend.git\n")
        readme.write("```\n\n")
        readme.write("Instale as dependências:\n\n")
        readme.write("```bash\n")
        readme.write("npm install\n")
        readme.write("# ou\\n")
        readme.write("yarn install\n")
        readme.write("```\n\n")
        readme.write("Crie o arquivo .env.local com as variáveis necessárias:\n\n")
        readme.write("```env\n")
        readme.write("NEXT_PUBLIC_GRAPHQL_API=https://seu-endpoint.com/graphql\n")
        readme.write("```\n\n")
        readme.write("Rode o projeto:\n\n")
        readme.write("```bash\n")
        readme.write("npm run dev\n")
        readme.write("# ou\n")
        readme.write("yarn dev\n")
        readme.write("```\n\n")
        readme.write("Acesse no navegador: http://localhost:3000\n\n")

        readme.write("<br /><br />")
        readme.write("\n## 🔗 Integração com o Backend\n\n")
        readme.write("Este frontend se comunica com uma API GraphQL, que está disponível no repositório WeaveTrip Backend. É necessário que o backend esteja em funcionamento para que as funcionalidades do front operem corretamente.\n\n")

        readme.write("\n## 🖼️ Telas da Aplicação\n\n")
        readme.write("A seguir, algumas telas do MVP WeaveTrip para ilustrar a experiência do usuário na plataforma:\n\n")
        readme.write("🔐 **Tela de Login**\n\n")
        readme.write("Interface de autenticação, onde o usuário acessa a plataforma com suas credenciais.\n\n")
        readme.write("![Login](https://github.com/user-attachments/assets/9523605e-b3ab-4db9-9bf6-7f7f0a719c3f)\n\n")
        readme.write("🏠 **Tela Inicial (Home)**\n\n")
        readme.write("Tela principal exibida após o login, com informações da viagem, participantes e opções de navegação.\n\n")
        readme.write("![Home](https://github.com/user-attachments/assets/71f61cb1-e2f7-4786-82c2-23a0cd3c4058)\n\n")
        readme.write("---\n\n")
        
        readme.write("<br /><br />")
        readme.write("\n## 📜 Licença\n\n")
        readme.write("Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n")

def atualizar_readme():
    versao_atual = inicializar_versao()
    nova_versao = incrementar_versao(versao_atual)
    data_hora = obter_data_hora_brasilia()
    arquivos = listar_arquivos()
    gerar_readme(nova_versao, data_hora, arquivos)

def copiar_readme_para_raiz():
    origem = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    destino = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    try:
        shutil.copy2(origem, destino)
        print("::notice::✅ README.md copiado para a raiz do projeto com sucesso.")
    except Exception as e:
        print(f"::error::❌ Erro ao copiar README para a raiz: {e}")
        
if __name__ == "__main__":
    atualizar_readme()
    copiar_readme_para_raiz()
