# Product Requirements Document (PRD) – Versão 3.0
**Stremio Local Subtitles Manager – Python + Flask**
*(Com Staging Automático via Stremio, Criação Autorizada de Pastas e Upload Posterior)*

## 1. Executive Summary
**Product Name:** Stremio Local Subtitles Manager – com controle de estrutura e permissão

**Goal:**
Desenvolver um servidor web local (Python/Flask) que intercepta as chamadas de busca de legendas do Stremio. Na requisição, se a legenda já existir salva no disco, ela é devolvida. Se não existir, a API **não aciona nenhum file upload** naquele momento. Em vez disso, ela registra essa busca de usuário (identificando filme/série, temporada, episódio e idioma) em uma área de "staging" em memória. O mantenedor do servidor (usuário/admin) pode então acessar uma interface separada, **autorizar** a criação das estruturas em pasta de toda essa demanda orgânica e, somente após a respectiva infraestrutura em disco estar devidamente criada, realizar através da aplicação web o **upload** da legenda em si, que já cairá no local autorizado e organizado previamente. 

**Target Users:**
Usuários avançados e administradores de repositório que desejam captar automaticamente a demanda sobre quais mídias estão sendo consumidas no Stremio e precisam de legendas.

**Value Proposition:**
* Acervo gerado sob demanda: O próprio Stremio alimenta organicamente a fila de *staging* apenas através de consumidores da casa buscando assistir filmes no sofá.
* Controle rigoroso: zero pastas criadas ou arquivos salvos até o administrador intervir no Web UI validando o que realmente deverá ser aceito.
* Desacoplamento estrutural temporal (Stremio busca -> Admin descobre que alguém quer tal filme e Autoriza os diretórios base -> Admin Upa a legenda).

## 2. Escopo
### In Scope:
* Add-on Stremio integrado diretamente pelas rotas de recursos (`GET /subtitles/...`) como provedor.
* Geração do registro em  **staging automático** em memória contendo metadados base (tipo, imdb_id, temporada/episódio, linguagem requerida) **e parâmetros estendidos da media** injetados nativamente pelo player no parâmetro `extra` (como `filename`, `videoSize`, `videoHash`) que identificam a *Release* exata tentada na televisão.
* Endpoint para listar todas as requisições de estrutura recém mapeadas como pendentes/não respondidas (`/staged`).
* Endpoint administrativo para autorizar a concepção estrita da **árvore de diretórios** daquela mídia solicitada (`/authorize`).
* Endpoint e Formulário HTML para **upload prático com checagem de viabilidade**, que somente aceitará arquivos de fato se as pastas referentes a ele já estiverem sido montadas na fase de aprovação.
* Endpoint para cancelar uma requisição recém capturada individualmente no *staging* (`/staged/<id>`).

### Out of Scope:
* Staging e trânsito massivo de pedaços de binários em memória RAM, já que o staging passa a ser estritamente descritivo (requisição da estrutura da mídia e não da transferência da legenda).
* Autenticação via senhas robustas no endpoint de gerenciamento já que se supõe operação caseira segura (LAN controlada).
* Persistência dessa fila de staging do usuário, a RAM é recomeçada em shutdowns.

## 3. User Stories

| ID | As a … | I want to … | So that … |
|---|---|---|---|
| US‑01 | Stremio App | Pesquisar na chamada inicial do vídeo no Addon se existe legenda para essa mídia | O cliente em casa saiba imediatamente se deve baixá-la para exibir ou se indiretamente engilhou o processo de captura para o Admin intervir. |
| US‑02 | Usuário/Administrador | Visualizar uma lista consolidada das chamadas não atendidas que ficaram presas na Área de Staging | Descobrir de relance e revisar quais filmes/séries demandam legendas pela galera e cujos diretórios precisam nascer. |
| US‑03 | Usuário/Administrador | Autorizar a criação massiva de pastas pendentes em base aos itens mapeados | O sistema físico de arquivos seja devidamente estruturado dentro do padrão (`/movies/{ID}`) suportando depósitos posteriores. |
| US‑04 | Usuário/Administrador | Proceder voluntariamente ao Upload de arquivo(s) de legenda para uma dada mídia e especificar/identificar sua tag de linguagem na interface (Multi-Idioma) | O Stremio consiga distinguir, listar em Dropdowns paralelos e tocar diferentes traduções ou tags customizadas para o mesmo vídeo local simultaneamente. |
| US‑05 | Usuário/Administrador | Purgar e esvaziar globalmente as captações não interessantes que lotaram a RAM/fila passivamente. (Clear Queue) | As detecções acidentais orgânicas não acumulem poeira, matando o lixo numa varredura única. |
| US‑06 | Usuário/Administrador | Alternar instântaneamente o idioma do Web App (Client-side i18n). | Operar nativamente a interface administrativa (Mega Grid, painéis, alertas) globalmente em múltiplos idiomas (PT/EN), guardando a escolha em cache. |

