"""
Publisher Final Delivery App - Prompt Engine
Handles construction of prompts for asset generation using the Drawer of Personas.
"""
import os
import json
import pandas as pd
from typing import Dict, Optional, List
from pathlib import Path

class PromptEngine:
    """Generates prompts for various assets based on metadata and council personas."""

    def __init__(self, root_path: str = None):
        if root_path is None:
            self.voices_path = Path("/Users/damirprice/Library/CloudStorage/GoogleDrive-luminapub67@gmail.com/My Drive/PUBLISHING_ASSETS_MASTER/02_VOICE_GUIDES")
        else:
            self.voices_path = Path(root_path) / "02_VOICE_GUIDES"

        self.personas = self._load_personas()

    def _load_personas(self) -> Dict[str, str]:
        """Loads the Council_Personas.json dynamically."""
        persona_file = self.voices_path / "Council_Personas.json"

        if not persona_file.exists():
            persona_file = Path("02_VOICE_GUIDES/Council_Personas.json")

        if persona_file.exists():
            try:
                with open(persona_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading personas: {e}")
                return self._get_default_personas()
        else:
            print(f"Persona file not found at {persona_file}. Using defaults.")
            return self._get_default_personas()

    def _get_default_personas(self) -> Dict[str, str]:
        """Fallback definitions if Council_Personas.json is missing."""
        return {
            "Music_Supervisor": "Focuses on sync utility and findability. Thinks in terms of real editorial workflows — quote requests, tight deadlines, catalog searches. Asks: does this track description tell an editor what they need to know in five seconds? Is the title searchable? Are the placement tags realistic and specific? Cuts anything that doesn't serve those questions. Enforces the hard boundary between theatrical catalogs (rC, SSC) and commercial catalog (EPP) — never allows placement tags to cross between these worlds.",
            "Lead_Video_Editor": "Focuses on broadcast utility and immediate usability. Thinks in terms of timeline gaps, scene transitions, and what a track actually does moment to moment. Asks: what happens in this track structurally? Where does the energy shift? What kind of cut does this serve? Demands specificity about instrumentation and sonic events. Rejects vague atmospheric language in favor of concrete, actionable description.",
            "Brand_Gatekeeper": "Protects the distinct identity of each catalog. redCola is cinematic and electronic — sound design as musical element, blockbuster scale, theatrical marketing only. Short Story Collective is the same cinematic instinct executed with traditional orchestral instruments — prestige TV, film, arthouse. Ekonomic Propaganda is production​​​​​​​​​​​​​​​​
