# Bem-vindo à 🍃 **CampoInteligente** 

O **CampoInteligente**, é uma plataforma voltada para a agricultura familiar, oferecendo um chatbot com inteligência artificial que integra dados meteorológicos e de mercado para auxiliar no plantio, manejo e colheita. A navegação é simples, com foco na interação via WhatsApp.

## 📄 Lista de arquivos da raiz deste repositório, atualizada automaticamente.

**Sistema:** [Campo Inteligente](https://www.campointeligente.agr.br/)

**Versão:** 2 (AUTO-INCREMENTO)

**URL:** https://www.campointeligente.agr.br/

**Data de Atualização:** 17/06/2025 15:23:45

**Responsável:** Marcos Morais

## 📂 Listagem de Arquivos

```
├── .env
├── .git
│   ├── FETCH_HEAD
│   ├── HEAD
│   ├── config
│   ├── description
│   ├── hooks
│   │   ├── applypatch-msg.sample
│   │   ├── commit-msg.sample
│   │   ├── fsmonitor-watchman.sample
│   │   ├── post-update.sample
│   │   ├── pre-applypatch.sample
│   │   ├── pre-commit.sample
│   │   ├── pre-merge-commit.sample
│   │   ├── pre-push.sample
│   │   ├── pre-rebase.sample
│   │   ├── pre-receive.sample
│   │   ├── prepare-commit-msg.sample
│   │   ├── push-to-checkout.sample
│   │   ├── sendemail-validate.sample
│   │   └── update.sample
│   ├── index
│   ├── info
│   │   └── exclude
│   ├── logs
│   │   ├── HEAD
│   │   └── refs
│   │       ├── heads
│   │       │   └── main
│   │       └── remotes
│   │           └── origin
│   │               ├── HEAD
│   │               └── main
│   ├── objects
│   │   ├── 02
│   │   │   └── 8875767e5067f8263836cb56a050b25b959df0
│   │   ├── 0a
│   │   │   └── 158f3b4f5b3917f4a4ad3b86c9dbaf61603ff8
│   │   ├── 24
│   │   │   └── 9a50de1dacd00c3fa5dd14f01b690ff6a23809
│   │   ├── 28
│   │   │   └── 4718be433432cf7d84fe477e3e559d7b2b1855
│   │   ├── 3a
│   │   │   └── 69bd5578baca0fbf15c27a9efa3de9417cb649
│   │   ├── 3c
│   │   │   └── 7e98ea3b4edc04f85dbc2903760e8f37a084a4
│   │   ├── 40
│   │   │   └── 464f837b223d75e139f48316d20f62147425eb
│   │   ├── 51
│   │   │   └── f3e7f026b8a3a25c8e8f4653de436bfd599204
│   │   ├── 75
│   │   │   └── bfce93d147e2bdaea7a7e44d8acc850dd1cae4
│   │   ├── 80
│   │   │   └── 1f1801027f3350b08ad85c984db805cd32e736
│   │   ├── 8a
│   │   │   └── 595a798f04a5db143f934dcb2c46be62c875d6
│   │   ├── 91
│   │   │   └── eec88691f99a70f49d6aa5495b1da000da7226
│   │   ├── ac
│   │   │   └── 578562de24fc5922955434f02c702ecda6a614
│   │   ├── af
│   │   │   └── a5c6f6008fd49de9dc775657851a43ed8af8da
│   │   ├── c3
│   │   │   └── 423e883d6db8ac8cb43e1ab07021f306693e2e
│   │   ├── c6
│   │   │   └── f35db6ace59bd3298edc265f0ca4aa669692ab
│   │   ├── d3
│   │   │   └── 660e9cecf95d68c17af5844ff7981364733c26
│   │   ├── df
│   │   │   └── c26fca0a4b138a054d2076d8807400594659bf
│   │   ├── e1
│   │   │   └── 6a1ea33f7b56433b15f0375ebc175b73f4a791
│   │   ├── e6
│   │   │   └── 9de29bb2d1d6434b8b29ae775ad8c2e48c5391
│   │   ├── f6
│   │   │   └── 71f6764b92a474b756af02385ccde70aeb17a8
│   │   ├── fb
│   │   │   └── 220f0eeed65e2eda62ad5f280ca36e8cc1373a
│   │   ├── info

│   │   └── pack

│   ├── refs
│   │   ├── heads
│   │   │   └── main
│   │   ├── remotes
│   │   │   └── origin
│   │   │       ├── HEAD
│   │   │       └── main
│   │   └── tags

│   └── shallow
├── .github
│   └── workflows
│       └── update-readme.yml
├── Dockerfile
├── OBSERVAÇÕES SOBRE OS CODIGOS
├── chatbot.py
├── chatbotR.py
├── db
│   └── conexao.py
├── docker-compose.yml
├── documentos
│   ├── LICENSE
│   └── requirements.txt
└── requirements.txt
```

## 🌳 Estrutura do Repositório

```
└── startup-campo-inteligente-back
    ├── .env
    ├── .git
    │   ├── FETCH_HEAD
    │   ├── HEAD
    │   ├── config
    │   ├── description
    │   ├── hooks
    │   │   ├── applypatch-msg.sample
    │   │   ├── commit-msg.sample
    │   │   ├── fsmonitor-watchman.sample
    │   │   ├── post-update.sample
    │   │   ├── pre-applypatch.sample
    │   │   ├── pre-commit.sample
    │   │   ├── pre-merge-commit.sample
    │   │   ├── pre-push.sample
    │   │   ├── pre-rebase.sample
    │   │   ├── pre-receive.sample
    │   │   ├── prepare-commit-msg.sample
    │   │   ├── push-to-checkout.sample
    │   │   ├── sendemail-validate.sample
    │   │   └── update.sample
    │   ├── index
    │   ├── info
    │   │   └── exclude
    │   ├── logs
    │   │   ├── HEAD
    │   │   └── refs
    │   │       ├── heads
    │   │       │   └── main
    │   │       └── remotes
    │   │           └── origin
    │   │               ├── HEAD
    │   │               └── main
    │   ├── objects
    │   │   ├── 02
    │   │   │   └── 8875767e5067f8263836cb56a050b25b959df0
    │   │   ├── 0a
    │   │   │   └── 158f3b4f5b3917f4a4ad3b86c9dbaf61603ff8
    │   │   ├── 24
    │   │   │   └── 9a50de1dacd00c3fa5dd14f01b690ff6a23809
    │   │   ├── 28
    │   │   │   └── 4718be433432cf7d84fe477e3e559d7b2b1855
    │   │   ├── 3a
    │   │   │   └── 69bd5578baca0fbf15c27a9efa3de9417cb649
    │   │   ├── 3c
    │   │   │   └── 7e98ea3b4edc04f85dbc2903760e8f37a084a4
    │   │   ├── 40
    │   │   │   └── 464f837b223d75e139f48316d20f62147425eb
    │   │   ├── 51
    │   │   │   └── f3e7f026b8a3a25c8e8f4653de436bfd599204
    │   │   ├── 75
    │   │   │   └── bfce93d147e2bdaea7a7e44d8acc850dd1cae4
    │   │   ├── 80
    │   │   │   └── 1f1801027f3350b08ad85c984db805cd32e736
    │   │   ├── 8a
    │   │   │   └── 595a798f04a5db143f934dcb2c46be62c875d6
    │   │   ├── 91
    │   │   │   └── eec88691f99a70f49d6aa5495b1da000da7226
    │   │   ├── ac
    │   │   │   └── 578562de24fc5922955434f02c702ecda6a614
    │   │   ├── af
    │   │   │   └── a5c6f6008fd49de9dc775657851a43ed8af8da
    │   │   ├── c3
    │   │   │   └── 423e883d6db8ac8cb43e1ab07021f306693e2e
    │   │   ├── c6
    │   │   │   └── f35db6ace59bd3298edc265f0ca4aa669692ab
    │   │   ├── d3
    │   │   │   └── 660e9cecf95d68c17af5844ff7981364733c26
    │   │   ├── df
    │   │   │   └── c26fca0a4b138a054d2076d8807400594659bf
    │   │   ├── e1
    │   │   │   └── 6a1ea33f7b56433b15f0375ebc175b73f4a791
    │   │   ├── e6
    │   │   │   └── 9de29bb2d1d6434b8b29ae775ad8c2e48c5391
    │   │   ├── f6
    │   │   │   └── 71f6764b92a474b756af02385ccde70aeb17a8
    │   │   ├── fb
    │   │   │   └── 220f0eeed65e2eda62ad5f280ca36e8cc1373a
    │   │   ├── info

    │   │   └── pack

    │   ├── refs
    │   │   ├── heads
    │   │   │   └── main
    │   │   ├── remotes
    │   │   │   └── origin
    │   │   │       ├── HEAD
    │   │   │       └── main
    │   │   └── tags

    │   └── shallow
    ├── .github
    │   └── workflows
    │       └── update-readme.yml
    ├── Dockerfile
    ├── OBSERVAÇÕES SOBRE OS CODIGOS
    ├── chatbot.py
    ├── chatbotR.py
    ├── db
    │   └── conexao.py
    ├── docker-compose.yml
    ├── documentos
    │   ├── LICENSE
    │   └── requirements.txt
    └── requirements.txt
```
<br /><br />
## 📜 Licença

Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).

