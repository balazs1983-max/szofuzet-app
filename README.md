# Szófüzet – gyakorló app

Ez a tárhely a gyakorló app forrása. A GitHub Pages innen szolgálja ki az appot: https://balazs1983-max.github.io/szofuzet-app/

- `docs/` – maga az app, ezt szolgálja ki a GitHub Pages. Ne szerkeszd kézzel, a `build/build.py` állítja elő.
- `build/template.html` – az app sablonja (a Szófüzet oldalból kivéve; ha az app változik, ez is frissül).
- `build/static/` – ikonok, manifest, service worker.
- `build/build.py` – a Szófüzet adataiból (szavak, haladás, foci-tények) elkészíti a `docs/` mappát. Csak akkor ír, ha változott valami.

A frissítést egy ütemezett Claude-feladat végzi naponta: kiolvassa a Szófüzet adatait, lefuttatja a `build.py`-t, és ha van változás, feltölti ide. A GitHub Pages pár percen belül közzéteszi ugyanazon a címen.
