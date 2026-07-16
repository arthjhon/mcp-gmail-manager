# Guia de instalação

> 🌐 **[Read in English →](INSTALLATION.md)**

Tutorial passo a passo pra instalar e configurar o **mcp-gmail-manager** — do setup OAuth no Google Cloud até uma integração MCP funcionando no Claude Code.

---

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Escolha seu caminho de instalação](#escolha-seu-caminho-de-instalação)
3. [Passo 1 — Instalar o pacote](#passo-1--instalar-o-pacote)
4. [Passo 2 — Configurar o Google Cloud (uma vez só)](#passo-2--configurar-o-google-cloud-uma-vez-só)
5. [Passo 3 — Colocar o credentials.json no lugar](#passo-3--colocar-o-credentialsjson-no-lugar)
6. [Passo 4 — Rodar o fluxo OAuth](#passo-4--rodar-o-fluxo-oauth)
7. [Passo 5 — Registrar no Claude Code](#passo-5--registrar-no-claude-code)
8. [Passo 6 — Verificar que funcionou](#passo-6--verificar-que-funcionou)
9. [Opcional — Hardening](#opcional--hardening)
10. [Múltiplas contas e múltiplas VMs](#múltiplas-contas-e-múltiplas-vms)
11. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

- Python 3.10 ou mais novo
- Uma conta Gmail (pessoal `@gmail.com` ou Google Workspace)
- Claude Code instalado e funcionando (`claude --version`)
- **Pra instalação em desktop**: browser na mesma máquina
- **Pra instalação em VM headless** (Contabo, DigitalOcean, Hetzner, EC2, etc.): acesso SSH e forma de fazer port forward

---

## Escolha seu caminho de instalação

| Cenário | Complexidade do auth | Vida do token |
|---|---|---|
| **Desktop (macOS / Linux com browser / Windows)** | Simples — browser e auth server na mesma máquina | Depende do modo OAuth abaixo |
| **VM headless** | Média — precisa SSH port forwarding | Idem |
| **Conta `@gmail.com` pessoal** | Mesmos passos de instalação | **Rotação a cada 7 dias** (modo Testing do Google) |
| **Conta Google Workspace (Internal)** | Mesmos passos de instalação | **Sem expiração** |

Pega a combinação que se aplica a ti e segue as seções abaixo.

---

## Passo 1 — Instalar o pacote

### macOS

```bash
brew install pipx           # pula se já tiver
pipx ensurepath             # adiciona ~/.local/bin no PATH
# fecha e reabre o terminal, ou: source ~/.zshrc

pipx install mcp-gmail-manager
```

### Linux (Debian / Ubuntu / Mint / Fedora / Arch)

```bash
sudo apt install pipx        # Debian / Ubuntu / Mint
sudo dnf install pipx        # Fedora / Rocky / Alma
sudo pacman -S python-pipx   # Arch
pipx ensurepath              # adiciona ~/.local/bin no PATH
# reabre a shell, ou: source ~/.bashrc

pipx install mcp-gmail-manager
```

### Windows (PowerShell)

```powershell
# Se não tiver Python:
winget install --id Python.Python.3.12

python -m pip install --user pipx
python -m pipx ensurepath
# fecha e reabre o PowerShell

pipx install mcp-gmail-manager
```

### Confere

```bash
python3 -c "import mcp_gmail_manager; print(mcp_gmail_manager.__version__)"
# Esperado: 0.3.3 (ou mais novo)
```

---

## Passo 2 — Configurar o Google Cloud (uma vez só)

É aqui que a maioria dos usuários trava. As screenshots deixam o processo trivial — usa como referência visual junto com o texto.

### 2.1 Cria (ou seleciona) um projeto no Google Cloud

Abre o [Google Cloud Console](https://console.cloud.google.com/).

![Console GCP na home — clica no dropdown de projeto no topo](images/01-gcp-select-project.png)

Clica em **New Project**, dá um nome (ex.: `mcp-gmail-manager`), deixa a Organization em "No organization" se estiver usando Gmail pessoal, e **Create**.

![Formulário de novo projeto com campo de nome](images/02-gcp-new-project-form.png)

### 2.2 Habilita a Gmail API

Vai em **APIs & Services → Library** e busca por `Gmail API`.

![APIs & Services Library — barra de busca com "Gmail API"](images/03-gcp-api-library.png)

Clica no resultado "Gmail API" e aperta **Enable**.

![Página da Gmail API com o botão Enable em destaque](images/04-gcp-gmail-api-enable.png)

> ⚠ **Importante**: habilita a **Gmail API**, não a "Gmail MCP API" — a última é o MCP remoto gerenciado do próprio Google e **não** é o que este projeto usa.

### 2.3 Configura a OAuth consent screen

Vai em **APIs & Services → OAuth consent screen** (na interface nova pode estar em "Google Auth Platform → Branding / Audience / Data access").

Escolhe o user type:

- **Internal** — disponível só se tu tem Google Workspace. Qualquer usuário da tua org Workspace pode autenticar; refresh tokens **não** expiram.
- **External** — necessário pra contas `@gmail.com` pessoais. Refresh tokens rotacionam a cada **7 dias** enquanto o app estiver em modo "Testing".

![Seleção do user type — Internal vs External](images/05-gcp-oauth-consent-user-type.png)

Preenche as info do app:

- **App name**: `mcp-gmail-manager` (ou o que quiser)
- **User support email**: teu email
- **Developer contact email**: teu email

![Formulário de informações do app](images/06-gcp-oauth-consent-app-info.png)

Adiciona os scopes — **só esses dois**, nada mais:

- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/gmail.settings.basic`

![Seleção de scopes na consent screen com os dois scopes obrigatórios](images/07-gcp-oauth-consent-scopes.png)

**Só External + Testing users**: adiciona os endereços Gmail que vão autenticar como test users (até 100). Pula essa etapa se escolheu Internal.

![Lista de test users com endereço Gmail adicionado](images/08-gcp-oauth-consent-test-users.png)

Salva a consent screen.

### 2.4 Cria o OAuth Client ID

Vai em **APIs & Services → Credentials → Create Credentials → OAuth Client ID**.

![Página de credenciais com botão Create Credentials](images/09-gcp-credentials-create.png)

Escolhe **Application type: Desktop app** e dá um nome (`mcp-gmail-manager-desktop` funciona).

![Seleção de application type — opção Desktop app](images/10-gcp-credentials-desktop-app.png)

Clica **Create** e depois **Download JSON** no dialog de confirmação. Salva o arquivo como `credentials.json`.

![Dialog de confirmação com botão Download JSON](images/11-gcp-credentials-download.png)

---

## Passo 3 — Colocar o credentials.json no lugar

### macOS / Linux (desktop ou VM)

```bash
mkdir -p ~/.config/mcp-gmail-manager
mv ~/Downloads/credentials.json ~/.config/mcp-gmail-manager/credentials.json
chmod 600 ~/.config/mcp-gmail-manager/credentials.json
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.config\mcp-gmail-manager" | Out-Null
Move-Item "$HOME\Downloads\credentials.json" "$HOME\.config\mcp-gmail-manager\credentials.json"
```

### Deploy em VM headless

Se o Google Cloud tá no teu desktop mas o MCP roda numa VM, transfere via `scp`:

```bash
scp ~/Downloads/credentials.json user@ip-da-vm:~/credentials.json
```

Aí na VM:

```bash
mkdir -p ~/.config/mcp-gmail-manager
mv ~/credentials.json ~/.config/mcp-gmail-manager/credentials.json
chmod 600 ~/.config/mcp-gmail-manager/credentials.json
```

---

## Passo 4 — Rodar o fluxo OAuth

### 4a — Desktop / local (browser na mesma máquina)

```bash
mcp-gmail-manager-auth
```

Cola a URL impressa no browser, loga com a conta Google que tu adicionou, e clica **Allow / Permitir**.

![Terminal exibindo a URL OAuth impressa](images/12-auth-cli-output.png)

![Dialog de consentimento do Google pedindo autorização do app](images/13-google-consent-dialog.png)

Vai aparecer a confirmação:

```
Token salvo em /Users/voce/.config/mcp-gmail-manager/token.json
```

![Terminal mostrando "Token salvo em ..." de sucesso](images/14-auth-success.png)

### 4b — VM headless (browser em máquina diferente)

O listener do auth binda em `localhost:8765` **na VM**. O Google vai redirecionar **teu browser** (no teu laptop) pra `http://localhost:8765/`. Precisa de um túnel SSH entre os dois.

**Da tua máquina local, num terminal NOVO:**

```bash
ssh -L 8765:localhost:8765 user@ip-da-vm
```

Deixa essa sessão aberta — ela mantém o túnel ativo.

**Dentro dessa mesma sessão SSH, na VM:**

```bash
mcp-gmail-manager-auth
```

Cola a URL no browser local, loga, clica **Permitir**. O callback viaja pelo túnel SSH e é capturado na VM.

#### Se a porta 8765 estiver em uso na VM

Verifica com `ss -tlnp | grep 8765`. Se tiver algo, escolhe uma porta livre (ex.: `18765`) e usa a env var `GMAIL_MCP_AUTH_PORT` (v0.3.3+):

```bash
# Na VM
export GMAIL_MCP_AUTH_PORT=18765
mcp-gmail-manager-auth
```

```bash
# Na máquina local — casa a porta
ssh -L 18765:localhost:18765 user@ip-da-vm
```

#### Nota específica pra Windows

Alguns Windows bloqueiam o `ssh -L` de bindar portas loopback locais com `bind [127.0.0.1]:8765: Permission denied` — geralmente Windows Defender ou algum agente EDR. Workarounds:

- Tenta `ssh -4 -L 18765:localhost:18765 user@ip-da-vm` (força IPv4)
- Roda PowerShell como Administrador
- Usa `GMAIL_MCP_AUTH_PORT=45123` (qualquer porta alta fora de `netsh interface ipv4 show excludedportrange protocol=tcp`)

Se nada resolver, roda o auth numa máquina Linux/macOS e faz `scp` do `token.json` resultante pra VM.

---

## Passo 5 — Registrar no Claude Code

```bash
claude mcp add gmail-manager -s user -- mcp-gmail-manager
```

A flag `-s user` faz o MCP ficar disponível em **todos os projetos** que tu abrir no Claude Code, não só no diretório atual.

![Terminal mostrando claude mcp add com sucesso e claude mcp list](images/15-claude-mcp-list.png)

Agora **reinicia a sessão do Claude Code** (fecha e reabre o chat, ou roda `/exit` e `claude`) pra carregar as schemas dos tools novos.

---

## Passo 6 — Verificar que funcionou

Numa sessão nova do Claude Code, pede:

> "Chama `get_profile` no gmail-manager."

O MCP deve retornar teu endereço Gmail e a contagem de mensagens/threads.

![Chat do Claude Code mostrando get_profile sendo chamado e o retorno](images/16-claude-tool-in-use.png)

Se tu vê teu email e stats, tá tudo pronto. Se der erro tipo `Token nao encontrado`, revisita o **Passo 4**.

---

## Opcional — Hardening

A configuração default é permissiva — sem allowlist, sem scan de secrets, sem rate limit. Ótima pra testar, não ideal pra produção. Pra ativar defaults security-first:

```bash
curl -o ~/.config/mcp-gmail-manager/config.json \
  https://raw.githubusercontent.com/arthjhon/mcp-gmail-manager/main/examples/config.example.json
```

Depois edita `~/.config/mcp-gmail-manager/config.json` e define `allowlist.domains` com os domínios que tu autoriza enviar. O warning de startup te lembra se deixar vazio.

Pra explicação completa de cada campo, veja a [seção Configuration do README](../README.pt-BR.md#configuração).

---

## Múltiplas contas e múltiplas VMs

Dá pra rodar várias instâncias do `mcp-gmail-manager` em paralelo — uma por conta Gmail, cada uma com seu diretório de config:

```bash
# 1. Cria diretório de config dedicado
mkdir -p ~/.config/mcp-gmail-trabalho && chmod 700 ~/.config/mcp-gmail-trabalho

# 2. Reutiliza o mesmo credentials.json (mesmo OAuth Client serve pra qualquer user autorizado)
cp ~/.config/mcp-gmail-manager/credentials.json ~/.config/mcp-gmail-trabalho/
chmod 600 ~/.config/mcp-gmail-trabalho/credentials.json

# 3. Autentica com a segunda conta
GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-trabalho mcp-gmail-manager-auth

# 4. Registra um segundo MCP com o env override
claude mcp add gmail-trabalho -s user \
  -e GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-trabalho \
  -- mcp-gmail-manager
```

As tools aparecem em namespaces separados: `mcp__gmail-manager__send_email`, `mcp__gmail-trabalho__send_email`, etc.

---

## Troubleshooting

### `credentials.json nao encontrado`

Tu pulou ou salvou errado o Passo 3. Verifica:

```bash
ls -la ~/.config/mcp-gmail-manager/credentials.json
# Esperado: -rw------- (chmod 600) e tamanho não-zero
```

### `Token nao encontrado. Rode mcp-gmail-manager-auth primeiro.`

Tu não completou o Passo 4 pra esse config dir, ou o token expirou (rotação de 7 dias em modo Testing). Roda o auth flow de novo.

### `Address already in use` na porta do auth

Outro processo tá segurando a porta na VM. Diagnostica com `ss -tlnp | grep <porta>` e mata ou usa `GMAIL_MCP_AUTH_PORT` pra pegar outra.

### `bind [127.0.0.1]:8765: Permission denied` (SSH client no Windows)

Veja a nota específica de Windows no [Passo 4b](#4b--vm-headless-browser-em-máquina-diferente).

### A tela de consent do Google diz "This app is restricted to a specific organization"

Tua consent screen está em **Internal** mas tu está tentando autenticar com uma conta Gmail fora daquela org Workspace. Ou:

- Muda a consent screen pra **External + Testing** e adiciona o endereço Gmail como test user, ou
- Autentica com uma conta Google dentro da mesma org Workspace

### Claude Code diz que a tool não existe

Tu esqueceu de reiniciar o Claude Code depois do `claude mcp add`. Roda `/exit` e `claude`, ou dá reload na janela do VSCode (`Developer: Reload Window` na command palette).

### Não achei minha situação nessa lista

Abre uma issue em https://github.com/arthjhon/mcp-gmail-manager/issues com:

- O comando que rodou
- Output completo do erro
- Teu OS, versão do Python (`python3 --version`) e versão do mcp-gmail-manager (`python3 -c "import mcp_gmail_manager; print(mcp_gmail_manager.__version__)"`)

---

## Próximos passos

- **[README](../README.pt-BR.md)** — visão geral, referência de tools, notas de segurança
- **[SECURITY.md](../SECURITY.md)** — threat model e limitações conhecidas
- **[examples/](../examples/)** — três presets de configuração prontos pra copiar
- **[audits/](../audits/)** — relatórios de audit externa de segurança
