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

## 4. Maskot "Bull" (character sheet — wajib konsisten)
Banteng antropomorfik merah `#E5283C` (shade `#B71A2D`), moncong besar merah-muda `#F2606C` dengan dua lubang
hidung gelap, tanduk maroon `#5E0E18` melengkung keluar lalu ke atas-dalam, jambul kecil merah tua di antara
tanduk, telinga daun ke samping, mata setengah tertutup percaya diri dengan alis tebal gelap, senyum smirk
ramah. Kemeja biru berkerah `#1B4C8F` (kerah `#2D66B5`) dengan kancing emas. Tangan merah seperti manusia.
Outline navy tebal `#0A1633`, flat vector, tanpa tekstur bulu realistis.

- Pose: idle, explain, celebrate, think, warn, present, shrug, wave, double_point.
- Ekspresi: smirk (default), happy, worried, serious, think, shock. Aksesori: glasses, tie, headset.
- Referensi render: `brand/mascot/bull-<pose>-<ekspresi>.png` (rig) dan `brand/reference/hero-bull-refined.webp`
  (ilustrasi resmi situs).
- Kepribadian: mentor tenang, cerdas, sedikit jahil; jujur soal risiko; tidak serakah, tidak panik.
- Dilarang: mengubah warna/tanduk/kemeja/proporsi, uang tunai/karung uang/mobil mewah, logo pihak lain.

**Prompt image-gen (ChatGPT) — tempel apa adanya lalu tambah adegan:**
> Flat vector editorial illustration, Kurzgesagt-inspired geometric style with soft glows and star-dust on a
> deep navy (#05183A→#0B58BC) background. Main character: the Saham Gorengan "Bull" — an anthropomorphic red
> bull (#E5283C) with a large pink-red muzzle (#F2606C) and two dark nostrils, dark maroon horns (#5E0E18)
> sweeping outward then up and inward, a small dark-red tuft between the horns, sideways leaf-shaped ears,
> confident half-lidded eyes with thick dark brows and a friendly smirk, wearing a blue collared shirt
> (#1B4C8F) with gold buttons, human-like red hands, thick navy outlines (#0A1633), no fur texture. Palette
> only navy, blues, red #ED2A3C, gold #FFCD35, white. No text except numbers if needed, no logos, no cash.
> Scene: <metafora topik + aksi Bull + 3 props>. Portrait 1080×1350, keep the top 40% calm for headline text.

## 5. Gaya ilustrasi & motion
- **Kurzgesagt**: bentuk geometris membulat, kedalaman berlapis (navy → biru → aksen terang), 1 glow radial di
  fokus, partikel bintang, palet terbatas, outline hanya pada karakter & props utama.
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
