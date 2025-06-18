import os
from datetime import datetime
import pytz
import shutil

# Caminho base para o diretório onde estão os arquivos do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Extensões e diretórios que devem ser ocultados na árvore
OCULTA_EXT = {".yml",".py",".md"}
OCULTA_DIR = {".git", ".github", ".gitignore", ".env", ".env.local"}

# Arquivos importantes
VERSAO_FILE = os.path.join(BASE_DIR, "versao.txt")
README_FILE = os.path.join(BASE_DIR, "README.md")
UPDATE_FILE = "update-readme.py"

# Fuso horário para data/hora
FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")


def copiar_readme_para_raiz():
    origem = os.path.join(BASE_DIR, "README.md")
    destino = os.path.abspath(os.path.join(BASE_DIR, "..", "README.md"))
    try:
        shutil.copy2(origem, destino)
        print("::notice::✅ README.md copiado para a raiz do projeto com sucesso.")
    except Exception as e:
        print(f"::error::❌ Erro ao copiar README para a raiz: {e}")


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


def gerar_arvore(path, ignorar=None, prefixo="", is_root=True, nome_raiz=None):
    ignorar = set(ignorar) if ignorar else set()
    linhas = []

    #if is_root:
    #    nome_raiz = nome_raiz or os.path.basename(path)
    #    linhas.append(f"🗂️ {nome_raiz}")
    
    if is_root:
        if nome_raiz is None:
            nome_raiz = os.path.basename(os.path.normpath(path)) or "."
        linhas.append(f"📂 {nome_raiz}")

    try:
        itens = sorted(os.listdir(path))
    except (FileNotFoundError, PermissionError) as e:
        return f"{prefixo}[Erro ao acessar {path}: {e}]"

    itens_filtrados = []
    for item in itens:
        if item in ignorar:
            continue
        caminho_item = os.path.join(path, item)
        if os.path.isdir(caminho_item):
            itens_filtrados.append(item)
        else:
            ext = os.path.splitext(item)[1].lower()
            if ext not in OCULTA_EXT:
                itens_filtrados.append(item)

    total = len(itens_filtrados)
    for i, item in enumerate(itens_filtrados):
        caminho_item = os.path.join(path, item)
        ultimo = (i == total - 1)
        ponteiro = "└── " if ultimo else "├── "

        if os.path.isdir(caminho_item):
            # Verifica se a pasta tem conteúdo relevante (não ignorado e visível)
            try:
                conteudo_dir = [
                    f for f in os.listdir(caminho_item)
                    if f not in ignorar and (
                        os.path.isdir(os.path.join(caminho_item, f)) or
                        os.path.splitext(f)[1].lower() not in OCULTA_EXT
                    )
                ]
            except (FileNotFoundError, PermissionError):
                conteudo_dir = []

            emoji = "📂" if conteudo_dir else "🗂️"
            linhas.append(f"{prefixo}{ponteiro}{emoji} {item}")

            if conteudo_dir:
                novo_prefixo = prefixo + ("    " if ultimo else "│   ")
                subarvore = gerar_arvore(caminho_item, ignorar, novo_prefixo, is_root=False)
                linhas.append(subarvore)
        else:
            linhas.append(f"{prefixo}{ponteiro}📄 {item}")

    return "\n".join(linhas)


def atualizar_readme():
    versao_atual = inicializar_versao()
    nova_versao = incrementar_versao(versao_atual)
    data_hora = obter_data_hora_brasilia()
    gerar_readme(nova_versao, data_hora)


def gerar_readme(versao, data_hora):
    with open(README_FILE, "w", encoding="utf-8") as readme:
        readme.write("# Bem-vindo ao 🍃**CampoInteligente**\n\n")
        readme.write(
            "O **CampoInteligente** é uma plataforma voltada para a agricultura familiar, "
            "oferecendo um chatbot com inteligência artificial que integra dados meteorológicos e de mercado "
            "para auxiliar no plantio, manejo e colheita. A navegação é simples, com foco na interação via WhatsApp.\n\n"
        )

        readme.write("\n## ℹ️ Importante \n\n")
        readme.write("ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN \n\n")
        readme.write("```\n")
        readme.write(f"Sistema..............: [Campo Inteligente](https://www.campointeligente.agr.br/)\n")
        readme.write(f"Versão...............: {versao} (AUTO-INCREMENTO)\n")
        readme.write(f"URL..................: https://www.campointeligente.agr.br/\n")
        readme.write(f"Data de Atualização..: {data_hora}\n")
        readme.write("Responsável..........: Marcos Morais\n")
        readme.write("```\n")

        readme.write("## 🧩 Tecnologias Utilizadas\n\n")
        readme.write("<p align='left'>\n")
        readme.write("  <img src='https://img.shields.io/badge/Figma-F24E1E?logo=figma&logoColor=white' alt='Figma' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Next.js-13.x-black?logo=next.js&logoColor=white' alt='Next.js' />\n")
        readme.write("  <img src='https://img.shields.io/badge/React-18.x-61DAFB?logo=react&logoColor=white' alt='React' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC?logo=tailwindcss&logoColor=white' alt='Tailwind CSS' />\n")
        readme.write("  <img src='https://img.shields.io/badge/GitHub-100000?logo=github&logoColor=white&style=flat' alt='GitHub' />\n")
        readme.write("</p>\n\n")

        readme.write("### Descrição das tecnologias:\n\n")
        readme.write("- **Next.js**: Framework React para criação de aplicações web escaláveis e de alto desempenho.\n")
        readme.write("- **React**: Biblioteca JavaScript para construção de interfaces de usuário interativas.\n")
        readme.write("- **Tailwind CSS**: Framework CSS para estilização rápida e personalizada.\n")
        readme.write("- **GitHub**: Controle de versão e colaboração no código.\n\n")

        readme.write("## 📂 Documentos\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore("./documentos", OCULTA_DIR))
        readme.write("\n```\n")

        readme.write("## 🌳 Estrutura do Repositório\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore("./", OCULTA_DIR))
        readme.write("\n```\n")

        readme.write("## 📜 Licença\n\n")
        readme.write("Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n")
        readme.write("## 🤝 Agradecimentos\n\n")
        readme.write("Contribuições, sugestões e feedbacks são muito bem-vindos! Caso tenha algum comentário ou queira contribuir com o projeto, sinta-se à vontade para abrir uma issue ou enviar um pull request.\n\n")
        readme.write("--- \n\n")
        readme.write("Desenvolvido com ❤️ pela equipe CampoInteligente | [Campo Inteligente](https://www.campointeligente.agr.br/) \n\n")


if __name__ == "__main__":
    atualizar_readme()
    copiar_readme_para_raiz()
