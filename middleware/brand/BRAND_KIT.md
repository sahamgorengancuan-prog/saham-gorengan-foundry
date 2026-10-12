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

Ciri yang WAJIB sama:
- **Gaya**: flat vector semi-realistis dengan **cel shading** 2–3 tone, outline **maroon gelap `#2B0A10`**
  (bukan hitam/navy), sedikit sudut 3/4.
- **Kepala**: wajah banteng panjang berbentuk baji, **moncong abu-abu gelap `#4B4F5E`** dengan lubang hidung
  gelap dan senyum smirk di moncong, alis tebal merah tua menaungi mata sipit percaya diri, jambul bulu runcing
  di dahi, bulu runcing di pipi.
- **Tanduk**: tebal, maroon gelap `#4A0A12`, melengkung keluar lalu naik dan **melengkung ke dalam** sehingga
  ujungnya saling menghadap di atas kepala (bentuk bulan sabit).
- **Telinga**: runcing seperti daun, menyamping.
- **Badan**: kepala besar duduk rendah di **bahu lebar berotot** (leher pendek-tebal), kulit merah `#D8192C`
  (bayangan `#A10F1E`, highlight `#F0434B`), bulu dada terlihat di kerah.
- **Pakaian**: kemeja kasual **teal gelap `#24485E`** (bayangan `#183244`), kerah terbuka, **lengan digulung
  di atas siku**, lengan bawah merah tebal, kepalan besar empat jari.
- **Aksen**: garis kilau emas `#F5C431` di dekat kepalan yang terangkat; props adegan: meja navy, monitor navy
  dengan grafik garis/candle biru muda, laptop silver dengan logo titik biru, ponsel.

Cara pakai di template: `{"source": "official", "art": "hero"}` merender file resmi 1:1 (cover/CTA/end card,
paling akurat). Untuk akting per adegan pakai rig vektor v2 (digambar mengikuti ciri di atas):
- Pose: idle, explain, celebrate, think, warn, present, shrug, wave, double_point.
- Ekspresi: smirk (default), happy, worried, serious, think, shock. Aksesori: glasses, tie, headset.
- Referensi render rig: `brand/mascot/bull-<pose>-<ekspresi>.png`.
- Kepribadian: mentor tenang, cerdas, sedikit jahil; jujur soal risiko; tidak serakah, tidak panik.
- Dilarang: moncong pink, kemeja biru terang, outline hitam, proporsi chibi/leher panjang, mengubah bentuk
  tanduk; uang tunai/karung uang/mobil mewah; logo pihak lain.

**Prompt image-gen (ChatGPT) — lampirkan `hero-bull-refined.webp` (dan file resmi lain) sebagai gambar
referensi, tempel prompt ini apa adanya, lalu tambah adegan:**
> Use the attached Saham Gorengan "Bull" artwork as the exact character reference — same character, same
> rendering style. Semi-realistic flat vector illustration with 2–3 tone cel shading and clean dark-maroon
> outlines. A muscular anthropomorphic red bull (#D8192C) in a slight 3/4 view: long wedge-shaped face with a
> charcoal-grey muzzle (#4B4F5E) and dark nostrils, smirk on the muzzle, heavy dark-red brow ridge over narrowed
> confident eyes, spiky fur tuft on the forehead and fur spikes on the cheeks and chest, thick dark-maroon horns
> (#4A0A12) that sweep outward and curl up and inward so the tips face each other above the head, pointed
> leaf-shaped ears sticking out sideways. Big head on broad muscular shoulders with a short thick neck. Dark-teal
> casual shirt (#24485E) with open collar and sleeves rolled above the elbow, thick red forearms, big
> four-finger fists, gold motion sparks (#F5C431) near a raised fist. Props in the same style: navy desk, navy
> monitors with light-blue line and candlestick charts, silver laptop with a blue dot logo. Background: deep
> navy-blue gradient (#071D48 → #0B58BC) with a soft glow, or transparent. No text except numbers, no logos,
> no cash. Scene: <metafora topik + aksi Bull + 3 props>. Portrait 1080×1350, keep the top 40% calm for text.

## 5. Gaya ilustrasi & motion
- **Karakter & props**: persis gaya ilustrasi situs (semi-realistis, cel shading, outline gelap). Jangan
  dibuat chibi/kartun bulat.
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
Header kartu: logo + "SAHAM GORENGAN" + nomor halaman. Footer: handle + domain. Bull selalu di bawah/samping,
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
