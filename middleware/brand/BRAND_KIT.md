# Saham Gorengan — Brand Kit & Aesthetic Reference (v1)

Sumber kebenaran mesin: `brand/brand.json` (warna, font, compliance, slot) + `sgmw/render/mascot.py`
(rig vektor Bull) + `sgmw/render/props.py` (props) + `sgmw/render/card.py` (template). Dokumen ini menjelaskan
aturannya untuk manusia, Claude, dan ChatGPT. Semua output harus terasa seperti **satu seri**.

## 1. Identitas
- **Nama**: Saham Gorengan / Komunitas Saham Gorengan · **Tagline**: Belajar saham tanpa drama.
- **Posisi**: komunitas edukasi saham Indonesia; Telegram gratis; SG Premium berbayar (Rp200rb/1 bln,
  Rp400rb/3 bln, Rp600rb/6 bln, Rp1jt/12 bln). Bukan pengelola dana, tidak menjanjikan profit.
- **Kanal**: sahamgorengan.id · IG @cuan_sahamgorengan · YouTube @SahamGorengan · t.me/sahamgorengancuan.

## 2. Warna
| Token | Hex | Pakai untuk |
|---|---|---|
| navy | `#05183A` | latar utama, outline gelap |
| deep_blue | `#09367B` | gradasi latar, panel |
| blue | `#0B438E` | panel, props |
| site gradient | `#071D48 → #073C8F → #0B58BC` | hero web, latar kartu |
| red | `#ED2A3C` | Bull, CTA, label MITOS, peringatan |
| gold | `#FFCD35` | highlight 1–3 kata, angka, label FAKTA |
| white | `#FAFDFF` | teks utama di latar gelap |
| muted / soft | `#B8D3FF` / `#D0E3FF` | teks sekunder |
| success / danger_soft | `#48E5AD` / `#FF7182` | grafik naik / turun, eyebrow |
Rasio: 60% navy-biru · 25% putih · 10% merah · 5% emas. Tidak ada warna di luar palet.

## 3. Tipografi
**Plus Jakarta Sans** saja (sama dengan situs). Display 800 (tracking -3%), heading 700–800, body 500–600,
label/eyebrow 800 UPPERCASE tracking 15%. Skala feed 1080×1350: display 92 · h1 72 · h2 54 · body 38 ·
small 28 · label 24. Video 1080×1920: headline 84–104 · caption 62 (outline navy 9px) · body 46.
Headline kartu ≤ 8 kata, frame video ≤ 6 kata. Highlight dengan `*kata*` → emas.

## 4. Maskot "Bull" (character sheet — wajib sama dengan ilustrasi sahamgorengan.id)
Sumber kebenaran: ilustrasi resmi di `sahamgorengan.id/assets/` → `brand/reference/hero-bull-refined.webp`
(Bull fist-pump di meja trading), `faq-bull.webp`, `community-bull-phone.webp`, `premium-bull-phone.webp`.

Ciri yang WAJIB sama (diverifikasi dari keempat file resmi):
- **Gaya**: flat vector modern **tanpa outline** — bentuk hanya isi warna; detail digambar dengan garis warna
  lebih gelap (helai bulu, lipatan jari, lipatan kemeja). Sedikit sudut 3/4 menghadap kanan.
- **Kepala**: moncong panjang dengan **moncong abu-abu gelap `#4A4B53`** menonjol di kanan-bawah wajah, lubang
  hidung gelap, garis senyum/seringai di moncong. **Mata kecil gelap** dengan kilau kecil di bawah **alis hitam
  tebal** (bentuk V = tegas/percaya diri, melengkung = ramah). Jambul bulu tersibak di dahi, bulu bergerigi di
  pipi, rahang, dan dada.
- **Tanduk**: pendek-tebal, maroon gelap `#5A1217` dengan pita lebih gelap, keluar-naik lalu ujungnya
  **melengkung ke dalam** di atas kepala.