## 4. Requisitos Funcionais

### 4.1 Configuração Base
* **FR‑01:** Ler diretiva de ambiente definindo path das mídias (ex.: `storage_path = "./subtitles_data"`).

### 4.2 Estrutura de Diretórios 
* **FR‑02:**
  * Filmes: `{storage_path}/movies/{movie_id}/`
  * Séries: `{storage_path}/series/{series_id}/season_{season:02d}/episode_{episode:02d}/`

### 4.3 Endpoints Integradores Stremio Add-on (Busca e Fila Automática)
* **FR‑03:** Servir os dados manifestos do ecossistema:
  * Emissão de `GET /manifest.json` e listagem como local add-on.
* **FR‑04:** Quando houver rotina de *Subtitle Pulling* do próprio View do Stremio:
  * A API cruza rapidamente os dados e tenta servir o `.srt` ou `.vtt`.
  * **Se Encontrado Localmente:** Devolve `HTTP 200` portando JSON legítimo contendo url da legenda para o player do Stremio ler direto.
  * **Se Falho/Indisponível:** A API engole passivamente fornecendo `200 OK` (apresentando Array Vazio `[]` visando não interromper o filme no FrontEnd). **Em seguida, assíncronamente, gera a pendência** na RAM (staging) extraindo todos os dados da rota e desmembrando obrigatoriamente a string "Extra" em um dicionário (ex: `filename=Tracker...2160p...`, `videoHash`), para que o Admin saiba exatamente a resolução e formato de *Release* exato daquele encode para atuação e garimpo infalível nos bastidores.

### 4.4 Gerenciamento de Staging (Pastas)
* **FR‑05:** `GET /staged` – retorna Array vivo das tuplas de mídias requesitantes. O Admin utiliza os metadados devolvidos para compor a interface.
* **FR‑06:** `POST /authorize` – Efetiva, materializa no disco em lote e limpa as mídias da interface do Staging.
  * O código irá apenas iterar pelos pendentes e executar `os.makedirs(target_dir, exist_ok=True)`.
  * **Zero Uploads ou Salvos de Arquivos na pasta ocorrem ao acionar este botão.**
  * Remove todas ou chaves específicas do status pending da memória.
* **FR‑07:** `DELETE /staged/all` – Rota global destrutiva que evoca a limpeza total do dicionário atual em cache RAM (`staging_list.clear()`).

### 4.5 Submissão de Upload de Legenda Post-Processo
* **FR‑08:** `POST /upload`
  * Endpoint da interface de Gerência do App providenciada ao Admin.
  * Recebe ativamente Multipart Formulário carregado com um binário `file` atrelado aos IDs da mídia em qual se destina.
  * **Gate de Verificação Rígido:** A lógica atua bloqueando inteiramente qualquer transação física de Upload caso a árvore hierárquica base de diretórios base daquela requisição já não tiver sido garantida/arquitetada no `authorize`. (Barrado e levanta trigger/retorno pedindo autorização sistêmica primeiro).

### 4.6 Web UI Administrativa e Localização (i18n)
* **FR‑09:** SPA Local ativada na root (`/`):
  * **Card Board 1 (Demandas Pendentes):** Fila robusta consumindo requisições do Stremio para autorização em massa ou exclusão global.
  * **Mega Grid Card (Repositório / File Input):** Uma tabela mapeada integrando metadados e Covers da Cinemeta API, apresentando Input Upload Inline limpo e *Badges* flag tags das legendas hospedadas. A listagem filtra eficientemente pastas raízes de Séries prestando foco às folhas de episódio.
  * **Switcher I18n Locale:** O Navbar do Header suporta toggles "PT/EN" regidos por dicionário JSON via Client-Side JS, permitindo renderização multilingue sem recarregar e que adquire persistência guardando dados do player no LocalStorage. 
  * **Fluxo de Instalação:** O botão "Instalar Add-on" abre um modal educativo com as URLs e gatilhos `stremio://` tanto para `localhost` (Desktop) quanto para o IP da Rede local (TV Boxes), facilitando a configuração em múltiplos dispositivos.

## 5. Requisitos Não Funcionais

