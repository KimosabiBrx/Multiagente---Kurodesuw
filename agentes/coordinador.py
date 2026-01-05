import json
import os
import re
from .base import AgenteBase
from .configuraciones import (
    CONFIG_HSR, CONFIG_ZZZ, CONFIG_GI,
    FUENTE_PRYDWEN, FUENTE_HONKAILAB, FUENTE_GENSHINLAB, FUENTE_GENSHINBUILD, FUENTE_GAMEWITH
)
from .investigador import AgenteInvestigador
from .analista import AgenteAnalista

class AgenteCoordinador(AgenteBase):
    def __init__(self, nombre="Coordinador"):
        super().__init__(nombre)
        self.investigador = AgenteInvestigador()
        self.analista = AgenteAnalista()

    def analizar_consulta(self, consulta):
        """
        Analiza la consulta del usuario para identificar juego, personaje y claves solicitadas.
        """
        consulta = consulta.lower().strip()
        
        # Detectar Juego
        juego = None
        if any(keyword in consulta for keyword in ["honkai", "star rail", "hsr"]):
            juego = "HSR"
        elif any(keyword in consulta for keyword in ["zenless", "zzz", "zone zero", "zenles"]):
            juego = "ZZZ"
        elif any(keyword in consulta for keyword in ["genshin", "impact", "gi"]): 
            juego = "GI" 
            
        if not juego:
            print(f"[{self.nombre}] No se detectó juego. Usando HSR por defecto.")
            juego = "HSR"

        # Extraer Nombre del Personaje
        nombre_personaje = None
        terminos_clave = r'\b(del|de|para|honkai|star\s*rail|zenless|zone\s*zero|zzz|y|o|hsr|genshin|impact|gi|build|general|completa|todo|discos|reliquias|artefactos|armas|arma|engine|cono|light\s*cone|stats|estadística|objetivo|target|final|substats|equipo|team|composición|partner|muestrame|quiero|la|el|los|las|un|una|y|teams|dame|vida|ataque|defensa|probabilidad\s*critica|daño\s*critico|maestria\s*elemental|w-engines|recarga\s*de\s*energía)\b'
        consulta_temp = re.sub(terminos_clave, ' ', consulta).strip()
        consulta_temp = re.sub(r'\s+', ' ', consulta_temp).strip()

        if consulta_temp:
            nombre_personaje = consulta_temp
            nombre_personaje = re.sub(r'[^\w\s-]', '', nombre_personaje).strip()

        if not nombre_personaje:
            ultima_palabra = consulta.split()[-1]
            if ultima_palabra not in ["hsr", "zzz", "build", "completa", "de", "la", "el", "gi", "impact"]:
                 nombre_personaje = re.sub(r'[^\w\s-]', '', ultima_palabra).strip()

        # Detectar Componentes Solicitados
        claves_solicitadas = ["character_name", "game", "build_name", "source", "Analisis_Gemini"]
        es_build_completa = any(keyword in consulta for keyword in ["build", "general", "completa", "todo"])
        
        if any(keyword in consulta for keyword in ["arma", "engine", "w-engine", "cono", "light cone"]): claves_solicitadas.append("weapon_recommendations")
        
        if juego in ["HSR", "ZZZ"]:
            if any(keyword in consulta for keyword in ["reliquia", "artefacto", "disco", "drive", "set", "ornamental"]):
                claves_solicitadas.extend(["artifact_set_recommendations", "planetary_set_recommendations", "main_stats_recommendations"])
        elif juego == "GI":
            if any(keyword in consulta for keyword in ["reliquia", "artefacto", "set", "tiara", "caliz", "arena"]):
                 claves_solicitadas.extend(["artifact_set_recommendations", "main_stats_recommendations"])

        if any(keyword in consulta for keyword in ["stats", "estadística", "objetivo", "target", "final", "substats", "vida", "ataque", "defensa", "critica", "maestria", "recarga"]): claves_solicitadas.append("final_stats_targets")
        if any(keyword in consulta for keyword in ["equipo", "team", "composición", "partner"]): claves_solicitadas.append("team_recommendations")

        if len(claves_solicitadas) <= 5 or es_build_completa:
            if juego == "GI":
                 claves_solicitadas.extend(["weapon_recommendations", "artifact_set_recommendations", "main_stats_recommendations", "final_stats_targets", "team_recommendations"])
            else:
                 claves_solicitadas.extend(["weapon_recommendations", "artifact_set_recommendations", "planetary_set_recommendations", "main_stats_recommendations", "final_stats_targets", "team_recommendations"])
        claves_solicitadas = list(dict.fromkeys(claves_solicitadas))

        return juego, nombre_personaje, claves_solicitadas

    def procesar_solicitud(self, juego, nombre_personaje, claves_solicitadas, eleccion_fuente, idioma_objetivo):
        """
        Orquesta las opciones de build.
        """
        if not nombre_personaje:
            return None, "No nombre de personaje válido."

        # Selección de Configuración
        if juego == "HSR":
            config_actual = CONFIG_HSR
            nombre_lab = FUENTE_HONKAILAB
            todas_fuentes = [
                (FUENTE_PRYDWEN, config_actual["url_base_primaria"], config_actual["segmento_ruta_primaria"]),
                (FUENTE_HONKAILAB, config_actual["url_base_terciaria"], config_actual["segmento_ruta_terciaria"]),
            ]
            mapa_fuentes = {'1': FUENTE_PRYDWEN, '2': nombre_lab}
        elif juego == "ZZZ":
            config_actual = CONFIG_ZZZ
            nombre_lab = FUENTE_GENSHINLAB
            todas_fuentes = [
                (FUENTE_PRYDWEN, config_actual["url_base_primaria"], config_actual["segmento_ruta_primaria"]),
                (FUENTE_GENSHINLAB, config_actual["url_base_terciaria"], config_actual["segmento_ruta_terciaria"]),
            ]
            mapa_fuentes = {'1': FUENTE_PRYDWEN, '2': nombre_lab}
        else: 
            config_actual = CONFIG_GI
            nombre_lab_1 = FUENTE_GENSHINBUILD
            nombre_lab_2 = FUENTE_GAMEWITH
            todas_fuentes = [
                (FUENTE_GENSHINBUILD, config_actual["url_base_primaria"], config_actual["segmento_ruta_primaria"]),
                (FUENTE_GAMEWITH, config_actual["url_base_secundaria"], config_actual["segmento_ruta_secundaria"]),
            ]
            mapa_fuentes = {'1': nombre_lab_1, '2': nombre_lab_2}

        # Prioridad de Fuente
        codigo_fuente_elegido = mapa_fuentes.get(eleccion_fuente)
        if codigo_fuente_elegido:
            prioridad_fuente = [s for s in todas_fuentes if s[0] == codigo_fuente_elegido]
            prioridad_fuente.extend([s for s in todas_fuentes if s[0] != codigo_fuente_elegido])
        else:
            prioridad_fuente = todas_fuentes

        if not idioma_objetivo:
            idioma_objetivo = "es"

        build_final = None
        razon_comparacion = ""