- **Telinga**: besar berbentuk daun, menyamping di bawah tanduk (bagian dalam `#A80F18`).
- **Badan**: merah terang `#E5161F` (bayangan `#B9111A`), kepala besar di **bahu lebar berotot**, leher pendek.
- **Pakaian**: kemeja kasual **teal gelap `#1F4C60`** (lipatan `#11303E`), kerah terbuka, **lengan digulung di
  atas siku**, lengan bawah merah tebal, tangan besar empat jari.
- **Elemen pendukung**: garis kilau pendek-tebal emas `#F2B630` / biru `#1D63E6`, kartu UI putih (avatar, garis
  abu, bar hijau, candle mini), bubble chat biru, bubble "?" putih, monitor navy dengan grafik biru muda, laptop
  silver logo titik biru, ponsel dengan daftar saham.
- **Art resmi**: `hero` (fist-pump di meja trading), `faq` (shrug ramah + bubble tanya), `community` (seringai,
  menunjuk ponsel + kartu UI), `premium` (memegang ponsel raksasa berisi daftar saham).

Cara pakai di template: `{"source": "official", "art": "hero|faq|community|premium"}` merender file resmi 1:1
(paling akurat — utamakan untuk cover, CTA, end card, dan adegan yang aksinya cocok). Untuk akting lain pakai rig
vektor v3 (flat tanpa outline, digambar mengikuti ciri di atas):
- Pose: idle, explain, celebrate, think, warn, present, shrug, wave, double_point.
- Ekspresi: smirk (default), happy, worried, serious, think, shock. Aksesori: glasses, tie, headset.
- Referensi render rig: `brand/mascot/bull-<pose>-<ekspresi>.png`.
- Kepribadian: mentor tenang, cerdas, sedikit jahil; jujur soal risiko; tidak serakah, tidak panik.
- Dilarang: outline apa pun di sekeliling karakter, moncong pink, kemeja biru terang, mata kartun putih besar,
  proporsi chibi/leher panjang, mengubah bentuk tanduk; uang tunai/karung uang/mobil mewah; logo pihak lain.

