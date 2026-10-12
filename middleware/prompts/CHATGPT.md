# Varian ChatGPT (GPT + connector MCP VPS)

Pakai `PIPELINE_DAILY.md` apa adanya, dengan perbedaan:

1. **Riset**: jika ChatGPT tidak punya Ubersuggest, gunakan web search untuk autocomplete/People Also Ask dan
   `app.py pool top` (pool berisi data Ubersuggest dari routine Claude). Tulis `research.primary_keyword.source`
   = `"pool"` atau `"web"` dengan jujur.
2. **Ilustrasi raster**: boleh membuat 1 ilustrasi topik dengan image generation memakai prompt Bull di
   `brand/BRAND_KIT.md §4`. Hasil 1080×1350 PNG. Kirim ke VPS lewat connector (write file) ke
   `sg-middleware/inbox/<dir>/media/illustration.png`, lalu daftarkan:
   ```json
   "illustration": {"kind": "image", "file": "media/illustration.png", "origin": "chatgpt_image_generation"}
   ```
   dan sertakan sebagai slide kedua carousel (`"assets": ["slides_01", "illustration", "slides_02", ...]`).
   Jika tidak ada jalur transfer byte yang nyata, JANGAN klaim terkirim — pakai template `illustration` + `art`.
3. **Tanpa akses shell**: jika connector hanya bisa menulis file, tulis bundle ke inbox dan minta user/Claude
   menjalankan `app.py ingest`. Atau kirim lewat HTTP (via SSH tunnel): `POST http://127.0.0.1:18790/api/v1/bundles`
   dengan header `Authorization: Bearer <state/api_token>` dan body `{"path": "<inbox dir>"}`.
4. Visual review tetap wajib atas file yang benar-benar dirender/diunggah.
