# Example Run — Real Pipeline Output

> Run against a Chinese vendor SDK README (Alibaba Cloud OSS docs) translated to Indonesian + summarized + extracted.
> Date: 2026-05-26 · Model: mimo-v2.5-pro / mimo-v2.5

## Input (Chinese, 1,247 characters)

```
阿里云对象存储 OSS 是一种海量、安全、低成本、高可靠的云存储服务...
[full source omitted for brevity, see examples/oss-cn.txt]
```

## Translation pipeline (3 passes, ZH → ID)

| Pass | Model | Tokens | Latency |
|---|---|---:|---:|
| Literal | mimo-v2.5 | 1,121 | 2.1s |
| Idiomatic | mimo-v2.5 | 1,184 | 2.4s |
| Review | mimo-v2.5 | 1,098 | 1.9s |
| **Subtotal** | | **3,403** | **6.4s** |

Output (Indonesian):
```
Alibaba Cloud Object Storage Service (OSS) adalah layanan penyimpanan cloud
yang masif, aman, hemat biaya, dan sangat andal. Kapasitas: tak terbatas...
[full ID translation omitted, see examples/oss-id.txt]
```

## Summarize (chunked, target=ID)

| Stage | Model | Tokens |
|---|---|---:|
| Chunk 1 (4K window) | mimo-v2.5 | 1,840 |
| Chunk 2 | mimo-v2.5 | 1,612 |
| Merge + dedupe | mimo-v2.5-pro | 1,401 |
| **Subtotal** | | **4,853** |

Output bullets:
- OSS adalah layanan penyimpanan objek skalabel dengan SLA 99.9% durabilitas
- Kompatibel dengan S3 API standar untuk migrasi mudah
- Mendukung enkripsi server-side dan client-side
- Pricing tiered: Standard, Infrequent Access, Archive (mulai dari ¥0.12/GB/bulan)
- SDK tersedia untuk Java, Python, Go, Node.js, PHP, .NET, C++, Android, iOS

## Extract

```json
{
  "entities": [
    {"name": "Alibaba Cloud OSS", "type": "service"},
    {"name": "S3 API", "type": "standard"}
  ],
  "dates": [],
  "amounts": [
    {"value": 0.12, "currency": "CNY", "context": "per GB per month, Standard tier"}
  ],
  "action_items": [
    "Pilih tier penyimpanan sesuai pola akses data",
    "Konfigurasi enkripsi server-side untuk data sensitif"
  ]
}
```

## Synthesize (full pipeline)

| Agent | Tokens |
|---|---:|
| Translator | 3,403 |
| Summarizer | 4,853 |
| Extractor | 2,891 |
| Synthesizer | 1,124 |
| **Total** | **12,271** |

Output brief:
```
Alibaba Cloud OSS adalah layanan penyimpanan objek cloud yang skalabel
dengan SLA durabilitas 99.9%, kompatibel S3 API, dan mendukung enkripsi
dual-side. Tersedia 3 tier harga (Standard ¥0.12/GB/bulan, IA, Archive)
dengan SDK lengkap untuk 9 bahasa. Action items: pilih tier sesuai pola
akses, aktifkan enkripsi untuk data sensitif.
```

reasoning_content snippet (synthesizer):
```
The chunked summary surfaces 5 key bullets but the brief should foreground
the SLA + S3 compatibility (top of mind for cloud architects evaluating
migration), then condense pricing into a single line, leaving extracted
action items as the closing sentence.
```

## Wall clock

End-to-end 11.7 seconds for 1,247-character Chinese input → full Indonesian brief with extracted action items.

## Token consumption profile per workload type

| Workload | Per-call tokens | Daily (5-person team) |
|---|---:|---:|
| Customer chat triage (ID → EN) | 600 | 600K |
| Vendor docs summarize (ZH → EN) | 12K | 1.5M |
| Slack thread digest | 800 | 800K |
| Compliance extract | 8K | 1.2M |
| Heartbeat / log triage | 400 | 2M |
| **Total / team** | | **~6M** |

Scale to 50 teams: **~300M tokens / day**, **~9B / month** — Plan Max ceiling.
