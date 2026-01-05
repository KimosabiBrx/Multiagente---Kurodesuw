import os
from datetime import datetime
from .base import AgenteBase

class AgenteGeneradorHTML(AgenteBase):
    def __init__(self, nombre="Generador HTML"):
        super().__init__(nombre)
        self.directorio_salida = "builds"
        
        # Crear directorio si no existe
        if not os.path.exists(self.directorio_salida):
            os.makedirs(self.directorio_salida)
            print(f"[{self.nombre}] Directorio '{self.directorio_salida}/' creado")

    def procesar_solicitud(self, datos):
        """
        Espera que datos contenga:
        - build_data: dict (datos de la build)
        - imagenes: list (URLs de imágenes)
        - nombre_personaje: str
        - juego: str
        """
        build_data = datos.get("build_data", {})
        imagenes = datos.get("imagenes", [])
        nombre_personaje = datos.get("nombre_personaje", "Personaje")
        juego = datos.get("juego", "Juego")
        
        print(f"[{self.nombre}] Generando HTML para {nombre_personaje} ({juego})")
        
        # Generar HTML
        html_content = self._generar_html(build_data, imagenes, nombre_personaje, juego)
        
        # Guardar archivo
        nombre_archivo = f"{nombre_personaje.lower().replace(' ', '_')}_{juego.lower()}.html"
        ruta_completa = os.path.join(self.directorio_salida, nombre_archivo)
        
        with open(ruta_completa, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[{self.nombre}] ✓ HTML generado: {ruta_completa}")
        
        return {
            "exito": True,
            "ruta_archivo": ruta_completa,
            "nombre_archivo": nombre_archivo
        }

    def _generar_html(self, build_data, imagenes, nombre_personaje, juego):
        """Genera el contenido HTML completo"""
        
        # Mapeo de nombres de juegos
        nombres_juegos = {
            "HSR": "Honkai: Star Rail",
            "ZZZ": "Zenless Zone Zero",
            "GI": "Genshin Impact"
        }
        nombre_juego_completo = nombres_juegos.get(juego, juego)
        
        # Fecha de generación
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Generar secciones
        seccion_imagenes = self._generar_galeria(imagenes, nombre_personaje)
        seccion_armas = self._generar_seccion_lista("Armas Recomendadas", build_data.get("weapon_recommendations", []))
        seccion_artefactos = self._generar_seccion_lista("Sets de Artefactos", build_data.get("artifact_set_recommendations", []))
        
        # Sección específica para HSR/ZZZ
        seccion_planetarios = ""
        if juego in ["HSR", "ZZZ"]:
            seccion_planetarios = self._generar_seccion_lista(
                "Ornamentos Planetarios" if juego == "HSR" else "Sets Secundarios",
                build_data.get("planetary_set_recommendations", [])
            )
        
        seccion_stats = self._generar_seccion_stats(build_data.get("main_stats_recommendations", {}))
        seccion_stats_finales = self._generar_seccion_stats_finales(build_data.get("final_stats_targets", {}))
        seccion_equipos = self._generar_seccion_lista("Composiciones de Equipo", build_data.get("team_recommendations", []))
        
        # Análisis de Gemini
        analisis = build_data.get("Analisis_Gemini", "")
        fuente = build_data.get("source", "Desconocida")
        
        # Template HTML
        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Build: {nombre_personaje} - {nombre_juego_completo}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header .game {{
            font-size: 1.2em;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .header .meta {{
            margin-top: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .gallery img {{
            width: 100%;
            height: 300px;
            object-fit: cover;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .gallery img:hover {{
            transform: scale(1.05);
        }}
        
        .section {{
            margin-bottom: 40px;
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            border-left: 5px solid #667eea;
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .list-item {{
            background: white;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 3px solid #764ba2;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card .label {{
            color: #667eea;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 0.9em;
        }}
        
        .stat-card .value {{
            color: #333;
            font-size: 1.1em;
        }}
        
        .analysis {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #ffc107;
            margin-top: 30px;
        }}
        
        .analysis h3 {{
            color: #856404;
            margin-bottom: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2em;
            }}
            
            .content {{
                padding: 20px;
            }}
            
            .gallery {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{nombre_personaje}</h1>
            <div class="game">{nombre_juego_completo}</div>
            <div class="meta">
                Fuente: {fuente} | Generado: {fecha}
            </div>
        </div>
        
        <div class="content">
            {seccion_imagenes}
            {seccion_armas}
            {seccion_artefactos}
            {seccion_planetarios}
            {seccion_stats}
            {seccion_stats_finales}
            {seccion_equipos}
            
            {f'<div class="analysis"><h3>📊 Análisis</h3><p>{analisis}</p></div>' if analisis else ''}
        </div>
        
        <div class="footer">
            Generado automáticamente por el Sistema Multi-Agente
        </div>
    </div>
</body>
</html>"""
        
        return html

    def _generar_galeria(self, imagenes, nombre_personaje):
        """Genera la galería de imágenes"""
        if not imagenes:
            return ""
        
        imgs_html = "\n".join([
            f'<img src="{img}" alt="{nombre_personaje}" onerror="this.style.display=\'none\'">'
            for img in imagenes[:6]  # Máximo 6 imágenes
        ])
        
        return f"""
        <div class="gallery">
            {imgs_html}
        </div>
        """

    def _generar_seccion_lista(self, titulo, items):
        """Genera una sección con lista de items"""
        if not items:
            return ""
        
        items_html = "\n".join([
            f'<div class="list-item">{item}</div>'
            for item in items if item
        ])
        
        return f"""
        <div class="section">
            <h2>{titulo}</h2>
            {items_html}
        </div>
        """

    def _generar_seccion_stats(self, stats):
        """Genera sección de stats principales"""
        if not stats or not any(stats.values()):
            return ""
        
        stats_html = "\n".join([
            f'<div class="stat-card"><div class="label">{key}</div><div class="value">{value}</div></div>'
            for key, value in stats.items() if value
        ])
        
        return f"""
        <div class="section">
            <h2>Stats Principales Recomendadas</h2>
            <div class="stats-grid">
                {stats_html}
            </div>
        </div>
        """

    def _generar_seccion_stats_finales(self, stats):
        """Genera sección de stats objetivo finales"""
        if not stats or not any(stats.values()):
            return ""
        
        stats_html = "\n".join([
            f'<div class="stat-card"><div class="label">{key}</div><div class="value">{value}</div></div>'
            for key, value in stats.items() if value
        ])
        
        return f"""
        <div class="section">
            <h2>Stats Objetivo (Finales)</h2>
            <div class="stats-grid">
                {stats_html}
            </div>
        </div>
        """