**Prompt image-gen (ChatGPT) — lampirkan `hero-bull-refined.webp` (dan file resmi lain) sebagai gambar
referensi, tempel prompt ini apa adanya, lalu tambah adegan:**
> Use the attached Saham Gorengan "Bull" artworks as the exact character and style reference — same character,
> same rendering. Modern flat vector illustration with NO outlines: pure colour fills, details only as darker
> same-hue lines. A muscular anthropomorphic bright-red bull (#E5161F) in a slight 3/4 view: long snout with a
> charcoal-grey muzzle (#4A4B53) protruding on the lower right, dark nostrils, confident grin on the muzzle, small
> dark eyes under thick near-black brows, swept fur tuft on the forehead and jagged fur on the cheeks, jaw and chest,
> short thick dark-maroon horns (#5A1217) with darker bands that curve out, up and inward over the head, big
> leaf-shaped ears sticking out sideways. Big head on broad muscular shoulders. Dark-teal casual shirt (#1F4C60)
> with open collar and sleeves rolled above the elbow, thick red forearms, big four-finger hands. Supporting
> elements in the same flat style: white fintech UI cards with grey text lines, green bars and mini candlesticks,
> blue chat bubbles, navy monitors with light-blue charts, short thick gold/blue spark strokes. Background: site
> navy-blue gradient (#071D48 → #0B58BC) or transparent. No text except numbers, no logos, no cash.
> Scene: <metafora topik + aksi Bull + 3 props>. Portrait 1080×1350, keep the top 40% calm for text.

## 5. Gaya ilustrasi & motion
- **Karakter & props**: persis gaya ilustrasi situs (flat modern tanpa outline, detail garis warna gelap).
  Jangan dibuat kartun ber-outline atau chibi.
- **Latar (Kurzgesagt)**: gradasi navy situs, kedalaman berlapis, 1 glow radial di fokus, partikel bintang
  halus, palet terbatas.
- **OverSimplified**: akting karakter jelas dan lucu, ekspresi berlebihan, timing komedi; humor tidak pernah
  merendahkan orang yang rugi.
- Motion: elemen masuk `pop`/`rise`/`slide` 0,35–0,5 dtk (ease-out-back), props `float`, kamera push-in 3–6%,
  dip-to-navy 0,18 dtk antar scene, caption selalu menyala, progress bar emas, end card 1,6 dtk.
- Suara: edge-tts `id-ID-ArdiNeural` (+6%), alternatif `id-ID-GadisNeural`. Musik opsional dengan ducking
  (taruh file berlisensi di `brand/music/`).

## 6. Layout & safe zone
| Format | Ukuran | Safe area (atas/kanan/bawah/kiri) |
|---|---|---|
| Feed IG/FB | 1080×1350 | 72/72/96/72 |
| Reels/Shorts | 1080×1920 | 230/150/430/80 (UI platform menutupi atas, bawah, kanan) |
| YouTube thumb | 1280×720 | 48/220/80/48 |
| OG link | 1200×630 | 48 semua |
| Hero web | 1600×900 | 64 semua |
Header kartu: logo KSG resmi (kepala banteng merah bergaris kecepatan, tanpa lingkaran) + "SAHAM GORENGAN" +
nomor halaman. Cover utama memakai template `explainer` (replika kartu lama situs: label merah, headline kapital
emas, panel chart + kotak "BULL EXPLAINS" berbingkai emas, footer domain/handle). Footer: handle + domain. Bull selalu di bawah/samping,
tidak menutupi teks.

## 7. Suara & copy
Bahasa Indonesia santai-profesional, sapaan "kamu", kalimat pendek, jelaskan sebab-akibat, contoh angka
HIPOTETIS, akui batasan. Disclaimer singkat di setiap post: "Edukasi, bukan ajakan beli/jual."
Frasa terlarang (diblok otomatis): pasti cuan/untung/naik, dijamin profit, auto cuan/kaya, cepat kaya, tanpa
risiko, 100% profit, sinyal pasti, pengelola/kelola/titip dana, premium gratis.

## 8. Platform playbook
| Platform | Format | Copy | Teknis (dicek middleware) |
|---|---|---|---|
| Web | artikel 1.100–1.600 kata | title 45–60 kar (keyword di depan), meta 130–155, H1 tunggal, TL;DR, TOC, FAQ, sumber, internal link | canonical, OG/Twitter, JSON-LD Article+Breadcrumb+FAQ, alt gambar, ≥ 900 kata |
| Instagram feed | carousel 7–9 × 1080×1350 | baris 1 hook ≤ 125 kar, 3–5 baris nilai, CTA simpan/bagikan, ≤ 5 hashtag, alt text tiap slide | rasio 4:5, PNG/JPEG ≤ 8 MB, 2–10 slide |
| Instagram Reels | MP4 9:16 35–55 dtk | caption seperti feed, cover dari template | H.264/AAC, 9:16, ≤ 180 dtk, share_to_feed |
| Facebook | photos (3 slide) + reel | 2–4 paragraf pendek, link artikel (UTM otomatis), ≤ 3 hashtag | 1–10 foto |
| YouTube Shorts | MP4 9:16 ≤ 60 dtk | title ≤ 70 kar + #Shorts, deskripsi: 2 baris keyword + jawaban, link, 8–15 tags, 3 hashtag | kategori Education (27), bahasa id, caption SRT otomatis |

## 9. Jadwal (WIB)
Web 10:30 · Instagram 15:00 · Facebook 15:30 · Reels & Shorts 17:00 (FB reel 17:10) · riset 19:00 untuk besok.
Post sosial menunggu artikel web terbit (link tidak boleh 404).
