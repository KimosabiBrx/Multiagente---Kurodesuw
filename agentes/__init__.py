# Módulo de Agentes Multi-Agente
# Este módulo contiene los agentes especializados para el sistema

from .base import AgenteBase
from .coordinador import AgenteCoordinador
from .investigador import AgenteInvestigador
from .analista import AgenteAnalista
from .imagenes import AgenteImagenes
from .generador_html import AgenteGeneradorHTML

__all__ = ['AgenteBase', 'AgenteCoordinador', 'AgenteInvestigador', 'AgenteAnalista', 'AgenteImagenes', 'AgenteGeneradorHTML']
