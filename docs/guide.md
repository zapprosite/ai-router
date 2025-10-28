# Guide — Painel /guide (Local‑first + Tier‑2)

Este guia explica como usar o painel em `/guide` e como sincronizar os comandos exibidos com o Makefile.

## 1) Como usar o painel

- Abra `http://localhost:8082/guide`.
 - Atalho: `make guide-open` (se disponível no ambiente gráfico). Caso contrário, abra manualmente `http://localhost:8082/guide`.
- A área superior possui atalhos para `/debug/where`, `/v1/models` e smokes.
- O Terminal (rodapé) mostra uma gaveta com comandos numerados.
  - Cada botão numérico copia SOMENTE o comando (atributo `data-cmd`).
  - Um toast confirma: “Comando copiado ✓”. Cole no seu terminal.

## 2) Sessão rápida (terminal)

```bash
# entrar no projeto
cd /srv/projects/ai-router

# ativar venv + carregar variáveis locais
. .venv/bin/activate && set -a; . config/.env.local; set +a
```

## 3) Cloud ON/OFF sem redigitar segredos

A chave já está em `config/.env.local`. Os alvos abaixo só alternam `ENABLE_OPENAI_FALLBACK` e reiniciam o serviço.

```bash
make cloud-status
make cloud-off
make cloud-on
```

## 4) Operação do serviço (systemd)

```bash
make status
make restart   && curl -fsS http://localhost:8082/healthz
make logs
make warm
```

## 5) Smokes e testes de modelos

```bash
make smoke
make local-llama
make local-deepseek
make test-nano
make test-mini
make test-codex
make test-high
```

## 6) Recuperação e stress (opcional)

```bash
scripts/RECOVER_SAFE.sh
scripts/STRESS_SAFE_ENV.sh
scripts/STRESS_LOCAL.sh
scripts/STRESS_MATRIX.sh
```

## 7) Backup

```bash
make backup-all
scripts/BACKUP_DESKTOP.sh
```

## 8) Sincronizar comandos do painel

O painel lê `/public/guide_cmds.json` e também injeta comandos padrão. Para refletir mudanças no Makefile:

```bash
make panel-json    # gera public/guide_cmds.json a partir do help do Makefile
make panel-refresh # força o painel a recarregar o JSON
```