###############################################################
        #Bucle de Procesamiento llama al investigador e analista
        for codigo_fuente, url_base, segmento_ruta in prioridad_fuente:
            print(f"\n[{self.nombre}] Probando fuente: {codigo_fuente}")
            
            # 1. Paso Investigador
            # 1. Paso Investigador (Protocolo A2A)
            param_investigador = {
                "cabecera": {"de": self.nombre, "para": "Investigador", "accion": "OBTENER_DATOS"},
                "cuerpo": {
                    "url_base": url_base,
                    "nombre_personaje": nombre_personaje,
                    "segmento_ruta": segmento_ruta,
                    "codigo_fuente": codigo_fuente
                }
            }
            respuesta_sobre = self.investigador.recibir_mensaje(param_investigador)
            
            # Verificar respuesta del protocolo
            resultado_investigacion = {"exito": False}
            if respuesta_sobre.get("estado") == "OK":
                 resultado_investigacion = respuesta_sobre["cuerpo"]
            else:
                 print(f"[{self.nombre}] Error A2A con Investigador: {respuesta_sobre.get('error')}")

            if resultado_investigacion["exito"]:
                contenido_texto = resultado_investigacion["contenido_texto"]
                
                # 2. Paso Analista
                # 2. Paso Analista (Protocolo A2A)
                param_analista = {
                    "cabecera": {"de": self.nombre, "para": "Analista", "accion": "ANALIZAR_DATOS"},
                    "cuerpo": {
                        "juego": config_actual["juego"],
                        "nombre_personaje": nombre_personaje,
                        "contenido_texto": contenido_texto,
                        "esquema_build": config_actual["esquema_build"],
                        "tamano_equipo": config_actual["tamano_equipo"],
                        "idioma_objetivo": idioma_objetivo
                    }
                }
                
                respuesta_analista_sobre = self.analista.recibir_mensaje(param_analista)
                
                # Verificar respuesta del protocolo
                resultado_analista = None
                if respuesta_analista_sobre.get("estado") == "OK":
                     resultado_analista = respuesta_analista_sobre["cuerpo"]
                else:
                     print(f"[{self.nombre}] Error A2A con Analista: {respuesta_analista_sobre.get('error')}")

                if resultado_analista:
                    # Chequeo de Viabilidad
                    es_viable = any(v for k, v in resultado_analista.items() if k not in ["character_name", "game", "source", "build_name", "main_stats_recommendations"])
                    if es_viable:
                        build_final = resultado_analista
                        # Agregar metadatos (usando claves en inglés para compatibilidad json)
                        build_final["game"] = config_actual["esquema_build"]["game"]
                        build_final["source"] = codigo_fuente
                        build_final["character_name"] = nombre_personaje
                        
                        if codigo_fuente_elegido:
                            razon_comparacion = f"Seleccionada porque usuario eligió: {codigo_fuente_elegido}."
                        else:
                            razon_comparacion = f"Seleccionada como primera fuente viable (Prioridad: {codigo_fuente})."
                        break
        
        if build_final:
            self._guardar_build(build_final, claves_solicitadas, config_actual, juego, nombre_personaje, razon_comparacion)
            build_filtrada = {key: build_final.get(key) for key in claves_solicitadas if key in build_final}
            return build_filtrada, None
        else:
            return None, "No se pudo encontrar una build viable."

    def _guardar_build(self, build_final, claves_solicitadas, config_actual, juego, nombre_personaje, razon_comparacion):
        build_final["Analisis_Gemini"] = razon_comparacion
        ruta_archivo = config_actual["ruta_archivo"]
        
        if os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                try:
                    todas_builds = json.load(f)
                except json.JSONDecodeError:
                    todas_builds = {}
        else:
            todas_builds = {}
            
        clave_build = f"{juego.lower()}_{nombre_personaje.lower().replace(' ', '_')}"
        todas_builds[clave_build] = build_final
        
        with open(ruta_archivo, 'w', encoding='utf-8') as f:
            json.dump(todas_builds, f, indent=4, ensure_ascii=False)
