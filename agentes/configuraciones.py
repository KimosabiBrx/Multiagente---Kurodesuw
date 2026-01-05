# Constantes de Fuentes
FUENTE_PRYDWEN = "Prydwen"
FUENTE_GAME8 = "Game8"
FUENTE_HONKAILAB = "HonkaiLab"
FUENTE_GENSHINLAB = "GenshinLab"
FUENTE_GENSHINBUILD = "GenshinBuilds"
FUENTE_GAMEWITH = "GameWithJP"

# Configuraciones de Juegos

CONFIG_HSR = {
    "juego": "HSR",
    "url_base_primaria": "https://www.prydwen.gg/star-rail/characters",
    "segmento_ruta_primaria": "/star-rail/characters/",
    "url_base_secundaria": "https://game8.co/games/Honkai-Star-Rail",
    "segmento_ruta_secundaria": "/Honkai-Star-Rail-",
    "url_base_terciaria": "https://honkailab.com/honkai-star-rail-characters/",
    "segmento_ruta_terciaria": "/honkai-star-rail-characters/",
    
    "ruta_archivo": 'hsr_builds.json',
    "tamano_equipo": 4, 
    "esquema_build": {
        "character_name": "", # Mantenemos keys en inglés si el JSON lo requiere, o cambiamos todo. Por compatibilidad con app.py original, mantendré keys de schema.
        "game": "HSR",
        "source": "", 
        "build_name": "Mejor Build General (Analizada por Gemini)",
        "weapon_recommendations": [],
        "artifact_set_recommendations": [], 
        "planetary_set_recommendations": [],
        "main_stats_recommendations": {
            "body": "Cuerpo", 
            "feet": "Pies", 
            "planar_sphere": "Esfera", 
            "link_rope": "Cuerda"
        },
        "final_stats_targets": {
            "HP": "", "DEF": "", "ATK": "", "CRIT Rate": "", "CRIT DMG": "", 
            "SPD": "", "Energy Regen Rate": "", "Effect RES": "", 
            "Effect HIT Rate": "", "Break Effect": ""
        },
        "team_recommendations": [] 
    }
}

CONFIG_ZZZ = {
    "juego": "ZZZ",
    "url_base_primaria": "https://www.prydwen.gg/zenless/characters",
    "segmento_ruta_primaria": "/zenless/agents/", 
    "url_base_secundaria": "https://game8.co/games/Zenless-Zone-Zero", 
    "segmento_ruta_secundaria": "/Zenless-Zone-Zero-", 
    "url_base_terciaria": "https://genshinlab.com/zenless-zone-zerozzz-characters/",
    "segmento_ruta_terciaria": "/zenless-zone-zerozzz-characters/",
    
    "ruta_archivo": 'zzz_builds.json',
    "tamano_equipo": 3, 
    "esquema_build": {
        "character_name": "",
        "game": "ZZZ",
        "source": "",
        "build_name": "Mejor Build General (Analizada por Gemini)",
        "weapon_recommendations": [],
        "artifact_set_recommendations": [],
        "main_stats_recommendations": {
            "head_drive": "Head Drive", 
            "hand_drive": "Hand Drive", 
            "feet_drive": "Feet Drive", 
            "core_drive": "Core Drive"
        },
        "final_stats_targets": {
            "HP": "", "DEF": "", "ATK": "", "CRIT Rate": "", "CRIT DMG": "",
            "Energy_Charge": "", "Impact_Rating": "", "Attribute_DMG": "",
            "Anomaly_Proficiency": ""
        },
        "team_recommendations": [] 
    }
}

CONFIG_GI = {
    "juego": "GI",
    "url_base_primaria": "https://genshin-builds.com/es/characters",
    "segmento_ruta_primaria": "/es/characters/",
    "url_base_secundaria": "https://gamewith.jp/genshin/article/show/230360",
    "segmento_ruta_secundaria": "https://gamewith.jp/genshin/article/show/",
    "mapa_id_gamewith": { 
        "furina": "407254",
        "navia": "426179", 
        "neuvillette": "399451"
    },
    
    "ruta_archivo": 'gi_builds.json',
    "tamano_equipo": 4, 
    "esquema_build": {
        "character_name": "",
        "game": "GI",
        "source": "", 
        "build_name": "Mejor Build General (Analizada por Gemini)",
        "weapon_recommendations": [],
        "artifact_set_recommendations": [], 
        "main_stats_recommendations": {
            "sands": "Arena del Tiempo", 
            "goblet": "Cáliz de Eonotemo", 
            "circlet": "Tiara de Logos"
        },
        "final_stats_targets": {
            "Vida": "", "ATK": "", "DEF": "", 
            "Probabilidad Critica": "", "Daño Critico": "", 
            "Maestria Elemental": "", "Recarga de Energía": ""
        },
        "team_recommendations": []
    }
}
