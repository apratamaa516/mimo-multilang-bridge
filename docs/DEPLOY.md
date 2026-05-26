# MiMo Multilang Bridge — Production Deploy

## Quick deploy (Docker)

```bash
docker build -t mimo-multilang-bridge .
docker run -d --name mimo-bridge \
  --restart unless-stopped \
  -p 8000:8000 \
  -e MIMO_API_KEY="$MIMO_API_KEY" \
  -e MIMO_BASE_URL="https://token-plan-sgp.xiaomimimo.com/v1" \
  mimo-multilang-bridge
```

Health check:

```bash
curl -s http://localhost:8000/api/health | jq
# {"status":"ok","version":"0.1.0","tracker_active":true}
```

OpenAPI docs:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## systemd unit (Linux VPS)

`/etc/systemd/system/mimo-bridge.service`:

```ini
[Unit]
Description=MiMo Multilang Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=mimo
Group=mimo
WorkingDirectory=/opt/mimo-bridge
EnvironmentFile=/opt/mimo-bridge/.env
ExecStart=/opt/mimo-bridge/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mimo-bridge
journalctl -u mimo-bridge -f
```

## Reverse proxy (Caddy)

```caddy
mimo.example.com {
    reverse_proxy localhost:8000
    encode gzip
    log {
        output file /var/log/caddy/mimo.log
    }
}
```

## Token budget guardrails

The tracker exposes per-agent breakdown at `/api/stats`:

```bash
curl -s http://localhost:8000/api/stats | jq '.agents'
# {
#   "translator":  {"calls": 412, "total_tokens": 412000},
#   "summarizer":  {"calls": 187, "total_tokens": 561000},
#   "extractor":   {"calls": 95,  "total_tokens": 142000},
#   "synthesizer": {"calls": 73,  "total_tokens": 109000}
# }
```

Set a daily cap via cron + the tracker output:

```bash
*/15 * * * * /opt/mimo-bridge/scripts/check_budget.sh 5000000
```

## Backup the tracker SQLite

The token tracker persists to `data/tracker.db`. Daily backup:

```bash
0 4 * * * sqlite3 /opt/mimo-bridge/data/tracker.db ".backup /backup/tracker-$(date +%F).db"
```
