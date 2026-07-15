# mcp-gmail-manager

> 🌐 **[Read in English →](README.md)**

[![PyPI version](https://img.shields.io/pypi/v/mcp-gmail-manager.svg)](https://pypi.org/project/mcp-gmail-manager/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-gmail-manager.svg)](https://pypi.org/project/mcp-gmail-manager/)
[![Licença: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Compatível com MCP](https://img.shields.io/badge/MCP-compatible-blueviolet.svg)](https://modelcontextprotocol.io)

Servidor [Model Context Protocol](https://modelcontextprotocol.io) abrangente para o Gmail: **35 ferramentas** cobrindo envio/preview/confirm, resposta, encaminhamento, rascunhos, busca, leitura, anexos, lixeira, labels, filtros, assinatura e resposta automática de férias.

Cinco funcionalidades de defesa em profundidade que diferenciam este MCP de outros para Gmail:

- **Log de auditoria tamper-evident** (ligado por padrão) — toda operação de escrita/envio/modificação/download grava uma linha JSON em `audit.jsonl`, encadeada por SHA-256 para que adulteração parcial seja detectável. Apenas metadados (sem corpo). Auditoria opcional de leituras via `audit_log.include_reads`.
- **Allowlist de destinatários** (desligada por padrão) — quando habilitada, toda operação de envio (`send_email`, `create_draft`, `reply_to_message`, `forward_message`, além de `create_filter` com ação `forward`) confere os destinatários contra domínios e endereços explícitos configurados.
- **Allowlist + denylist de paths de anexo** (denylist ligada por padrão) — o MCP recusa anexar ou sobrescrever arquivos de credencial óbvios (`~/.ssh/`, `~/.aws/`, `id_rsa`, `.env`, `token.json`, etc.), fechando o ataque "LLM exfiltra chave SSH como anexo". Veja [Notas de segurança](#notas-de-segurança) para o deny set completo.
- **Marcadores de tainted-content contra prompt injection** — tools de leitura (`get_message`, `get_thread`, `search_threads`, `list_drafts`) envolvem corpos e snippets em tags `<untrusted-email-content>...</untrusted-email-content>`. Descrições de tools instruem o LLM a tratar conteúdo dentro das tags como dado, não instrução.
- **Escopos OAuth de menor privilégio** — solicita apenas `gmail.modify` + `gmail.settings.basic`. **Não** solicita `mail.google.com`, então delete permanente é intencionalmente indisponível.

Veja [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) para uma configuração em modo institucional.

## Ferramentas (33)

| Grupo | Ferramentas |
|---|---|
| Envio / resposta / encaminhamento | `send_email`, `preview_send_email`, `confirm_send_email`, `reply_to_message`, `forward_message` |
| Rascunhos | `create_draft`, `list_drafts`, `send_draft`, `update_draft`, `delete_draft` |
| Leitura / perfil | `get_profile`, `get_message`, `search_threads`, `get_thread` |
| Anexos | `get_message_attachments`, `download_attachment` |
| Lixeira | `trash_message`, `untrash_message`, `trash_thread`, `untrash_thread` |
| Labels | `list_labels`, `create_label`, `update_label`, `delete_label`, `label_message`, `unlabel_message`, `label_thread`, `unlabel_thread` |
| Filtros | `list_filters`, `create_filter`, `delete_filter` |
| Assinatura | `get_signature`, `update_signature` |
| Resposta automática | `get_vacation_responder`, `set_vacation_responder` |

Escopos OAuth solicitados: `gmail.modify` + `gmail.settings.basic`. **Não** solicita o escopo superuser `https://mail.google.com/` — delete permanente não é suportado intencionalmente.

## Requisitos

- Python ≥ 3.10
- Projeto no Google Cloud com a Gmail API habilitada e um OAuth Client 2.0 (tipo Desktop)
- Forma de fazer forward de `localhost:8765` até o host onde o auth roda (geralmente `ssh -L 8765:localhost:8765 user@host`)

## Instalação

Suportado em Linux, macOS e Windows. Caminho recomendado é [pipx](https://pipx.pypa.io/), que instala o CLI num venv isolado e expõe os entry points no `$PATH`.

### Linux (Debian / Ubuntu / Mint / Fedora / Arch)

```bash
sudo apt install pipx        # Debian / Ubuntu / Mint
sudo dnf install pipx        # Fedora
sudo pacman -S python-pipx   # Arch
pipx ensurepath              # adiciona ~/.local/bin no PATH
# reabre o terminal ou: source ~/.bashrc

pipx install mcp-gmail-manager
```

### macOS

```bash
brew install pipx            # ou: python3 -m pip install --user pipx
pipx ensurepath              # adiciona ~/.local/bin no PATH
# reabre o terminal ou: source ~/.zshrc

pipx install mcp-gmail-manager
```

### Windows (PowerShell)

```powershell
# Se não tiver Python:  winget install --id Python.Python.3.12
python -m pip install --user pipx
python -m pipx ensurepath
# fecha e reabre o PowerShell

pipx install mcp-gmail-manager
```

Caveats Windows — tudo funciona, com duas notas sobre o modelo do OS:

- **Permissões do token.** Em Linux/macOS o MCP grava `token.json` com `chmod 0o600`. Windows não tem `chmod` POSIX, então o arquivo herda a ACL do teu `%USERPROFILE%` — protegido contra outras contas de usuário, mas qualquer processo rodando como *teu* usuário consegue ler. Mesma postura efetiva da maioria dos CLI Windows que guarda token OAuth.
- **Deny list de anexos funciona.** A partir da v0.3.2 o matching de deny/allow-list normaliza paths pra forward-slash via `Path.as_posix()`, então um path Windows tipo `C:\Users\me\.ssh\id_rsa` é corretamente pego pelo pattern default `~/.ssh/`. Confirmado pelo smoke suite nos dois OSes.

### Alternativa em qualquer OS — venv manual

```bash
python3 -m venv ~/.venv-mcp-gmail
~/.venv-mcp-gmail/bin/pip install mcp-gmail-manager
# Windows: python -m venv %USERPROFILE%\.venv-mcp-gmail
# Use o caminho absoluto ao registrar no Claude Code (ver abaixo)
```

**Por que não `pip install` global?** Em distros Debian-based modernas e no Python do Homebrew falha com `error: externally-managed-environment` ([PEP 668](https://peps.python.org/pep-0668/)) — o SO protege seu Python. Os métodos pipx e venv acima são as soluções canônicas.

**Do código-fonte:**

```bash
git clone https://github.com/arthjhon/mcp-gmail-manager.git
cd mcp-gmail-manager
pipx install .
```

## Setup no Google Cloud (uma vez, ~10 minutos)

1. Vá para o [Google Cloud Console](https://console.cloud.google.com/) e crie um novo projeto (ou use um existente).
2. Habilite a **Gmail API** (não confunda com a "Gmail MCP API" — essa é o MCP gerenciado do próprio Google; não é o que queremos).
3. Configure a **OAuth consent screen**:
   - User type: **Internal** se a sua conta for parte de um Google Workspace (sem expiração de token); senão **External** em modo Testing (até 100 usuários, refresh tokens **expiram a cada 7 dias** — veja [Expiração de token](#expiração-de-token) abaixo).
   - Escopos: adicione `https://www.googleapis.com/auth/gmail.modify` e `https://www.googleapis.com/auth/gmail.settings.basic`. **Nada mais.**
   - Test users (apenas External): adicione o endereço Gmail com o qual você vai autenticar.
4. Crie um **OAuth Client ID**:
   - Application type: **Desktop app**
   - Baixe o JSON. Salve como `credentials.json`.

## Primeira autenticação

Mova as credentials para o diretório de config (padrão: `~/.config/mcp-gmail-manager/`):

```bash
mkdir -p ~/.config/mcp-gmail-manager
mv ~/Downloads/client_secret_*.json ~/.config/mcp-gmail-manager/credentials.json
chmod 600 ~/.config/mcp-gmail-manager/credentials.json
```

Rode o fluxo OAuth:

```bash
mcp-gmail-manager-auth
```

Isso abre um listener em `localhost:8765` e imprime uma URL de autorização do Google. Abra a URL num browser **em uma máquina que consiga chegar em `localhost:8765` no host de auth**:

- **Desktop local**: a URL impressa funciona direto.
- **Servidor remoto / headless**: faça forward da porta a partir do seu laptop primeiro:
  ```bash
  ssh -L 8765:localhost:8765 user@seu-servidor
  ```
  Aí roda o `mcp-gmail-manager-auth` dentro daquela sessão SSH.

Autorize com a conta Google que vai assinar os emails enviados. Em caso de sucesso, o script grava `token.json` e encerra.

## Expiração de token

A vida útil do refresh token depende de como a OAuth consent screen está configurada:

| Setup | Vida do refresh token | Precisa reautorizar? |
|---|---|---|
| **Internal** (Google Workspace) | Sem expiração | Nunca (até o usuário revogar) |
| **External + Testing** | **7 dias** (política do Google pra apps não-verificados) | **Sim — toda semana** |
| **External + Production verificado** | Sem expiração | Nunca, mas verificação requer um security assessment pago do Google |

Quando o refresh token expira em modo Testing, você vai ver erros `invalid_grant` ou `Token has been expired or revoked`. Pra recuperar:

```bash
rm ~/.config/mcp-gmail-manager/token.json
mcp-gmail-manager-auth
```

Leva ~30 segundos. Seu `credentials.json` **não é afetado** — só o token do usuário.

### Como evitar a rotação semanal

- **Usuários Workspace**: configure a consent screen como **Internal** ao invés de External. Token nunca expira.
- **Usuários Gmail pessoal**: re-auth semanal é a única opção prática hoje. Verificação de Production pra `gmail.modify` requer um security assessment do Google (pago, semanas de processo) — inviável pra projetos pessoais.
- **Configure um lembrete no calendário** ou um cron pra te avisar semanalmente. Uma release futura pode adicionar avisos proativos antes da expiração.

## Registrar no Claude Code

Se instalou via `pipx`:

```bash
claude mcp add gmail-manager -- mcp-gmail-manager
```

Se instalou num venv manual que não está no `$PATH`:

```bash
claude mcp add gmail-manager -- ~/.venv-mcp-gmail/bin/mcp-gmail-manager
```

Reinicie a sessão do Claude Code pra que as schemas das ferramentas novas sejam carregadas.

## Múltiplas contas Gmail

Cada instância do MCP gerencia **uma** conta Gmail. Pra usar várias contas na mesma sessão do Claude Code (ex.: pessoal + trabalho), registre o MCP **uma vez por conta** com um `GMAIL_MCP_CONFIG_DIR` distinto. Cada instância tem credentials, token, audit log e config próprios — totalmente isolados.

### Setup por conta

```bash
# 1. Diretório de config dedicado
mkdir -p ~/.config/mcp-gmail-<nome> && chmod 700 ~/.config/mcp-gmail-<nome>

# 2. Reusa o mesmo OAuth client (um credentials.json serve pra qualquer usuário do mesmo projeto GCP)
cp ~/.config/mcp-gmail-<outra>/credentials.json ~/.config/mcp-gmail-<nome>/
chmod 600 ~/.config/mcp-gmail-<nome>/credentials.json

# 3. Autentica com a conta Gmail alvo
GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-<nome> mcp-gmail-manager-auth

# 4. Registra com a sobrescrita de env
claude mcp add gmail-<nome> -s user \
  -e GMAIL_MCP_CONFIG_DIR=$HOME/.config/mcp-gmail-<nome> \
  -- mcp-gmail-manager
```

Reinicia o Claude Code. As ferramentas aparecem sob namespaces separados:

- `mcp__gmail-pessoal__send_email` → envia da conta pessoal
- `mcp__gmail-trabalho__send_email` → envia da conta de trabalho

Você pode pedir ao Claude "envia pelo gmail-trabalho" e ele pega o namespace certo.

### Configuração por conta

Cada `<config_dir>/config.json` é independente. Padrões úteis:

```json
// ~/.config/mcp-gmail-trabalho/config.json — allowlist estrita
{
  "allowlist": {
    "enabled": true,
    "domains": ["suaempresa.com"]
  }
}
```

```json
// ~/.config/mcp-gmail-pessoal/config.json — silencia o audit log
{
  "audit_log": { "enabled": false }
}
```

Comprometimento do token de uma conta não vaza a outra — cada uma vive em pasta separada com `chmod 600`.

## Configuração

`~/.config/mcp-gmail-manager/config.json` é opcional — se não existir, valores padrão razoáveis são aplicados (sem allowlist, audit log ligado). Dois exemplos prontos pra copiar estão incluídos:

- [`examples/config.example.json`](examples/config.example.json) — **defaults hardened** (ponto de partida recomendado). Toda guardrail ligada; allowlist habilitada mas vazia, então o warning de startup vai apontar o que configurar primeiro.
- [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) — exemplo institucional totalmente populado com domínios de exemplo.
- [`examples/config.permissive.json`](examples/config.permissive.json) — **opt-out explícito** pra quem quer sem guardrails (allowlist off, content scan off, rate limit off, sem confirmação de envio). Considere apenas se entende o blast radius.

Referência de schema:

```json
{
  "allowlist": {
    "enabled": false,
    "domains": [],
    "emails": []
  },
  "audit_log": {
    "enabled": true,
    "include_reads": false,
    "path": null
  },
  "attachments": {
    "max_total_bytes": 20971520,
    "allowed_paths": [],
    "deny_patterns": [],
    "use_default_deny_patterns": true
  }
}
```

| Campo | Padrão | Significado |
|---|---|---|
| `allowlist.enabled` | `false` | Quando `false`, qualquer destinatário é aceito. Habilite explicitamente pra uso institucional. |
| `allowlist.domains` | `[]` | Sufixos de domínio (lower-case) aceitos como destinatário. |
| `allowlist.emails` | `[]` | Endereços explícitos (lower-case) aceitos independente do domínio. |
| `audit_log.enabled` | `true` | Anexa toda escrita/envio/modificação no JSONL. |
| `audit_log.include_reads` | `false` | Também loga operações de leitura (`get_message`, `search_threads`, etc.). Útil pra detectar reconhecimento silencioso. |
| `audit_log.path` | `null` | `null` → `<config_dir>/audit.jsonl`. Sobrescreva pra centralizar logs. |
| `audit_log.max_size_bytes` | `10485760` (10 MB) | Rotaciona pra `audit.jsonl.1..N` quando o arquivo atual passa desse tamanho. A cadeia recomeça em cada rotação; verifique cada arquivo separado com o CLI. |
| `audit_log.max_backups` | `5` | Número de backups rotacionados mantidos. Os mais antigos são sobrescritos. |
| `audit_log.verify_on_startup` | `false` | Percorre a cadeia no start do servidor e emite warning em stderr se estiver quebrada. Barato pra logs de até alguns MB. |
| `attachments.max_total_bytes` | `20971520` (20 MB) | Limite combinado de tamanho por envio. Limite duro do Gmail é 25 MB raw. |
| `attachments.allowed_paths` | `[]` | Quando populado, sources de attach e destinos de download DEVEM estar sob uma dessas bases. Vazio = só deny patterns se aplicam. |
| `attachments.deny_patterns` | `[]` | Regex extras pra rejeitar (matched contra path absoluto). Somam aos defaults. |
| `attachments.use_default_deny_patterns` | `true` | Inclui o deny set built-in (`~/.ssh/`, `~/.aws/`, `id_rsa`, `.env`, `token.json`, arquivos de credencial, browser stores). |
| `rate_limit.enabled` | `false` | Quando `true`, limita envios por hora por instância rodando. Sliding window in-memory — reseta a cada restart. |
| `rate_limit.sends_per_hour` | `60` | Aplicado a `send_email`, `reply_to_message`, `forward_message` e `send_draft` combinados. |
| `content_scan.enabled` | `false` | Quando `true`, escaneia subject/body/signature/vacation outbound procurando padrões de secrets. Matches bloqueiam a operação antes de chegar no Gmail. |
| `content_scan.use_default_patterns` | `true` | Inclui os regexes built-in (chaves AWS, tokens Stripe/OpenAI/Anthropic/GitHub/GitLab/Google/Twilio, chaves PEM privadas, JWTs, credenciais embutidas em URL). |
| `content_scan.patterns` | `[]` | Padrões extras do usuário. Cada entrada: `{"name": "...", "regex": "..."}`. Nomes aparecem nas mensagens de erro pra debug. |
| `content_scan.scan_subject` / `scan_body` / `scan_signature` / `scan_vacation` | `true` | Toggles por escopo. Útil pra desligar um local mantendo outros ativos. |
| `send_confirmation.required` | `false` | Quando `true`, `send_email` direto é desabilitado — precisa passar por `preview_send_email` → `confirm_send_email(preview_id)`. |
| `send_confirmation.preview_ttl_seconds` | `300` | Quanto tempo um preview fica válido antes de precisar ser reemitido. |

### Verificando o audit log

Rode `mcp-gmail-manager-verify-log` pra percorrer a cadeia de hashes e confirmar que nenhuma entrada foi editada ou removida:

```bash
mcp-gmail-manager-verify-log                       # verifica o log ativo
mcp-gmail-manager-verify-log ~/.config/.../audit.jsonl.1   # verifica um backup rotacionado
```

Exit codes: `0` OK, `1` log não encontrado, `2` JSON malformado, `3` cadeia quebrada.

### Sobrescritas via variável de ambiente

| Variável | Padrão |
|---|---|
| `GMAIL_MCP_CONFIG_DIR` | `$XDG_CONFIG_HOME/mcp-gmail-manager` ou `~/.config/mcp-gmail-manager` |
| `GMAIL_MCP_CREDENTIALS` | `<config_dir>/credentials.json` |
| `GMAIL_MCP_TOKEN` | `<config_dir>/token.json` |

## Notas de segurança

- **Modelo de ameaça**: este MCP é primariamente endurecido contra um **LLM se comportando mal** — prompt injection, destinatários alucinados, cenários de "convencer a ferramenta a exfiltrar". **Não** substitui segurança do host; um atacante com acesso local pode ler `token.json` e chamar a Gmail direto, contornando toda guardrail aqui.
- **Armazenamento do token**: `token.json` é gravado com `chmod 600`. Trate como senha.
- **Sem telemetria remota**: o servidor roda inteiramente na sua máquina. Sem telemetria, sem chamadas a terceiros além de `googleapis.com`.
- **Escopo OAuth é deliberadamente estreito-ish**: `gmail.modify` cobre send/read/label/trash/drafts. **Não** solicita `mail.google.com`, então delete permanente é indisponível — deletes vão pra Lixeira e podem ser desfeitos com `untrash_*`. Se você só precisa enviar, faça fork e troque por `gmail.send`.
- **Guardrails de destinatário cobrem forward-em-filtros**: `create_filter` com `action.forward` apontando pra endereço fora da allowlist é rejeitado. Filtros eram bypass comum de allowlists só-de-envio.
- **Tools de leitura marcam conteúdo como untrusted**: corpos e snippets são envolvidos em `<untrusted-email-content>...</untrusted-email-content>`. Descrições de tools instruem LLMs downstream a tratar conteúdo envolvido como dado. Qualquer ocorrência da tag de fechamento dentro do body é escapada pra prevenir break-out.
- **Deny set padrão de anexos** (source e destino) cobre paths comuns de credencial/segredo:
  `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, `~/.docker/config.json`, `~/.kube/`, `.env`, `.env.*`, `credentials.json`, `token.json`, `id_rsa`/`id_ed25519`/`id_ecdsa`/`id_dsa`, `.git-credentials`, `.netrc`, `wallet.dat`, `.bash_history`, `.zsh_history`, `~/.mozilla/*/logins.json`, `authorized_keys`, `known_hosts`. Estenda via `attachments.deny_patterns` ou restrinja mais via `attachments.allowed_paths`.
- **Audit log é tamper-evident, não tamper-proof**: cada entrada inclui `prev_hash = sha256(linha anterior)`. Modificação parcial quebra a cadeia e é detectável. Uma reescrita completa do log por atacante com file-write **não** é prevenida — combine com log shipping off-host (roadmap) pra garantias mais fortes.
- **O que NÃO é mitigado**: rate limiting (agente comprometido pode queimar quota do Gmail rápido), scan de padrões no body outbound (sem regex de secrets), phishing via signature/vacation (allowlist não cobre conteúdo delas), rewrite total de log por atacante local. Veja [SECURITY.md](SECURITY.md) para o threat model atual e roadmap.

## Limitações

- A verificação "Production" do OAuth pra `gmail.modify` requer um security assessment pago do Google. Fique em "Internal" (Workspace, sem expiração) ou "Testing" (≤ 100 usuários, **rotação de refresh token a cada 7 dias** — veja [Expiração de token](#expiração-de-token)) pra evitar isso.
- Composição de email com corpo HTML não está exposta como campo de primeira classe. Use `create_draft` + edição manual de HTML no UI do Gmail, ou estenda `_build_mime` num fork.
- Notificações push (Pub/Sub `watch`/`stop`) não foram implementadas — fora do escopo.

## Contribuindo

Issues e PRs bem-vindos. Mantenha mudanças escopadas, documente qualquer ferramenta nova com exemplo de schema, e adicione uma entrada no audit log pra qualquer coisa que altere estado.

## Licença

MIT — veja [LICENSE](LICENSE).
