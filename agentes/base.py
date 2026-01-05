from abc import ABC, abstractmethod

class AgenteBase(ABC):
    def __init__(self, nombre):
        self.nombre = nombre

    @abstractmethod
    def procesar_solicitud(self, datos):
        """
        Procesa la solicitud entrante.
        :param datos: Datos de entrada (diccionario u objeto)
        :return: Resultado del procesamiento
        """
        pass

    def recibir_mensaje(self, mensaje):
        """
        Implementación del protocolo A2A.
        Espera un diccionario con claves:
        - cabecera: { de, para, accion }
        - cuerpo: { ... datos ... }
        """
        # Validación basica del protocolo
        if not isinstance(mensaje, dict) or "cabecera" not in mensaje or "cuerpo" not in mensaje:
            return {"estado": "ERROR", "error": "Formato de mensaje inválido (A2A Protocol Violation)"}

        # Enrutar según acción o llamar al procesador por defecto
        # Aqui simplificamos redirigiendo al método existente procesar_solicitud
        try:
            resultado = self.procesar_solicitud(mensaje["cuerpo"])
            return {
                "estado": "OK",
                "cuerpo": resultado,
                "cabecera_respuesta": {
                    "de": self.nombre,
                    "para": mensaje["cabecera"].get("de", "Desconocido")
                }
            }
        except Exception as e:
            return {"estado": "ERROR", "error": str(e)}
