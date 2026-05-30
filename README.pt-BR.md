# mcp-gmail-manager

> 🌐 **[Read in English →](README.md)**

Servidor [Model Context Protocol](https://modelcontextprotocol.io) abrangente para o Gmail: **33 ferramentas** cobrindo envio, resposta, encaminhamento, rascunhos, busca, leitura, anexos, lixeira, labels, filtros, assinatura e resposta automática de férias.

Duas funcionalidades opcionais que diferenciam este MCP de outros para Gmail:

- **Log de auditoria local** (ligado por padrão) — toda operação de escrita/envio/modificação/download grava uma linha JSON em `audit.jsonl`. Apenas metadados (sem conteúdo do corpo). Trilha de compliance sem dependência de terceiros.
- **Allowlist de destinatários** (desligada por padrão) — quando habilitada, toda operação de envio (`send_email`, `create_draft`, `reply_to_message`, `forward_message`) confere os destinatários contra domínios e endereços explícitos configurados. Útil em contextos institucionais ou de compliance. Veja [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) para habilitar.

## Ferramentas (33)

| Grupo | Ferramentas |
|---|---|
| Envio / resposta / encaminhamento | `send_email`, `reply_to_message`, `forward_message` |
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

```bash
pip install mcp-gmail-manager
```

Ou direto do código-fonte:

```bash
git clone https://github.com/arthjhon/mcp-gmail-manager.git
cd mcp-gmail-manager
pip install .
```

## Setup no Google Cloud (uma vez, ~10 minutos)

1. Vá para o [Google Cloud Console](https://console.cloud.google.com/) e crie um novo projeto (ou use um existente).
2. Habilite a **Gmail API** (não confunda com a "Gmail MCP API" — essa é o MCP gerenciado do próprio Google; não é o que queremos).
3. Configure a **OAuth consent screen**:
   - User type: **Internal** se a sua conta for parte de um Google Workspace; senão **External** em modo Testing (limite de 100 usuários, tokens expiram a cada 7 dias — funciona pra uso individual).
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

## Registrar no Claude Code

```bash
claude mcp add gmail-manager -- mcp-gmail-manager
```

Ou, se você instalou num virtualenv que não está no `$PATH`:

```bash
claude mcp add gmail-manager -- /caminho/para/venv/bin/mcp-gmail-manager
```

Reinicie a sessão do Claude Code pra que as schemas das ferramentas novas sejam carregadas.

## Configuração

`~/.config/mcp-gmail-manager/config.json` é opcional — se não existir, valores padrão razoáveis são aplicados (sem allowlist, audit log ligado). Dois exemplos prontos pra copiar estão incluídos:

- [`examples/config.example.json`](examples/config.example.json) — mínimo, sem allowlist (comportamento padrão). Use este se quer que o MCP envie pra qualquer endereço.
- [`examples/config.with-allowlist.json`](examples/config.with-allowlist.json) — setup institucional com allowlist ativa.

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
    "path": null
  },
  "attachments": {
    "max_total_bytes": 20971520
  }
}
```

| Campo | Padrão | Significado |
|---|---|---|
| `allowlist.enabled` | `false` | Quando `false`, qualquer destinatário é aceito. Habilite explicitamente pra uso institucional. |
| `allowlist.domains` | `[]` | Sufixos de domínio (lower-case) aceitos como destinatário. |
| `allowlist.emails` | `[]` | Endereços explícitos (lower-case) aceitos independente do domínio. |
| `audit_log.enabled` | `true` | Anexa toda escrita/modificação/envio no JSONL. |
| `audit_log.path` | `null` | `null` → `<config_dir>/audit.jsonl`. Sobrescreva pra centralizar logs. |
| `attachments.max_total_bytes` | `20971520` (20 MB) | Limite combinado de tamanho por envio. Limite duro do Gmail é 25 MB raw. |

### Sobrescritas via variável de ambiente

| Variável | Padrão |
|---|---|
| `GMAIL_MCP_CONFIG_DIR` | `$XDG_CONFIG_HOME/mcp-gmail-manager` ou `~/.config/mcp-gmail-manager` |
| `GMAIL_MCP_CREDENTIALS` | `<config_dir>/credentials.json` |
| `GMAIL_MCP_TOKEN` | `<config_dir>/token.json` |

## Notas de segurança

- **Armazenamento do token**: `token.json` é gravado com `chmod 600`. Trate como senha — qualquer um com permissão de leitura consegue agir como sua conta Gmail.
- **Sem telemetria remota**: o servidor roda inteiramente na sua máquina. Sem telemetria, sem chamadas a terceiros além de `googleapis.com`.
- **Allowlist é defesa em profundidade, não perímetro de segurança**: um atacante que comprometa sua máquina pode ler `token.json` e chamar a Gmail API direto, contornando o MCP. A allowlist defende contra o LLM ser enganado ou alucinar destinatários maliciosos, não contra comprometimento do host.
- **Escopo OAuth é amplo**: `gmail.modify` cobre tudo exceto delete permanente. Se você só precisa enviar, faça um fork e troque o escopo por `gmail.send`.
- **Delete permanente é intencionalmente não suportado**: não solicitamos `https://mail.google.com/`. Deletes vão pra Lixeira e podem ser desfeitos com `untrash_*`.

## Limitações

- A verificação "Production" do OAuth pra `gmail.modify` requer um security assessment do Google (pago, semanas de processo). Fique em "Internal" (Workspace) ou "Testing" (≤ 100 usuários, refresh de 7 dias) pra evitar isso.
- Composição de email com corpo HTML não está exposta como campo de primeira classe. Use `create_draft` + edição manual de HTML no UI do Gmail, ou estenda `_build_mime` num fork.
- Notificações push (Pub/Sub `watch`/`stop`) não foram implementadas — fora do escopo.

## Contribuindo

Issues e PRs bem-vindos. Mantenha mudanças escopadas, documente qualquer ferramenta nova com exemplo de schema, e adicione uma entrada no audit log pra qualquer coisa que altere estado.

## Licença

MIT — veja [LICENSE](LICENSE).
