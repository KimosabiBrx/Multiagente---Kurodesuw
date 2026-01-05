import json
import os
from google import genai
from google.genai.errors import APIError
from dotenv import load_dotenv
from .base import AgenteBase

class AgenteAnalista(AgenteBase):
    def __init__(self, nombre="Analista"):
        super().__init__(nombre)
        load_dotenv()
        try:
            self.cliente = genai.Client()
        except Exception as e:
            print(f"[{self.nombre}] ERROR: No se pudo inicializar cliente Gemini. Detalle: {e}")
            self.cliente = None
        
        self.modelo_completado = "gemini-2.5-flash"

    def procesar_solicitud(self, datos):
        """
        Espera que datos contenga:
        - juego
        - nombre_personaje
        - contenido_texto
        - esquema_build
        - tamano_equipo
        - idioma_objetivo
        """
        if not self.cliente:
            return None

        juego = datos['juego']
        nombre_personaje = datos['nombre_personaje']
        contenido_texto = datos['contenido_texto']
        esquema_build = datos['esquema_build']
        tamano_equipo = datos['tamano_equipo']
        idioma_objetivo = datos.get('idioma_objetivo', 'es')

        return self.analizar_texto_con_gemini(
            juego, nombre_personaje, contenido_texto, esquema_build, tamano_equipo, idioma_objetivo
        )

    def analizar_texto_con_gemini(self, juego, nombre_personaje, contenido_texto, esquema_build, tamano_equipo, codigo_idioma_objetivo="es"):
        if juego == "HSR":
            terminos_juego = """
            **TÉRMINOS CLAVE HSR:**
            - Light Cone (Cono de Luz / Arma) - Relics (Reliquias / Set de 4 piezas)
            - Planar Ornaments (Ornamentos Planetarios / Set de 2 piezas)
            - Estadísticas Únicas: Effect RES, Effect HIT Rate, Break Effect, Energy Regen Rate.
            """
            tipo_equipo = "personajes"
        elif juego == "ZZZ":
            terminos_juego = """
            **TÉRMINOS CLAVE ZZZ:**
            - W-Engine (Motor W / Arma) - Drives (Componentes de 4 piezas)
            - Sub/Core Drives (Componentes de 2 piezas)
            - Estadísticas Únicas: Impact Rating, Energy Charge, Anomaly Proficiency, Attribute DMG.
            """
            tipo_equipo = "agentes"
        else: 
            terminos_juego = """
            **TÉRMINOS CLAVE GI:**
            - Weapon (Arma) - Artifacts (Artefactos / Sets de 4 ó 2 piezas combinadas)
            - Artefactos con Main Stat variable: Sands (Arena del Tiempo), Goblet (Cáliz de Eonotemo), Circlet (Tiara de Logos).
            - Estadísticas Únicas: Maestria Elemental, Recarga de Energía.
            """
            tipo_equipo = "personajes"

        nombre_idioma = {
            "es": "ESPAÑOL", "en": "INGLÉS", "jp": "JAPONÉS", "cn": "CHINO", "fr": "FRANCÉS", 'cr': "COREANO"
        }.get(codigo_idioma_objetivo.lower(), "ESPAÑOL")

        contenido_json_schema = json.dumps(esquema_build, indent=4, ensure_ascii=False)
        
        instruccion_equipo = f"""Busca las 3 composiciones de equipo más relevantes y variadas que incluyan a '{nombre_personaje}'.
        Cada entrada en la lista 'team_recommendations' debe ser una única CADENA de texto, conteniendo los nombres de los **{tamano_equipo} {tipo_equipo}** separados por comas y TRADUCIDOS al {nombre_idioma}.
        Ejemplo para HSR/GI: ["Acheron, Sparkle, Pela, Lynx", "Blade, Bronya, Pela, Lynx"].
        Ejemplo para ZZZ: ["Billy, Nicole, Corin"].
        Si no encuentras 3 composiciones claras, usa la cadena "Equipo No Encontrado" para las entradas faltantes.

        **IMPORTANTE:** Si la fuente no proporciona estadísticas finales, rellena el diccionario 'final_stats_targets' con cadenas vacías ("").
        """
        
        instruccion_traduccion = f"""
        INSTRUCCIÓN DE LOCALIZACIÓN (CRÍTICA): Analiza el 'TEXTO A ANALIZAR'. Debes TRADUCIR y localizar todos los nombres de los ítems (sets, armas/conos/engines), estadísticas y nombres de personajes/agentes al IDIOMA **{nombre_idioma}** ({codigo_idioma_objetivo}) en el JSON de salida.
        """
        
        prompt = f"""Eres un agente de recopilación de datos de videojuegos. Tu tarea es analizar el siguiente texto de una página de build del juego {juego} del personaje/agente '{nombre_personaje}' y extraer las recomendaciones.

        {terminos_juego}
        {instruccion_equipo}
        {instruccion_traduccion}

        FORMATO DE SALIDA: Debes responder ÚNICAMENTE con un objeto JSON válido, sin ningún texto adicional, explicaciones o código.

        JSON SCHEMA (Solo proporciona los valores, no las claves estáticas):
        {contenido_json_schema}

        TEXTO A ANALIZAR:
        ---
        {contenido_texto}
        ---
        """
        
        try:
            respuesta = self.cliente.models.generate_content(
                model=self.modelo_completado,
                contents=prompt,
                config={"response_mime_type": "application/json"} 
            )
            texto_salida_llm = respuesta.text.strip()

            if texto_salida_llm.startswith('```json'): 
                texto_salida_llm = texto_salida_llm[7:].strip().rstrip('`')
                
            return json.loads(texto_salida_llm)

        except APIError as e:
            print(f"[{self.nombre}] Error API: {e}")
            return None
        except json.JSONDecodeError:
            print(f"[{self.nombre}] Error Parseo JSON.")
            return None
        except Exception as e:
            print(f"[{self.nombre}] Error Desconocido: {e}")
            return None
