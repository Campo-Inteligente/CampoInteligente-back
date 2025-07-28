import os
from datetime import datetime
import pytz
import shutil

# Caminho base: raiz do repositório (2 níveis acima, pois script está em .github/workflows)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

# Extensões e diretórios que devem ser ocultados na árvore
OCULTA_EXT = {".yml", ".py", ".git"}
OCULTA_DIR = {".git", ".github", ".gitignore", ".env", ".env.local", "backup-repositorio","venv", "jquery", "select2"}

# Caminhos dos arquivos dentro da pasta documentos/
DOCS_DIR = os.path.join(BASE_DIR, "documentos")
os.makedirs(DOCS_DIR, exist_ok=True)  # Garante que documentos/ exista

VERSAO_FILE = os.path.join(DOCS_DIR, "versao.txt")
README_FILE = os.path.join(DOCS_DIR, "README.md")
UPDATE_FILE = os.path.join(os.path.dirname(__file__), "update-readme.py")

# Fuso horário para data/hora
FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")


def copiar_readme_para_raiz():
    origem = README_FILE
    destino = os.path.join(BASE_DIR, "README.md")
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

        readme.write("## ℹ️ Importante \n\n")
        readme.write("ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN \n\n")
        readme.write("```\n")
        readme.write(f"Repositório..........: BACK-END\n")
        readme.write(f"Sistema..............: [Campo Inteligente](https://www.campointeligente.agr.br/)\n")
        readme.write(f"Versão...............: {versao} (AUTO-INCREMENTO)\n")
        readme.write(f"URL..................: https://www.campointeligente.agr.br/\n")
        readme.write(f"Data de Atualização..: {data_hora}\n")
        readme.write("Responsável..........: Marcos Morais\n")
        readme.write("```\n")

        readme.write("## 👥 Participantes\n\n")

        readme.write("<table style='width:100%'>\n")
        readme.write("<thead><tr>")
        readme.write("<th style='text-align:left'>Nome</th>")
        readme.write("<th style='text-align:left'>Função</th>")
        readme.write("<th style='text-align:left'>Contato</th>")
        readme.write("</tr></thead>\n")
        readme.write("<tbody>\n")
        readme.write("<tr><td>MARCOS MORAIS DE SOUSA            </td><td>Gerente de Projetos       </td><td><a href='https://www.linkedin.com/in/marcosmoraisjr/'>LinkedIn</a> | <a href='https://instagram.com/marcosmoraisjr'>Instagram</a> | <a href='mailto:mmstec@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>ARTHUR LAGO MARTINS               </td><td>Scrum Master              </td><td><a href='https://www.linkedin.com/in/arthur-martins-510b36235/'>LinkedIn</a> | <a href='https://instagram.com/arthurmarttins_'>Instagram</a> | <a href='mailto:202110445@uesb.edu.br'>Email</a></td></tr>\n")
        readme.write("<tr><td>JOÃO VICTOR OLIVEIRA SANTOS       </td><td>Ciência de Dados          </td><td><a href='https://www.linkedin.com/in/joão-victor-oliveira-santos-3b8aa1203/'>LinkedIn</a> | <a href='https://instagram.com/jv.osantos'>Instagram</a> | <a href='mailto:joao.osantos27@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>JUAN PABLO SÃO PEDRO SAPUCAIA     </td><td>Back-End                  </td><td><a href='https://www.linkedin.com/in/juan-pablo-09a65b2a6/'>LinkedIn</a> | <a href='https://instagram.com/juan_pablosps'>Instagram</a> | <a href='mailto:juan.psapucaia7@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>ABIMAEL UANDERSON S. CRISTÓVÃO    </td><td>Back-End                  </td><td><a href='https://www.linkedin.com/in/abimael-uanderson/'>LinkedIn</a> | <a href='https://instagram.com/abimaeluanderson'>Instagram</a> | <a href='mailto:abimael.servicos12dt@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>GISELE GOMES OLIVEIRA             </td><td>Front-End                 </td><td><a href='https://www.linkedin.com/in/gisele-gomes-oliveira-037bb1128/'>LinkedIn</a> | <a href='https://instagram.com/belagisa13'>Instagram</a> | <a href='mailto:belagisa14@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>FABIO SANTOS FRUTUOSO             </td><td>Front-End                 </td><td><a href='https://www.linkedin.com/in/fabio-santos-frutuoso-1784401b9/'>LinkedIn</a> | <a href='https://instagram.com/gandalfs_800'>Instagram</a> | <a href='mailto:frutuosofabio10@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>BRUNA DE QUEIROZ COSTA            </td><td>Publicidade e Processos   </td><td><a href='https://www.linkedin.com/in/bruna-queiroz-5422a7261/'>LinkedIn</a> | <a href='https://instagram.com/brhunaqueiroz'>Instagram</a> | <a href='mailto:qbruna2003@gmail.com'>Email</a></td></tr>\n")
        readme.write("<tr><td>CAMPO INTELIGENTE                 </td><td>Startup                   </td><td><a href='https://instagram.com/startupcampointeligente'>LinkedIn | <a href='https://www.instagram.com/startupcampointeligente'>Instagram</a> | <a href='mailto:startupcampointeligente@gmail.com'>Email</a></td></tr>\n")
        readme.write("</tbody>\n</table>\n\n")

        readme.write("## 🧩 Tecnologias Utilizadas\n\n")
        readme.write("<p align='left'>\n")
        readme.write("  <img src='https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white' alt='Python' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Django-3.x-092E20?logo=django&logoColor=white' alt='Django' />\n")
        readme.write("  <img src='https://img.shields.io/badge/DRF-REST_Framework-red?logo=django&logoColor=white' alt='Django REST Framework' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Django_Channels-ASGI-44B78B?logo=django&logoColor=white' alt='Django Channels' />\n")
        readme.write("  <img src='https://img.shields.io/badge/PostgreSQL-13+-4169E1?logo=postgresql&logoColor=white' alt='PostgreSQL' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Uvicorn-ASGI-121212?logo=fastapi&logoColor=white' alt='Uvicorn' />\n")
        readme.write("  <img src='https://img.shields.io/badge/Daphne-ASGI-11B5AF?logoColor=white' alt='Daphne' />\n")
        readme.write("  <img src='https://img.shields.io/badge/httpx-Async-0e83cd?logo=python&logoColor=white' alt='httpx' />\n")
        readme.write("  <img src='https://img.shields.io/badge/python--dotenv-.env-ffc107?logo=python&logoColor=black' alt='python-dotenv' />\n")
        readme.write("  <img src='https://img.shields.io/badge/OpenAI-GPT-412991?logo=openai&logoColor=white' alt='OpenAI' />\n")
        readme.write("  <img src='https://img.shields.io/badge/drf--yasg-Swagger_Integration-6DB33F?logo=swagger&logoColor=white' alt='drf-yasg' />\n")
        readme.write("  <img src='https://img.shields.io/badge/CORS-django--cors--headers-orange?logo=django&logoColor=white' alt='django-cors-headers' />\n")
        readme.write("  <img src='https://img.shields.io/badge/psycopg2--binary-PostgreSQL-blue?logo=postgresql&logoColor=white' alt='psycopg2-binary' />\n")
        readme.write("  <img src='https://img.shields.io/badge/GitHub-Repo-181717?logo=github&logoColor=white' alt='GitHub' />\n")
        readme.write("</p>\n\n")

        readme.write("Descrição das tecnologias:\n\n")
        readme.write("- **Python 3.8+**\n\n")
        readme.write("- **Django** + **Django REST Framework**\n\n")
        readme.write("- **Django Channels** + **ASGI** (suporte a WebSockets)\n\n")
        readme.write("- **PostgreSQL**\n\n")
        readme.write("- **Uvicorn** + **Daphne** (servidores assíncronos)\n\n")
        readme.write("- **httpx** (requisições HTTP assíncronas)\n\n")
        readme.write("- **python-dotenv** (variáveis de ambiente)\n\n")
        readme.write("- **openai** (integração com GPT)\n\n")
        readme.write("- **drf-yasg** (documentação Swagger/OpenAPI)\n\n")
        readme.write("- **django-cors-headers** (suporte a CORS)\n\n")
        readme.write("- **psycopg2-binary** (conector PostgreSQL)\n\n")
        readme.write("- **GitHub**: Controle de versão e colaboração no código.\n\n")

        readme.write("## 🌱 Prepare seu ambiente para reproduzir este repositório\n\n")
        readme.write("<p align='center'>\n")
        readme.write("  📘 <a href='documentos/TUTORIAL.md'><strong>Tutorial para Rodar o Repositório</strong></a>\n")
        readme.write("</p>\n\n")
        
        readme.write("## 📂 Documentos\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(os.path.join(BASE_DIR, "documentos"), OCULTA_DIR))
        readme.write("\n```\n")

        readme.write("## 🌳 Estrutura do Repositório\n\n")
        readme.write("```\n")
        readme.write(gerar_arvore(BASE_DIR, OCULTA_DIR))
        readme.write("\n```\n")

        readme.write("## 📜 Licença\n\n")
        readme.write("Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n")
        readme.write("## 🤝 Agradecimentos\n\n")
        readme.write("Contribuições, sugestões e feedbacks são muito bem-vindos! Caso tenha algum comentário ou queira contribuir com o projeto, sinta-se à vontade para abrir uma issue ou enviar um pull request.\n\n")
        readme.write("--- \n\n")
        readme.write("Desenvolvido com ❤️ pela equipe 11 | [Campo Inteligente](https://www.campointeligente.agr.br/) \n\n")


if __name__ == "__main__":
    atualizar_readme()
    copiar_readme_para_raiz()
