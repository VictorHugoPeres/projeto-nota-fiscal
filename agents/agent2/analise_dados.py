"""Módulo de Compatibilidade para Agent2.

Redireciona para `agents.agent2.persistencia_dados`.
"""

from agents.agent2.persistencia_dados import Agent2, normalizar_documento

__all__ = ["Agent2", "normalizar_documento"]
