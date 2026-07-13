# Execute Next (optional)

**When:** you want cloud agents to run tasks automatically — one task per fresh chat, squash-merge to `main` between runs.

**Default workflow** is manual: `/execute` in a new chat per task. You only need this doc if you set up [Cursor Automations](https://cursor.com/automations).

## Setup (once)

1. [cursor.com/automations](https://cursor.com/automations) → **New automation** → trigger **Webhook**
2. Repository: your repo, branch `main`
3. Prompt: copy from `.cursor/automations/execute-next-prompt.txt`
4. **Save** → copy webhook URL to `.cursor/automations/config.json` → `webhookUrl`
5. **Generate auth header** → add to `.env`:
   ```bash
   CURSOR_AUTOMATION_TOKEN=crsr_...
   ```
6. Push planning state so cloud agents see your active change:
   ```bash
   ./scripts/sync-execute-next.sh --commit --push
   ```

For cloud auto-chain, also add `CURSOR_AUTOMATION_TOKEN` to [Cloud Agent Environment](https://cursor.com/dashboard/cloud-agents) → your repo → Runtime secrets.

## Daily use

```bash
./scripts/trigger-execute-next.sh    # start or resume chain (after previous task is on main)
```

Each run: agent picks next task via `./scripts/next-task.sh` → implements → `./scripts/finish-execute-task.sh` (squash-merge PR → triggers next).

**Human only** does the final stage merge/archive. Mid-stage gates (G*) are auto-acked.

## If chain breaks

```bash
gh pr merge <n> --squash
./scripts/trigger-execute-next.sh
```
