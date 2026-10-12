# Keyword research playbook (Ubersuggest MCP)

## Parameter tetap
- Lokasi Indonesia: `locId: 2360`, `language: "id"`; `google_suggestions`: `country: "id"`, `language: "id"`.
- Kuota: cek `user_limits` → `usage.account.reports.{used,limit}` (paket saat ini: **3 report/hari**,
  `monthly_keyword_metrics_updates` 10/bulan — jangan pakai `keyword_metrics` kecuali benar-benar perlu).

## Rotasi seed per hari (`target_day`, mengikuti content mix brand)

| Hari | Pilar | Seed `match_keywords` (maks 3 per call) |
|---|---|---|
| Senin | indikator | "indikator saham", "analisa teknikal saham", "cara membaca chart saham" |
| Selasa | berita/regulasi | "saham gorengan", "papan pemantauan khusus", "suspensi saham" |
| Rabu | konsep | "ara arb saham", "bid offer saham", "lot saham" |
| Kamis | rekomendasi (edukasi cara membaca screening; ticker hanya jika ada data resmi bertanggal) | "rekomendasi saham", "saham gorengan hari ini", "screener saham" |
| Jumat | berita/pasar | "ihsg", "saham indonesia", "dividen saham" |
| Sabtu | psikologi & risiko | "fomo saham", "cut loss saham", "money management saham" |
| Minggu | pemula/komunitas | "cara main saham", "saham untuk pemula", "modal main saham" |

Boleh ganti seed bila pool sudah punya > 30 kandidat belum terpakai untuk pilar itu (hemat kuota → pakai
call untuk `serp_analysis` saja).

## Urutan call (maks 3)
1. `match_keywords` (seed hari ini, `limit: 100`, `sortby: "-search_volume"`) → simpan JSON mentah ke
   `sg-middleware/state/cache/ubersuggest-<YYYY-MM-DD>-match.json` → `app.py pool add <file> --cluster <pilar>`.
2. `google_suggestions` untuk 1–3 kandidat teratas → simpan → ubah jadi baris `{keyword, question: true}`
   untuk frasa berbentuk pertanyaan → `pool add` (tanpa metrik; dipakai sebagai bukti "most searched question"
   dan bahan FAQ).
3. `serp_analysis` (`limit: 10`, `locId: 2360`, `language: "id"`) untuk kandidat final → bukti answer gap.

Jika `reports` tersisa < 3: lewati langkah 1 (pakai pool), atau lewati 2 (pakai WebSearch "<keyword>"
untuk melihat People Also Ask & autocomplete).

## Definisi filter
- **Low competition**: `sd` (SEO difficulty) ≤ 30. Tie-break: `competition` (iklan) ≤ 0,33 lebih baik.
- **Very high volume**: `app.py pool top` memberi `tier`: `very_high` = kuartil atas kandidat dan ≥ 1.000/bln.
  Contoh baseline Okt-2026: "cara main saham" 8.100 (sd 18), "saham gorengan adalah" 2.400 (sd 17),
  "jam bursa saham indonesia" 1.900 (sd 20), "apa itu saham gorengan" 720 (sd 13).
- Intent: utamakan `Informational`. `Commercial` (mis. "aplikasi saham") hanya untuk konten edukasi netral
  tanpa endorse broker.
- Tolak: keyword merek pihak ketiga (stockbit, ajaib, bibit, broker tertentu) sebagai fokus, crypto/forex,
  "grup wa saham", topik yang memaksa rekomendasi ticker tanpa data.

## Keluaran ke bundle (`research`)
```json
{"cluster":"konsep","seed_keywords":["ara arb saham"],
 "primary_keyword":{"keyword":"...","volume":2400,"sd":17,"pd":1,"competition":0,"intent":"Informational","source":"ubersuggest","fetched":"2026-10-12"},
 "secondary_keywords":[{"keyword":"...","volume":720,"sd":13}],
 "question":{"text":"Kenapa saham gorengan bisa ARA lalu ARB?","variants":["..."],"type":"unanswered","evidence":"Top 10: ... tidak ada simulasi order book; 3 hasil forum; aturan ARB lama.","gap_score":0.8},
 "serp_top":[{"url":"...","note":"tipis/usang/forum"}],
 "ubersuggest_reports_used":3}
```
