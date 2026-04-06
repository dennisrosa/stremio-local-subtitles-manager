<h1 align="center">🎬 SLSM - Stremio Local Subtitles Manager</h1>

<p align="center">
  <em>Um framework em Python (Flask) para gerenciamento passivo e submissão massiva de legendas locais em seu player Stremio, controladas numa Single Page Application robusta e multilinguagem.</em>
</p>

---

## ⚡ O que o SLSM resolve?
Você já passou raiva baixando legendas manuais que o Stremio não encontra oficialmente nas fontes externas, mas odeia a burocracia de criar arquivos e pastas com a nomenclatura que o Add-on pede no seu sistema de disco local C:/ ou D:/?

Nasceu o **Stremio Local Subtitles Manager (SLSM)**! Um addon que atua como um ouvinte local. Na requisição inicial o seu Stremio buscará a legenda para algum filme. Se não possuir, o App guarda o "pedido" pendente na memória (Staging Area). Você - Sysadmin da sua máquina - entra na área de gerência Web UI em qualquer navegador, e com **apenas 1 Clique** ("Autorizar Todas"), toda a estrutura hierárquica física vazia de Pastas (Movie ID / Seasons / Episodes) é automaticamente gerada e enraizada no HD. Depois, basta fazer os Uploads ali mesmo com um belo grid visual da Cinemeta API da sua própria casa!

## ✨ Funcionalidades
- **🎯 Smart Auto-Staging:** Capta os erros orgânicos da falta de legendas durante seu uso natural de TV/Stremio e documenta as carências para sua devida revisão e aprovação.
- **📁 Gerência de Repositório Dinâmico:** Visualização limpa através do "Mega Grid Card", onde é filtrado séries por folhas de episódios poupando poluição. O Web Server busca Títulos e Posters interativos usando API oficial pública da Cinemeta.
- **🌐 Suporte Nativo a Multi-Ideomas (i18n):** Todo o painel traduz instântaneamente (Client-Side Vanilla JS) p/ Português do Brasil (PT-BR) e Inglês Universal (EN) preservados no Cache! E auto-classificação internacional para as bandeiras de legenda (.eng, .per, .pt).
- **🚀 Upload Inline Simplificado:** Sistema sem fricção para bater o mouse e empurrar direto do seu Windows Explorer à pasta almejada com validação robusta por trás!

## 📦 Instalação Fácil (CLI Daemon)

O SLSM foi projetado como um módulo que acorda executáveis globais, injeta ele direto no Path:
Ou instale diretamente do código do Git:
```bash
git clone https://github.com/dennisrosa/stremio-local-subtitles-manager.git
cd stremio-local-subtitles-manager
pip install -e .
```

## 🎮 Iniciando & Uso da Interface CLI (Command Line Engine)
Terminada a instalação pip, você ganhou acesso em definitivo ao comando `slsm-server` rodando isoladamente em qualquer Powershell, Bash ou CMD do seu ambiente.

Inicie com configurações base, chamando a porta universal `3001`:
```bash
slsm-server
```

### Comandos de Customização Hacker
Você é o dono da rede. Escolha as entradas personalizadas se desejar mapear servidores num NAS, SSD, ou Drive Externo customizado em qualquer porta do Roteador (ex: `:8080`)
```bash
slsm-server --port 8080 --storage-path "D:\Minhas_Series\LegendasTV"
```

## 📺 Integrando & Lincando seu Stremio à Base
Simples! O server deve estar Online. E então, insira no link raiz o final com `/manifest.json`, veja:
Abra seu Desktop App Oficial do Stremio e dispare o endereço de instalação interna.
Ou cole este botão mágico no navegador e veja ser requisitado em milissegundos:
> `stremio://localhost:3001/manifest.json` *(Substitua a porta local caso trocou no CLI!)*

![Screenshot App](https://i.imgur.com/qUa6aFn.png) *(Imagem de Exemplo Ilustrativa)*

---

### Licença
Software Livre mantido em contribuição ao ecossistema OpenSource com carinho. Use e Modifique à vontade! 🚀
