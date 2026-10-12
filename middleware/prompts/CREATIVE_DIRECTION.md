# Creative direction — "LLM brain" untuk aset multi-platform

## 1. Dari pertanyaan ke thesis
- **Thesis** = satu kalimat insight yang non-obvious dan benar. Contoh lemah: "Saham gorengan berisiko."
  Contoh kuat: "Persen naik itu hasil; likuiditas antrean jual yang menentukan apakah kamu bisa keluar."
- Turunkan: 1 miskonsepsi populer → koreksi; 1 mekanisme sebab-akibat; 1 simulasi hipotetis berangka; 1 batasan
  (kapan teori ini tidak berlaku); 1 aksi praktis.

## 2. Metafora visual (wajib unik per topik)
Pilih metafora fisik yang menjelaskan MEKANISME, lalu 3 props pendukung. Contoh:
| Konsep | Metafora | Props |
|---|---|---|
| Likuiditas tipis | wajan gorengan kecil: sedikit minyak cepat panas & cepat gosong | `wok`, `fire`, `hourglass` |
| ARA/ARB | lift dengan batas lantai atas/bawah | `arrow_up`, `arrow_down`, `lock` |
| Order book | antrean kasir di dua sisi | `crowd`, `scale`, `document` |
| FOMO | kerumunan lari ke satu pintu | `crowd`, `megaphone`, `warning` |
| Manajemen risiko | pelampung + target | `shield`, `target`, `piggy` |
Props tersedia (render konsisten): arrow_down, arrow_up, building, calendar, candles, chart_down, chart_up,
clock, coin, crowd, desk, document, fire, gauge, hourglass, laptop (silver, logo biru), lightbulb, lock, magnifier,
megaphone, money, monitor (navy + grafik biru muda, seperti situs), phone, piggy, rocket, scale, shield, target,
warning, wok; elemen UI gaya art resmi: ui_card_profile, ui_card_chart, ui_card_trend, chat_bubble, question_bubble,
user_badge, sparks_gold, sparks_blue, phone_app. Semua flat tanpa outline (sama dengan art resmi). Boleh menambah SVG kustom (`art.svg`) dengan gaya
yang sama: flat, outline navy `#0A1633` 6–8px, sudut membulat, palet brand saja.

## 3. Bull acting (OverSimplified-style)
Karakter harus identik dengan ilustrasi sahamgorengan.id (lihat BRAND_KIT §4). Untuk cover, CTA, dan end card
utamakan art resmi: `"mascot": {"source": "official", "art": "hero"}` (fist-pump di meja trading), `faq` (shrug +
bubble tanya — cocok untuk "tidak ada jawaban resmi"/pertanyaan), `community` (menunjuk ponsel + kartu UI — cocok
untuk "cek data/aplikasi"), `premium` (ponsel raksasa berisi daftar saham — cocok untuk screening/watchlist). Untuk adegan yang butuh akting spesifik pakai rig:
Pose: idle, explain, celebrate, think, warn, present, shrug, wave, double_point.
Ekspresi: smirk (default), happy, worried, serious, think, shock. Aksesori: none, glasses (analitis), tie
(formal/regulasi), headset (berita/live).
Aturan: reaksi besar dan jelas (shock saat angka mengejutkan, think saat pertanyaan, warn saat risiko,
present saat menjelaskan grafik, celebrate hanya untuk *pemahaman*, bukan profit). Bull tidak pernah memegang
uang tunai/karung uang. Selang-seling sisi (`side: left/right`) antar scene agar dinamis.

## 4. Arc narasi short (Kurzgesagt) — 35–55 detik
1. **Hook (0–1,5 dtk)**: pertanyaan atau angka mengejutkan di layar + Bull `shock`/`think`.
2. **Konteks (1 scene)**: kenapa orang peduli.
3. **Mekanisme (2–3 scene)**: metafora bergerak (props `pop`/`float`, `counter` untuk angka).
4. **Taruhannya (1 scene)**: risiko/miskonsepsi — Bull `warn`/`worried`, bg `red` boleh 1 scene.
5. **Insight (1 scene)**: thesis dalam ≤ 6 kata di headline.
6. **Aksi (1 scene)**: 1 langkah praktis + "versi lengkap + hitungan di sahamgorengan.id".
Teks layar ≤ 6 kata; VO santai-profesional, "kamu", kalimat ≤ 14 kata; angka di VO dieja.

Contoh scene:
```json
{"vo":"Kenapa saham kecil bisa naik tiga puluh lima persen cuma dalam dua hari?",
 "caption":"Kenapa saham kecil bisa naik *35%* dalam 2 hari?",
 "headline":"Naik *35%* dalam 2 hari?","bg":"navy",
 "mascot":{"pose":"think","expression":"shock","side":"right"},
 "counter":{"from":0,"to":35,"suffix":"%","x":330,"y":880,"size":220},
 "camera":{"zoom":[1.0,1.06]}}
```
Koordinat panggung video 1080×1920: headline 270–600, panggung 600–1340 (Bull berdiri di 1340), caption ~1420,
bawah 1500+ tertutup UI platform. Props `x` 200–880, `y` 700–1200, `size` 220–380.

## 5. Carousel IG (7–9 slide)
Slide 1 utamakan `explainer` (replika kartu situs: `label`, `headline` kapital emas, `subhead`, `chart_points` atau
`art`, `mascot` resmi, `strip`). Alternatif `cover` (hook ≤ 8 kata, 1–3 kata *highlight*, Bull pose sesuai emosi) → isi (`point` bernomor / `stat` /
`myth_fact` / `example` HIPOTETIS / `checklist` / `illustration` dengan `art`) → `cta`.
Satu slide = satu ide; body ≤ 45 kata. Contoh `point` dengan art:
```json
{"template":"point","alt":"Bull menunjuk wajan kecil yang cepat panas sebagai metafora likuiditas tipis",
 "data":{"number":2,"eyebrow":"Mekanisme","heading":"Wajan kecil cepat *panas*",
  "body":"Saham dengan antrean jual tipis seperti wajan dengan sedikit minyak: dorongan kecil langsung terasa besar.",
  "art":{"viewbox":"0 0 936 420","props":[{"name":"wok","x":300,"y":230,"size":300},{"name":"fire","x":300,"y":360,"size":120}],
         "mascot":{"pose":"present","expression":"smirk","x":690,"y":420,"height":400}}}}
```
Template lain: `stat` {value,label,context,source}, `myth_fact` {myth,fact}, `example` {heading,scenario,steps[],result},
`checklist` {heading,items[]}, `quote` {text}, `illustration` {art (viewbox 0 0 1080 1350), headline, caption},
`cta` {} (default CTA brand).

## 6. Artikel web
Struktur: jawaban langsung di `tldr` → section mekanisme → contoh Indonesia → simulasi HIPOTETIS → miskonsepsi →
batasan → checklist → FAQ (varian pertanyaan Google). Paragraf 2–4 kalimat, subjudul berbentuk pertanyaan,
keyword utama di title, H1, paragraf pertama, satu H2, dan meta description — alami, tanpa stuffing.
