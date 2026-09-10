# VORTEX SFILE ULTIMATE — Railway

1. Upload semua isi folder ini ke repository GitHub.
2. Railway → New Project → Deploy from GitHub.
3. Railway otomatis membaca Dockerfile.
4. Generate Domain dari Railway.
5. Buka `/health` untuk cek service.

Fix penting versi ini:
- Node.js ikut di-install di container.
- `sfile.mobi` otomatis dinormalisasi ke `sfile.co`.
- Kegagalan metadata tidak lagi mematikan resolver.
- Error resolver ditampilkan ke Web UI, bukan hanya "exit status 1".
- Direct URL/CDN URL dipilih otomatis.
