import json
import os
import re
from flask import Flask, render_template, request, jsonify
from agentes.coordinador import AgenteCoordinador
from agentes.imagenes import AgenteImagenes
from agentes.generador_html import AgenteGeneradorHTML

app = Flask(__name__)
coordinador = AgenteCoordinador()
agente_imagenes = AgenteImagenes()
agente_html = AgenteGeneradorHTML()

# Main Flask Routes


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Maneja los mensajes del chat y el estado de la conversación."""
    data = request.json
    user_input = data.get('message', '').strip()
    state = data.get('state', {'step': 'initial'})
    json_response = {}

    if state['step'] == 'initial':
        game, target_character, requested_keys = coordinador.analizar_consulta(user_input)
        if not target_character:
            json_response = {'response': "No pude identificar el nombre del personaje. Por favor, sé más específico (ej: 'Build para Acheron HSR').", 'state': {'step': 'initial'}}
        else:
            state.update({'step': 'waiting_source', 'game': game, 'target_character': target_character, 'requested_keys': requested_keys})
            if game == "HSR": prompt_sources = "1: Prydwen, 2: HonkaiLab"
            elif game == "ZZZ": prompt_sources = "1: Prydwen, 2: GenshinLab"
            else: prompt_sources = "1: GenshinBuilds (ES), 2: GameWith (JP)"
            response_text = f"¡Entendido! Buscando a <strong>{target_character.title()}</strong>. ¿Fuente preferida?<br>({prompt_sources})"
            json_response = {'response': response_text, 'state': state}

    elif state['step'] == 'waiting_source':
        state['source_choice'] = user_input if user_input in ['1', '2'] else ''
        state['step'] = 'waiting_language'
        response_text = "Perfecto. ¿Que idioma desea los resultados? (ej: 'es', 'en', 'jp', 'cn', 'fr', 'cr'). Deja en blanco para 'es'."
        json_response = {'response': response_text, 'state': state}

    elif state['step'] == 'waiting_language':
        state['target_language'] = user_input if user_input else 'es'
#genera la build
        result, error = coordinador.procesar_solicitud(
            state['game'], state['target_character'], state['requested_keys'],
            state.get('source_choice', ''), state.get('target_language', 'es')
        )

        images_list = []
        try:
            game_names = {
                "HSR": "Honkai Star Rail",
                "ZZZ": "Zenless Zone Zero", 
                "GI": "Genshin Impact"
            }
            game_full = game_names.get(state['game'], state['game'])
            etiqueta_busqueda = f"{state['target_character']} {game_full} hoyoverse"
            
            # Protocolo A2A para AgenteImagenes
            msg_img = {
                "cabecera": {"de": "OrquestadorFlask", "para": "AgenteImagenes", "accion": "BUSCAR_IMAGENES"},
                "cuerpo": {
                    "etiqueta": etiqueta_busqueda,
                    "max_imagenes": 6
                }
            }
            resp_img = agente_imagenes.recibir_mensaje(msg_img)
            
            if resp_img.get("estado") == "OK":
                resultado_imagenes = resp_img["cuerpo"]
                if resultado_imagenes["exito"]:
                    images_list = resultado_imagenes["imagenes"]
            else:
                print(f"Error A2A Imagenes: {resp_img.get('error')}")

        except Exception as e:
            print(f"Error buscando imágenes: {e}")

#esta parte ahce el response final
        if result:
            # Generar página HTML con la build
            try:
                # Protocolo A2A para AgenteGeneradorHTML
                msg_html = {
                    "cabecera": {"de": "OrquestadorFlask", "para": "AgenteGeneradorHTML", "accion": "GENERAR_HTML"},
                    "cuerpo": {
                        "build_data": result,
                        "imagenes": images_list,
                        "nombre_personaje": state['target_character'],
                        "juego": state['game']
                    }
                }
                resp_html = agente_html.recibir_mensaje(msg_html)
                
                if resp_html.get("estado") == "OK":
                    resultado_html = resp_html["cuerpo"]
                    if resultado_html["exito"]:
                        print(f"✓ Página HTML generada: {resultado_html['ruta_archivo']}")
                else:
                    print(f"Error A2A HTML: {resp_html.get('error')}")

            except Exception as e:
                print(f"Error generando HTML: {e}")
            
            response_text = f"¡Aquí tienes la build para <strong>{state['target_character'].title()}</strong>!<br>¿Necesitas otra build?"
            json_response = {
                'response': response_text,
                'data': result,
                'images': images_list,  
                'game': state.get('game'),
                'state': {'step': 'initial'}
            }
        else:
            response_text = f"Lo siento, hubo un error: {error}.<br>¿Quieres intentar con otro personaje?"
            json_response = {'response': response_text, 'data': None, 'game': state.get('game'), 'state': {'step': 'initial'}}

    else:
        json_response = {'response': "Ha ocurrido un error de estado. Reiniciando.", 'state': {'step': 'initial'}}

    return jsonify(json_response)

if __name__ == "__main__":
    app.run(debug=True)