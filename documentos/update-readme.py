import os
from datetime import datetime
import pytz

# Constantes usadas no script
VERSAO_FILE = "versao.txt"        # Arquivo que controla a versão do README
README_FILE = "README.md"         # Arquivo README a ser gerado/atualizado
UPDATE_FILE = "update-readme.py"  # Nome deste script (para ignorar na listagem)
FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")  # Fuso horário para data/hora

def inicializar_versao():
    """
    Garante que o arquivo de versão exista.
    Se não existir, cria com valor inicial 1.
    Retorna o número da versão atual (int).
    """
    if not os.path.exists(VERSAO_FILE):
        with open(VERSAO_FILE, "w") as file:
            file.write("1")
        return 1
    with open(VERSAO_FILE, "r") as file:
        try:
            return int(file.read().strip())
        except ValueError:
            # Caso o conteúdo seja inválido, reinicia a versão em 1
            return 1

def incrementar_versao(versao_atual):
    """
    Incrementa a versão passada em 1 e salva no arquivo de controle.
    Retorna a nova versão (int).
    """
    nova_versao = versao_atual + 1
    with open(VERSAO_FILE, "w") as file:
        file.write(str(nova_versao))
    return nova_versao

def obter_data_hora_brasilia():
    """
    Obtém a data e hora atuais no fuso horário de Brasília,
    formatadas como string "dd/mm/yyyy HH:MM:SS".
    """
    agora = datetime.now(FUSO_HORARIO_BRASIL)
    return agora.strftime("%d/%m/%Y %H:%M:%S")

def listar_arquivos():
    """
    Retorna uma lista ordenada dos arquivos presentes no diretório atual,
    ignorando arquivos específicos definidos na constante 'ignorar'.
    Somente arquivos (não diretórios) são listados.
    """
    ignorar = {README_FILE, VERSAO_FILE, UPDATE_FILE, ".gitignore"}
    return sorted([
        f for f in os.listdir(".")
        if os.path.isfile(f) and f not in ignorar
    ])

def gerar_arvore(path, prefixo="", ignorar=None):
    """
    Gera uma representação em árvore do diretório 'path', recursivamente,
    semelhante ao comando 'tree' do DOS/Linux.
    
    Args:
        path (str): Caminho do diretório raiz para gerar a árvore.
        prefixo (str): Prefixo usado para criar a indentação recursiva.
        ignorar (set): Conjunto de nomes de arquivos/pastas a ignorar.
    
    Retorna:
        str: A representação em árvore do diretório.
    """
    if ignorar is None:
        ignorar = {README_FILE, VERSAO_FILE, UPDATE_FILE, ".gitignore"}

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
    """
    Cria ou sobrescreve o arquivo README.md com as informações da versão,
    data de atualização, lista de arquivos e a estrutura em árvore do diretório raiz.
    Recebe:
        - versao: número da versão atual (int)
        - data_hora: string da data/hora formatada
        - arquivos: lista de arquivos no diretório raiz
    """
    with open(README_FILE, "w", encoding="utf-8") as readme:
        readme.write("# Bem-vindo à 🍃 **CampoInteligente** \n\n")
        readme.write(
            "O **CampoInteligente**, é uma plataforma voltada para a agricultura familiar, "
            "oferecendo um chatbot com inteligência artificial que integra dados meteorológicos e de mercado "
            "para auxiliar no plantio, manejo e colheita. A navegação é simples, com foco na interação via WhatsApp.\n\n"
        )
        
        readme.write("## 📄 Lista de arquivos da raiz deste repositório, atualizada automaticamente.\n\n")
        readme.write("```\n") 
        readme.write("**Sistema:** [Campo Inteligente](https://www.campointeligente.agr.br/)\n\n")
        readme.write(f"**Versão:** {versao} (AUTO-INCREMENTO)\n\n")
        readme.write(f"**URL:** https://www.campointeligente.agr.br/\n\n")
        readme.write(f"**Data de Atualização:** {data_hora}\n\n")
        readme.write("**Responsável:** Marcos Morais\n\n")
        readme.write("\n```\n")        

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
        readme.write("\n## 📜 Licença\n\n")
        readme.write("Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n")

def copiar_readme_para_raiz():
    origem = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    destino = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    try:
        shutil.copy2(origem, destino)
        print("::notice::✅ README.md copiado para a raiz do projeto com sucesso.")
    except Exception as e:
        print(f"::error::❌ Erro ao copiar README para a raiz: {e}")

def atualizar_readme():
    """
    Função principal do script:
    - Inicializa ou lê a versão atual
    - Incrementa a versão
    - Obtém a data/hora atual em Brasília
    - Lista os arquivos do diretório atual
    - Gera o README.md com todas as informações
    """
    versao_atual = inicializar_versao()
    nova_versao = incrementar_versao(versao_atual)
    data_hora = obter_data_hora_brasilia()
    arquivos = listar_arquivos()
    gerar_readme(nova_versao, data_hora, arquivos)

if __name__ == "__main__":
    atualizar_readme()
    copiar_readme_para_raiz()
