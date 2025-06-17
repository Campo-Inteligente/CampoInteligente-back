# Bem-vindo à **WeaveTrip**

A **WeaveTrip** é um sistema B2C, com arquitetura baseada em APIs, que integra serviços de passagens, hospedagem e eventos em uma única interface. Diferencial marcante: Montagem de viagens totalmente sob demanda em um só lugar, com UX centrada no usuário e arquitetura API-first que permite integrações futuras com marketplaces e apps de experiência — indo além das agências tradicionais.

<br /><br />
## ℹ️ Importante 

```ESTE README É ATUALIZADO AUTOMATICAMENTE A CADA COMMIT NA MAIN ```

**Sistema:** [WeaveTrip](https://www.WeaveTrip.tours.br/)

**Versão:** 41 (AUTO-INCREMENTO)

**URL:** https://www.WeaveTrip.tours.br/

**Data de Atualização:** 17/06/2025 12:45:14

**Responsável:** Marcos Morais

<br /><br />
## 🧩 Tecnologias Utilizadas 

<p align='left'> 
  <img src='https://img.shields.io/badge/Next.js-13.x-black?logo=next.js&logoColor=white' alt='Next.js' />
  <img src='https://img.shields.io/badge/React-18.x-61DAFB?logo=react&logoColor=white' alt='React' />
  <img src='https://img.shields.io/badge/TypeScript-4.x-3178c6?logo=typescript&logoColor=white' alt='TypeScript' />
  <img src='https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC?logo=tailwindcss&logoColor=white' alt='Tailwind CSS' />
  <img src='https://img.shields.io/badge/GraphQL-2023E7?logo=graphql&logoColor=white' alt='GraphQL' />
  <img src='https://img.shields.io/badge/Apollo_Client-311C87?logo=apollo-graphql&logoColor=white' alt='Apollo Client' />
  <img src='https://img.shields.io/badge/Figma-F24E1E?logo=figma&logoColor=white' alt='Figma' />
  <img src='https://img.shields.io/badge/Axios-5A29E4?logo=axios&logoColor=white' alt='Axios' />
<p /> 
<br /><br />
## 🎨 Protótipo no Figma 

O design da interface do usuário está disponível no Figma. Ele foi pensado para proporcionar uma experiência fluida, acessível e agradável.

🔗 Link do protótipo: [Figma - WeaveTrip](https://www.figma.com/design/i8ipqOKX0czzeilS9JsMR3/MVP----Restic36?node-id=1-2&t=QV1Mwbs9NK1MDy6H-1)

<br /><br />
## 📂 Documentos

Lista de arquivos da pasta `documentos/`, atualizada automaticamente.

```
├── LICENSE
└── requirements.txt
```
<br /><br />
## 🌳 Estrutura do Repositório

Lista de arquivos no `repositório`, atualizada automaticamente.

```
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
│   │   ├── info

│   │   └── pack
│   │       ├── pack-c00370e3c5421e813736e085dbf9ae2657fbcaac.idx
│   │       ├── pack-c00370e3c5421e813736e085dbf9ae2657fbcaac.pack
│   │       └── pack-c00370e3c5421e813736e085dbf9ae2657fbcaac.rev
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
│       ├── update-readme.yml
│       └── update-readme.yml-bkp
├── app
│   ├── assets
│   │   └── image
│   │       ├── WeaveTrip.jpg
│   │       ├── image1.jpg
│   │       ├── image2.jpg
│   │       ├── image3.jpg
│   │       └── profile.webp
│   ├── components
│   │   ├── ButtonHome
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── ButtonLogar
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── ButtonModal
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── CardProduct
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── CardTitle
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── CardUser
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── Cards
│   │   │   ├── DestinationCard
│   │   │   │   └── index.tsx
│   │   │   ├── ExperienceCard
│   │   │   │   ├── index.tsx
│   │   │   │   └── style.css
│   │   │   └── PromotionCard
│   │   │       └── index.tsx
│   │   ├── Compras
│   │   │   ├── Button
│   │   │   │   └── index.tsx
│   │   │   ├── Card
│   │   │   │   └── index.tsx
│   │   │   ├── DetalhesBtn
│   │   │   │   └── index.tsx
│   │   │   ├── Nav
│   │   │   │   └── index.tsx
│   │   │   ├── ResumoPedido
│   │   │   │   └── index.tsx
│   │   │   ├── Table
│   │   │   │   ├── Td
│   │   │   │   │   └── index.tsx
│   │   │   │   ├── Th
│   │   │   │   │   └── index.tsx
│   │   │   │   └── index.tsx
│   │   │   └── Tag
│   │   │       └── index.tsx
│   │   ├── DetalheProduto
│   │   │   ├── Buttons
│   │   │   │   ├── PrimaryButton.tsx
│   │   │   │   └── SecondaryButton.tsx
│   │   │   ├── ImageGallery
│   │   │   │   └── index.tsx
│   │   │   ├── Rate
│   │   │   │   └── index.tsx
│   │   │   ├── Select
│   │   │   │   └── index.tsx
│   │   │   └── Tag
│   │   │       └── index.tsx
│   │   ├── EditUserModal
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── Footer
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── Hr
│   │   │   └── index.tsx
│   │   ├── InputCadastro
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── InputModal
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── LayoutHome
│   │   │   ├── Avatar
│   │   │   │   └── index.tsx
│   │   │   ├── Button
│   │   │   │   └── index.tsx
│   │   │   ├── SideBar
│   │   │   │   ├── NavItem
│   │   │   │   │   └── index.tsx
│   │   │   │   └── index.tsx
│   │   │   └── index.tsx
│   │   ├── Menu
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── NavUser
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── ProductTable
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── Profile
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── RecuperarSenha
│   │   │   ├── Button.tsx
│   │   │   ├── InputData.tsx
│   │   │   ├── RecuperarSenhaStep.tsx
│   │   │   └── SectionHeader.tsx
│   │   ├── SearchSection
│   │   │   ├── SearchDestiny
│   │   │   │   └── index.tsx
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── SelectModal
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   ├── StaticCard
│   │   │   ├── index.tsx
│   │   │   └── styles.css
│   │   ├── UploadImage
│   │   │   ├── index.tsx
│   │   │   └── style.css
│   │   └── UserTable
│   │       ├── index.tsx
│   │       └── style.css
│   ├── globals.css
│   ├── hooks
│   │   └── useAuth.tsx
│   ├── layout.tsx
│   ├── models
│   │   ├── product.ts
│   │   └── user.ts
│   ├── page.module.css
│   ├── page.tsx
│   ├── pages
│   │   ├── cadastro
│   │   │   ├── page.tsx
│   │   │   └── styles.css
│   │   ├── carrinho
│   │   │   └── page.tsx
│   │   ├── configuracao
│   │   │   ├── page.tsx
│   │   │   └── styles.css
│   │   ├── detalheProduto
│   │   │   └── page.tsx
│   │   ├── home
│   │   │   ├── page.tsx
│   │   │   └── style.css
│   │   ├── login
│   │   │   ├── page.tsx
│   │   │   └── styles.css
│   │   ├── minhasCompras
│   │   │   └── page.tsx
│   │   ├── painelcontrole
│   │   │   ├── page.tsx
│   │   │   └── styles.css
│   │   ├── produtocadastrado
│   │   │   ├── page.tsx
│   │   │   └── style.css
│   │   ├── produtoeditar
│   │   │   └── [id]
│   │   │       ├── page.tsx
│   │   │       └── styles.css
│   │   ├── profileclient
│   │   │   ├── page.tsx
│   │   │   └── styles.css
│   │   ├── recuperarSenha
│   │   │   └── page.tsx
│   │   ├── usuariocadastrado
│   │   │   ├── page.tsx
│   │   │   └── style.css
│   │   └── usuarioeditar
│   │       └── [id]
│   │           ├── page.tsx
│   │           └── styles.css
│   └── service
│       ├── ApolloProvider.tsx
│       ├── api.ts
│       ├── apollo.ts
│       └── queries.ts
├── db.json
├── documentos
│   ├── LICENSE
│   └── requirements.txt
├── eslint.config.mjs
├── next.config.ts
├── package-lock.json
├── package.json
├── postcss.config.mjs
├── public
│   └── logo-header.svg
├── tsconfig.json
└── yarn.lock
```
<br /><br />
## 🚀 Como rodar o projeto

Clone este repositório:

```bash
git clone https://github.com/seu-usuario/weavetrip-frontend.git
```

Instale as dependências:

```bash
npm install
# ou\nyarn install
```

Crie o arquivo .env.local com as variáveis necessárias:

```env
NEXT_PUBLIC_GRAPHQL_API=https://seu-endpoint.com/graphql
```

Rode o projeto:

```bash
npm run dev
# ou
yarn dev
```

Acesse no navegador: http://localhost:3000

<br /><br />
## 🔗 Integração com o Backend

Este frontend se comunica com uma API GraphQL, que está disponível no repositório WeaveTrip Backend. É necessário que o backend esteja em funcionamento para que as funcionalidades do front operem corretamente.


## 🖼️ Telas da Aplicação

A seguir, algumas telas do MVP WeaveTrip para ilustrar a experiência do usuário na plataforma:

🔐 **Tela de Login**

Interface de autenticação, onde o usuário acessa a plataforma com suas credenciais.

![Login](https://github.com/user-attachments/assets/9523605e-b3ab-4db9-9bf6-7f7f0a719c3f)

🏠 **Tela Inicial (Home)**

Tela principal exibida após o login, com informações da viagem, participantes e opções de navegação.

![Home](https://github.com/user-attachments/assets/71f61cb1-e2f7-4786-82c2-23a0cd3c4058)

---

<br /><br />
## 📜 Licença

Este projeto está licenciado sob os termos do arquivo [LICENSE](./documentos/LICENSE).

