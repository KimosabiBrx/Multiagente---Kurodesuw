import os
import re
import unicodedata
from urllib.parse import urljoin, urlparse, quote_plus
from playwright.sync_api import sync_playwright
from .base import AgenteBase

class AgenteImagenes(AgenteBase):
    def __init__(self, nombre="Buscador de Imágenes"):
        super().__init__(nombre)

    def procesar_solicitud(self, datos):
        """
        Espera que datos contenga:
        - etiqueta: str (término de búsqueda)
        - max_imagenes: int (opcional, default 6)
        """
        etiqueta = datos.get("etiqueta", "")
        max_imagenes = datos.get("max_imagenes", 6)
        
        if not etiqueta:
            return {"exito": False, "imagenes": []}
        
        print(f"[{self.nombre}] Buscando imágenes para: {etiqueta}")
        imagenes = self._buscar_imagenes_hoyolab(etiqueta, max_imagenes)
        
        return {"exito": True, "imagenes": imagenes}

    def _buscar_imagenes_hoyolab(self, etiqueta: str, max_post=6):
        """
        Busca imágenes relacionadas con la etiqueta en múltiples fuentes.
        - Logs detallados en consola para ver candidatos, respuestas HTTP y razones.
        - Usa storage_state 'state.json' si existe para evitar 401 por recursos privados.
        - Umbral reducido a 0.5 para mayor recall.
        """
        def _normalize_text(s: str) -> str:
            if not s:
                return ""
            s = unicodedata.normalize("NFKD", s)
            s = "".join(c for c in s if not unicodedata.combining(c))
            return re.sub(r'\s+', ' ', s).strip().lower()

        def _token_overlap_score(a: str, b: str) -> float:
            ta = [t for t in re.split(r'\W+', _normalize_text(a)) if t]
            tb = [t for t in re.split(r'\W+', _normalize_text(b)) if t]
            if not ta or not tb:
                return 0.0
            set_a, set_b = set(ta), set(tb)
            inter = set_a.intersection(set_b)
            denom = (len(set_a) + len(set_b)) / 2.0
            return (len(inter) / denom) if denom > 0 else 0.0

        def _is_placeholder_image(src: str) -> bool:
            if not src:
                return True
            s = src.lower()
            if s.startswith("data:"):
                return True
            if s.endswith(".svg") and ("rp/" in s or "sprite" in s or "icons" in s):
                return True
            if "/rp/" in s or "/th?id=" in s or "placeholder" in s or "blank" in s:
                return True
            if re.search(r'/\d+x\d+(\.|/)|thumb|thumbnail', s):
                return True
            return False

        def _image_match_score(etiqueta: str, src: str, alt: str, parent_text: str, filename: str, figcaption: str) -> float:
            etiqueta_n = _normalize_text(etiqueta or "")
            if not etiqueta_n:
                return 0.0
            score = 0.0
            if etiqueta_n in _normalize_text(alt or ""):
                score += 1.0
            if etiqueta_n in _normalize_text(filename or ""):
                score += 1.0
            if etiqueta_n in _normalize_text(figcaption or ""):
                score += 1.0
            score += 0.45 * _token_overlap_score(etiqueta, parent_text or "")
            score += 0.45 * _token_overlap_score(etiqueta, src or "")
            return min(1.0, score)

        seeds = [
            f"https://www.hoyolab.com/search?keyword={quote_plus(etiqueta)}",
            f"https://www.bing.com/images/search?q={quote_plus(etiqueta)}",
            f"https://www.pixiv.net/en/tags/{quote_plus(etiqueta)}/artworks",
        ]

        found = []
        seen = set()
        state_file = "state.json"
        SCORE_THRESHOLD = 0.5

        try:
            with sync_playwright() as p:
                # Lanzar navegador con ignorar errores de HTTPS y argumentos para estabilidad
                browser = p.chromium.launch(
                    headless=True,
                    args=['--ignore-certificate-errors', '--ignore-ssl-errors']
                )
                
                if os.path.exists(state_file):
                    context = browser.new_context(
                        storage_state=state_file,
                        ignore_https_errors=True,
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    print(f"[{self.nombre}] Usando storage_state: {state_file}")
                else:
                    context = browser.new_context(
                        ignore_https_errors=True,
                         user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    print(f"[{self.nombre}] No se encontró storage_state; continuando sin sesión.")

                page = context.new_page()

                for seed in seeds:
                    if len(found) >= max_post:
                        break
                    try:
                        print(f"[{self.nombre}] Abriendo seed: {seed}")
                        network_images = set()

                        def on_response(resp):
                            try:
                                url = resp.url
                                ct = (resp.headers.get("content-type") or "").lower()
                                if resp.status == 200 and ct.startswith("image"):
                                    cleanu = url.split("#")[0].split("?")[0]
                                    network_images.add(cleanu)
                            except Exception:
                                pass

                        page.on("response", on_response)
                        page.goto(seed, wait_until='domcontentloaded', timeout=60000)
                        page.wait_for_timeout(800)
                        
                        page.evaluate("""
                            () => {
                                document.querySelectorAll('img').forEach(img => {
                                    try {
                                        const ds = img.getAttribute('data-src') || img.getAttribute('data-original') || img.dataset.src || img.dataset.original;
                                        if (ds) img.src = ds;
                                        const dss = img.getAttribute('data-srcset') || img.dataset.srcset;
                                        if (dss && !img.src) img.src = dss.split(',')[0].trim().split(' ')[0];
                                    } catch(e){}
                                });
                            }
                        """)
                        
                        for _ in range(10):
                            page.mouse.wheel(0, 1500)
                            page.wait_for_timeout(500)
                        page.wait_for_timeout(1000)

                        imgs = page.locator("img")
                        total = 0
                        try:
                            total = imgs.count()
                        except Exception:
                            total = 0
                        print(f"[{self.nombre}] imgs DOM detectadas: {total}, network captures: {len(network_images)}")

                        candidates = []
                        for i in range(total):
                            try:
                                src = imgs.nth(i).get_attribute("src") or imgs.nth(i).get_attribute("data-src") or imgs.nth(i).get_attribute("data-original") or ""
                                if not src:
                                    ss = imgs.nth(i).get_attribute("srcset") or ""
                                    if ss:
                                        src = ss.split(",")[0].strip().split(" ")[0]
                                src_clean = re.sub(r'\?.*$', '', src)
                                alt = imgs.nth(i).get_attribute("alt") or imgs.nth(i).get_attribute("title") or ""
                                parent_text = ""
                                try:
                                    parent_text = imgs.nth(i).locator("xpath=..").inner_text()
                                except Exception:
                                    parent_text = ""
                                filename = urlparse(src_clean).path.split("/")[-1] if src_clean else ""
                                figcaption = ""
                                try:
                                    el = imgs.nth(i).locator("xpath=ancestor::figure[1]//figcaption")
                                    if el.count() > 0:
                                        figcaption = el.nth(0).inner_text()
                                except Exception:
                                    figcaption = ""
                                if src_clean:
                                    abs_url = urljoin(page.url, src_clean)
                                    candidates.append((abs_url, alt, parent_text, filename, figcaption))
                            except Exception:
                                continue

                        for ni in network_images:
                            candidates.append((ni, "", "", ni.split("/")[-1], ""))

                        unique_candidates = []
                        for c in candidates:
                            u = c[0]
                            if not u:
                                continue
                            u_clean = re.sub(r'\?.*$', '', u)
                            if u_clean in seen:
                                continue
                            seen.add(u_clean)
                            unique_candidates.append((u_clean, c[1], c[2], c[3], c[4]))

                        print(f"[{self.nombre}] candidatos únicos: {len(unique_candidates)}")

                        for urlc, alt, parent_text, filename, figcaption in unique_candidates:
                            if len(found) >= max_post:
                                break
                            if _is_placeholder_image(urlc):
                                continue

                            score = _image_match_score(etiqueta, urlc, alt, parent_text, filename, figcaption)

                            status = None
                            try:
                                resp = page.request.get(urlc, timeout=8000)
                                status = resp.status
                            except Exception:
                                status = None

                            if status == 401:
                                try:
                                    headers = {"Referer": page.url}
                                    resp2 = page.request.get(urlc, headers=headers, timeout=8000)
                                    status = resp2.status
                                except Exception:
                                    pass

                            print(f"[{self.nombre}] candidato: {urlc} score={score:.2f} status={status} alt_len={len(alt)} filename='{filename}'")

                            if (score >= SCORE_THRESHOLD and status == 200) or (score >= 0.8 and (status is None or status == 200)):
                                clean_url = re.sub(r'\?.*$', '', urlc)
                                if clean_url not in found:
                                    found.append(clean_url)
                            else:
                                if status == 200 and score >= 0.45:
                                    clean_url = re.sub(r'\?.*$', '', urlc)
                                    if clean_url not in found:
                                        found.append(clean_url)

                        page.wait_for_timeout(400)
                        page.remove_listener("response", on_response)
                    except Exception as e:
                        print(f"[{self.nombre}] fallo seed {seed}: {e}")
                        try:
                            page.remove_listener("response", on_response)
                        except Exception:
                            pass
                        continue

                try:
                    page.close()
                    context.close()
                    browser.close()
                except Exception:
                    pass

        except Exception as e:
            print(f"[{self.nombre}] Error general: {e}")

        print(f"[{self.nombre}] encontrados: {len(found)} (limit {max_post}) -> {found[:max_post]}")
        return found[:max_post]