| Categoria | Requisito |
|---|---|
| Memória | O staging contém apenas metadados curtos, anulando gargalos drásticos de armazenamento (Nenhum binário gigante subindo acidentalmente vai para memória buffer/RAM). Tolerando requisições na ordem de milhares tranquilamente. O Error 507 foi abortado nessa revisão. |
| Atomicidade | `makedirs()` do Auth atuará em bloco, protegendo em "Exception Catchs" e alertando caso permissões em máquina falhem sem estourar toda a lista dos outros que sucederam. | 
| Limpeza Expansiva (TTL) | As requisições pendentes sem ação no Staging devem ser auto-drenadas obrigatoriamente num teto de `24 horas` via Timestamp Expire na tupla da memória, limitando tráfego defasado que a família acidentalmente testou clicando em um pacote TV há dias. |


## 6. Arquitetura Técnica e Fluxo

### 6.1 Estrutura em Lógica Reativa RAM (Exemplo Realístico)
```python
staging_list = []  
{
    "id": "abc-e3b0-21a4",
    "type": "series",
    "media_id": "tt13875494",
    "season": 3,
    "episode": 11,
    "language": "por",
    "target_dir": "E://subtitles/series/tt13875494/season_03/episode_11/",
    "detected_at": 1690002131,
    "extra_info": {
        "filename": "Tracker 2024 S03E11 To the Bone 2160p AMZN WEB-DL DDP5 1 H 265-NTb.mkv",
        "videoHash": "fb86d6e64c2ccedf",
        "videoSize": "5010136924"
    }
}
```

### 6.2 O Circuito Orgânico do Stremio (Demonstrativo Passo-a-Passo)
1. Familia na Sala clica num filme no sofá (`ID: tt5500`) e o painel base do Stremio ativa as buscas pelo idioma default (PT).
2. O Add-On de vocês engatilha o sinal e o Stremio manda `GET /subtitles/movie/tt5500/por.json` ocultamente pro Servidor Local.
3. Backend checa a pasta referencial. O arquivo físico *não existe* no drive.
4. Backend espertamente finaliza pro player Stremio com sucessos de JSON e array vazios `[]`. A família na sala verá que a legenda não rolou no menu de seleção e prosseguem o filme sem usar nosso add-on ou partem pra o OpenSubtitles público.
5. Em paralelo lá dentro da placa: A thread do nosso Backend anexou no dicionário de `staging_list` esse grito do ID `tt5500` dizendo *"Preciso que façam um diretório base pra mim"*.
6. SysAdmin (o Nerd de casa) acorda, entra no browser `http://localhost:5000`.
7. O SysAdmin checa que a família tentou assistir `tt5500`. Ele clica no layout em `Authorizar`.
8. Python engole aquilo, aciona `os.makedirs(caminho)` em background gerando a pasta nula fisicamente e tira o nome `tt5500` da memória.
9. SysAdmin vai tranquilamente em um site na nuvem, encontra a legenda SRT e faz download para Downloads do Windows.
10. SysAdmin volta ao nosso Server App Web na caixa de forms manual, escolhe "Upload for Filmes -> tt5500", e arrasta o SRT.
11. A Legenda é carimbada na respectiva pasta que já estava gerada te esperando.
12. Hoje novamente à noite a família da Play e o Stremio repete o passo 2. O Add-on responde em triunfo com os JSON de link de subtitle.

## 7. Integração e Validação do Stremio
Sem estresse pro View Component do player de video. Transparência completa, transformando a navegação comum com interações ativas em requests indiretos para criar estrutura na matriz Local.

## 8. Entregáveis Finalizados
* Código fonte Python `app.py`.
* Layout Frontend `index.html` básico consumindo Boostrap e as APIS REST elaborando a ponte visual e UX para Gestão de Uploads.
* Documentação de setup e uso.

## 9. Critérios de Avaliação Sucesso Final
1. Requisições naturais sem salvamento pré-existente criam de fato enfileiramento lógico rastreável pelo Administrador.
2. A API impossibilita (com HTTP 400 Bad Request/Precondition Failed e aviso direto na interface web) que o Gerenciador Consiga upar arquivos cujas raízes de organização (Diretórios de Temporadas, episódios) NÃO ESTEJAM fisicamente dispostas e já ativas no FileSystem.
3. O administrador consegue converter essa pendência em pastas tangíveis sem bugs por meio da ação `Authorize`.
4. Uma requisição da família é sumariamente preterida por validade e descartada eternamente no ar se o administrador não mexer no console dentro de `24h completas` após a família dar play.