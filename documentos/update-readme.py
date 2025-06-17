import os
from datetime import datetime
import pytz
import shutil

# Caminho base para o diretório onde estão os arquivos do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constantes usadas no script
OCULTA_EXT = {".yml"}                                        # sempre em minúsculas para padronizar
OCULTA_DIR = {".git",".env",".env.local",".github", "documentos"}     # como conjunto, para consistência e busca rápida
VERSAO_FILE = os.path.join(BASE_DIR, "versao.txt")                    # Arquivo de versão dentro de ./documentos
README_FILE = os.path.join(BASE_DIR, "README.md")                     # README também dentro de ./documentos
UPDATE_FILE = "update-readme.py"                                      # Nome do script
FUSO_HORARIO_BRASIL = pytz.timezone("America/Sao_Paulo")              # Fuso horário

def copiar_readme_para_raiz():
    origem = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")
    destino = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.md"))
    try:
        shutil.copy2(origem, destino)
        print("::notice::✅ README.md copiado para a raiz do projeto com sucesso.")
    except Exception as e:
        print(f"::error::❌ Erro ao copiar README para a raiz: {e}")

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
        readme.write("# Bem-vindo ao 🍃**CampoInteligente**\n\n")
        readme.write(
            "O **CampoInteligente** é uma plataforma voltada para a agricultura familiar, "
            "oferecendo um chatbot com inteligência artificial que integra dados meteorológicos e de mercado "
            "para auxiliar no plantio, manejo e colheita. A navegação é simples, com foco na interação via WhatsApp.\n\n"
        )
        
        readme.write("\n## ℹ️ Importante \n\n")
        readme.write("ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN \n\n")
        readme.write("```\n")
        readme.write("Sistema..............: [Campo Inteligente](https://www.campointeligente.agr.br/)\n")
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

        # Lista simples de arquivos
        readme.write("## 📂 Listagem de Arquivos\n\n")
        readme.write("```\n")  # Bloco de código para preservar formatação
        readme.write(gerar_arvore(BASE_DIR)) # Gera a árvore do diretório atual
        readme.write("\n```\n")        

        # Seção adicional: estrutura em árvore
        readme.write("\n## 🌳 Estrutura do Repositório\n\n")
        readme.write("```\n")  # Bloco de código para preservar formatação
        readme.write(gerar_arvore(os.path.abspath(os.path.join(BASE_DIR, ".."))))  # Gera árvore da pasta informada
        readme.write("\n```\n")


        readme.write("## 🧑‍💻 Como Contribuir\n\n")
        readme.write("Contribuições são sempre bem-vindas! Para colaborar com o projeto, siga os passos abaixo:\n\n")
        readme.write("1. **Faça um Fork do Repositório**\n")
        readme.write("Clique no botão *Fork* no canto superior direito deste repositório para criar uma cópia do repositório em sua conta do GitHub.\n\n")
        readme.write("2. **Clone o Repositório**\n")
        readme.write("Clone o repositório na sua máquina local para começar a trabalhar:\n\n")
        readme.write("```bash\n")
        readme.write("git clone https://github.com/seu-usuario/CampoInteligente.git\n")
        readme.write("cd CampoInteligente\n")
        readme.write("```\n\n")
        readme.write("3. **Crie uma Branch para Sua Contribuição**\n")
        readme.write("Crie uma nova branch para a sua contribuição, garantindo que seu trabalho seja mantido separado da branch principal:\n\n")
        readme.write("```bash\n")
        readme.write("git checkout -b minha-contribuicao\n")
        readme.write("```\n\n")
        readme.write("4. **Realize as Alterações Necessárias**\n")
        readme.write("Sinta-se à vontade para editar, corrigir ou adicionar novos recursos à aplicação conforme sua necessidade.\n\n")
        readme.write("5. **Commit e Push das Alterações**\n")
        readme.write("Adicione suas alterações e faça o commit com uma mensagem descritiva:\n\n")
        readme.write("```bash\n")
        readme.write("git add .\n")
        readme.write("git commit -m \"Descrição das mudanças realizadas\"\n")
        readme.write("git push origin minha-contribuicao\n")
        readme.write("```\n\n")
        readme.write("6. **Crie um Pull Request (PR)**\n")
        readme.write("Após realizar o push da sua branch, acesse seu repositório no GitHub e crie um *Pull Request*.\n")
        readme.write("Compare a sua branch com a branch principal (`main`) do repositório original e envie para revisão.\n\n")

        readme.write("## 🛠️ Como Rodar Localmente\n\n")
        readme.write("Para rodar a aplicação localmente em seu ambiente de desenvolvimento, siga os passos abaixo.\n\n")
        readme.write("### Pré-requisitos\n")
        readme.write("Certifique-se de ter o seguinte instalado:\n\n")
        readme.write("- Node.js (versão LTS recomendada)\n")
        readme.write("- npm ou yarn (gerenciador de pacotes)\n\n")

        readme.write("### Passos para Executar o Projeto Localmente\n\n")
        readme.write("**Instale as dependências do projeto:**\n\n")
        readme.write("```bash\n")
        readme.write("npm install\n")
        readme.write("npm install framer-motion\n")
        readme.write("```\n\n")
        readme.write("**Construa o projeto:**\n\n")
        readme.write("```bash\n")
        readme.write("npx next build\n")
        readme.write("```\n\n")
        readme.write("**Execute a aplicação localmente:**\n\n")
        readme.write("```bash\n")
        readme.write("npm run dev     # Modo de Desenvolvimento\n")
        readme.write("npm run build   # Compilação para Produção\n")
        readme.write("npm run start   # Modo de Visualização\n")
        readme.write("```\n\n")
        readme.write("**Acesse a aplicação:**\n\n")
        readme.write("Abra o navegador e acesse [http://localhost:3000](http://localhost:3000) para ver a aplicação em funcionamento.\n\n")

        readme.write("**Atualize o repositório:**\n\n")
        readme.write("Após realizar alterações e verificar que tudo está funcionando localmente, envie suas modificações para o GitHub:\n\n")
        readme.write("```bash\n")
        readme.write("git add .\n")
        readme.write("git commit -m \"Mensagem explicando as mudanças\"\n")
        readme.write("git push origin minha-contribuicao\n")
        readme.write("```\n\n")


        # Lista simples de arquivos
        readme.write("## 📂 Licença\n\n")
        readme.write("Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).\n\n")

        readme.write("## 🤝 Agradecimentos\n\n")
        readme.write("Contribuições, sugestões e feedbacks são muito bem-vindos! Caso tenha algum comentário ou queira contribuir com o projeto, sinta-se à vontade para abrir uma issue ou enviar um pull request..\n\n")
        readme.write("--- \n\n")
        readme.write("Desenvolvido com ❤️ pela equipe CampoInteligente | [Campo Inteligente](https://www.campointeligente.agr.br/) \n\n")

if __name__ == "__main__":
    atualizar_readme()
    copiar_readme_para_raiz()
