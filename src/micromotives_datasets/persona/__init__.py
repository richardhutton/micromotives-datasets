"""Personas: rendering them, and harmonising them across surveys.

`render` turns a populated `Persona` into the text block that goes into the
prompt. `bands` reconciles attributes that different surveys chopped up
differently, which is what lets rows from several studies sit in one corpus
without describing the same person two incompatible ways.
"""

from .render import render

__all__ = ["render"]
