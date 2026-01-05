import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from .base import AgenteBase
from .utilidades import limpiar_url_markdown
from .configuraciones import (
    CONFIG_GI, 
    FUENTE_PRYDWEN, FUENTE_GAME8, FUENTE_HONKAILAB,
    FUENTE_GENSHINLAB, FUENTE_GENSHINBUILD, FUENTE_GAMEWITH
)

class AgenteInvestigador(AgenteBase):
    def __init__(self, nombre="Investigador"):
        super().__init__(nombre)

    def procesar_solicitud(self, datos):
        """
        Espera que datos contenga:
        - url_base
        - nombre_personaje
        - segmento_ruta
        - codigo_fuente
        """
        url_base = datos.get("url_base")
        nombre_personaje = datos.get("nombre_personaje")
        segmento_ruta = datos.get("segmento_ruta")
        codigo_fuente = datos.get("codigo_fuente")
        
        print(f"[{self.nombre}] Buscando URL...")
        url_personaje = self.obtener_url_personaje(url_base, nombre_personaje, segmento_ruta, codigo_fuente)
        
        if url_personaje:
            print(f"[{self.nombre}] Obteniendo contenido de {url_personaje}...")
            sopa = self.obtener_y_analizar(url_personaje, codigo_fuente)
            if sopa:
                print(f"[{self.nombre}] Extrayendo texto...")
                contenido_texto = self.extraer_texto(sopa, codigo_fuente)
                return {"exito": True, "contenido_texto": contenido_texto, "url": url_personaje}
        
        return {"exito": False, "error": "No se pudo recuperar el contenido."}

    def obtener_url_personaje(self, url_base, nombre_personaje, segmento_ruta, codigo_fuente):
        url_base = limpiar_url_markdown(url_base)
        target_name_normalized = nombre_personaje.strip().lower().replace(" ", "-").replace("_", "-").replace("'", "")
        target_name_simple = nombre_personaje.strip().lower()
        
        segmento_enlace_check = ""
        
        if codigo_fuente == FUENTE_GAMEWITH:
            # Chequeo de Mapa de ID
            target_name_key = target_name_normalized.replace("-", "")
            mapa_gamewith = CONFIG_GI.get("mapa_id_gamewith", {})
            
            if target_name_key in mapa_gamewith:
                  id_articulo = mapa_gamewith[target_name_key]
                  url_completa = f"https://gamewith.jp/genshin/article/show/{id_articulo}"
                  print(f"[{self.nombre}] Enlace GameWith encontrado por ID: {url_completa}")
                  return url_completa
            segmento_enlace_check = target_name_normalized 
          
        elif codigo_fuente == FUENTE_PRYDWEN:
            segmento_enlace_check = f"{segmento_ruta}{target_name_normalized}"
        elif codigo_fuente == FUENTE_HONKAILAB or codigo_fuente == FUENTE_GENSHINLAB: 
            segmento_enlace_check = f"{target_name_normalized}-build"
        elif codigo_fuente == FUENTE_GENSHINBUILD: 
            segmento_enlace_check = f"{segmento_ruta}{target_name_normalized}"
        
        print(f"[{self.nombre}] Buscando enlace para: {nombre_personaje} en {url_base}")
        
        try:
            with sync_playwright() as p:
                navegador = p.chromium.launch(headless=True)
                pagina = navegador.new_page()
                pagina.goto(url_base, wait_until='domcontentloaded', timeout=90000) 
                
                # Espera dinámica para Prydwen
                if codigo_fuente == FUENTE_PRYDWEN:
                    selector_a_esperar = 'a[href*="/agents/"], a[href*="/characters/"]'
                    try:
                        pagina.wait_for_selector(selector_a_esperar, timeout=20000)
                    except Exception as e:
                        print(f"Advertencia: Selector de lista Prydwen no apareció. Fallback 5s. Error: {e}")
                        pagina.wait_for_timeout(5000)
                else:
                    pagina.wait_for_timeout(5000)
    
                contenido_html = pagina.content()
                navegador.close()
                
                sopa = BeautifulSoup(contenido_html, 'html.parser')
                enlace = None
                
                if codigo_fuente == FUENTE_GAMEWITH and url_base.count('/') > 4: 
                    print(f"La URL base parece ser un artículo: {url_base}")
                    return url_base
    
                # Estrategia 1: Busqueda por slug en HREF
                if segmento_enlace_check:
                    enlace = sopa.find('a', href=lambda href: href and segmento_enlace_check in href)
                
                # Estrategia 2: Busqueda por texto
                if not enlace:
                    print(f"[{self.nombre}] Fallback a búsqueda por texto para {codigo_fuente}.")
                    todos_los_enlaces = sopa.find_all('a', href=True)
                    busqueda_normalizada = target_name_simple.replace(" ", "").replace("_", "").replace("'", "")
                    
                    for a in todos_los_enlaces:
                        texto_enlace = a.get_text(strip=True).strip().lower()
                        texto_enlace_normalizado = texto_enlace.replace(" ", "").replace("_", "").replace("'", "")
                        
                        if texto_enlace_normalizado == busqueda_normalizada:
                            enlace = a
                            break
                        
                        if len(busqueda_normalizada) > 3 and busqueda_normalizada in texto_enlace_normalizado:
                            if any(char.isalpha() for char in texto_enlace): 
                                enlace = a
                                break
    
                if enlace:
                    url_completa = enlace['href']
                    if not url_completa.startswith("http"):
                        if codigo_fuente == FUENTE_PRYDWEN:
                            url_completa = "https://www.prydwen.gg" + url_completa
                        elif codigo_fuente == FUENTE_HONKAILAB:
                            url_completa = "https://honkailab.com" + url_completa
                        elif codigo_fuente == FUENTE_GENSHINLAB:
                            url_completa = "https://genshinlab.com" + url_completa
                        elif codigo_fuente == FUENTE_GENSHINBUILD: 
                            url_completa = "https://genshin-builds.com" + url_completa
                        elif codigo_fuente == FUENTE_GAMEWITH: 
                            url_completa = "https://gamewith.jp" + url_completa 
                            
                    url_completa = limpiar_url_markdown(url_completa)
                    print(f"[{self.nombre}] Enlace encontrado: {url_completa}")
                    return url_completa
                else:
                    print(f"[{self.nombre}] Enlace no encontrado para '{nombre_personaje}'.")
                    return None
    
        except Exception as e:
            print(f"Error en obtener_url_personaje para {codigo_fuente}: {e}")
            return None

    def obtener_y_analizar(self, url, codigo_fuente):
        url = limpiar_url_markdown(url)
        print(f"[{self.nombre}] Playwright obteniendo: {url}")
        try:
            with sync_playwright() as p:
                navegador = p.chromium.launch(headless=True)
                pagina = navegador.new_page()
                pagina.goto(url, wait_until='domcontentloaded', timeout=90000) 
                pagina.wait_for_timeout(5000)
                
                # Manejo de pop-ups
                selectores_cookies = ['text="Accept"', 'text="Aceptar"', 'text="I accept"', 'text="Consent"'] 
                try:
                    for selector in selectores_cookies:
                        pagina.click(selector, timeout=100) 
                except:
                    pass
                    
                pagina.wait_for_selector('h1, article, body', timeout=15000) 
                pagina.wait_for_timeout(2000) 
    
                contenido_html = pagina.content()
                navegador.close()
                return BeautifulSoup(contenido_html, 'html.parser')
    
        except Exception as e:
            print(f"[{self.nombre}] Error obteniendo {codigo_fuente}: {e}")
            return None

    def extraer_texto(self, sopa, fuente):
        if fuente == FUENTE_PRYDWEN:
             seccion_build = sopa.find('div', id='page-content') or sopa.main
        elif fuente == FUENTE_GAME8:
             seccion_build = sopa.find('article', class_=re.compile(r'a-article')) or sopa.main
        elif fuente == FUENTE_HONKAILAB or fuente == FUENTE_GENSHINLAB: 
             seccion_build = sopa.find('div', class_='entry-content') or sopa.main
        elif fuente == FUENTE_GENSHINBUILD: 
             seccion_build = sopa.find('div', class_='main-content') or sopa.find('article') or sopa.main
        elif fuente == FUENTE_GAMEWITH: 
             seccion_build = sopa.find('div', class_='gdb_col_content') or sopa.find('div', id='page_content') or sopa.main
        else:
            seccion_build = None

        if not seccion_build:
             seccion_build = sopa.body
        
        if seccion_build:
            texto_completo = seccion_build.get_text(separator=' ', strip=True)
            if len(texto_completo) < 500:
                print(f"[{self.nombre}] Texto extraído muy corto (<500 caracteres).")
                return ""
            return texto_completo
        return ""
