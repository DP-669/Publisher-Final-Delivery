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
        
        # Fallback to local if running in test environment and not found
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
        """Fallback definitions if file is missing."""
        return {
          "Music_Supervisor": "Focuses on emotion, narrative, no fluff.",
          "Lead_Video_Editor": "Focuses on broadcast utility and transitions.",
          "Brand_Gatekeeper": "Enforces catalog rules: redCola, SSC, EPP, and bans cliches.",
          "Head_of_AR": "Writes the 3-Sentence Track Description Arc.",
          "Art_Director": "Focuses on MidJourney v7 parameters, textures, and lighting.",
          "Copywriter": "Focuses on direct response MailChimp rhythm.",
          "Arbitrator": "Synthesizes divergent ideas into a final output."
        }

    # --- TAB 01 Prompts ---
    def generate_keywords_analysis_prompt(self, catalog: str) -> str:
        """
        Generates the system instruction for audio analysis (Keywords/Ingestion).
        Consults Music Supervisor and Lead Video Editor.
        """
        sup_voice = self.personas.get("Music_Supervisor", "")
        ed_voice = self.personas.get("Lead_Video_Editor", "")
        
        prompt = f"""
        You are acting as a dual-persona council:
        1. Music Supervisor: {sup_voice}
        2. Lead Video Editor: {ed_voice}
        
        Analyze the provided audio track for the {catalog} catalog. Provide a highly detailed, human-like analysis in JSON format.
        
        Required JSON Structure:
        {{
            "Title": "A creative, evocative title for the track",
            "Composer": "", 
            "Keywords": "Exactly 15 to 20 comma-separated keywords (mood, genre, instrumentation, editorial use). Keep all phrases to 3 words maximum.",
            "Description": "A rough initial description of the track's narrative and utility."
        }}
        Note: Leave 'Composer' blank.
        """
        return prompt

    def get_harvest_loop_prompt(self, keyword: str) -> str:
        """Auto-correction loop prompt for long keywords."""
        return f"Rephrase the keyword '{keyword}' so it is exactly 1, 2, or 3 words maximum. Preserve the original semantic meaning perfectly. Return ONLY the new keyword, no other text."


    # --- TAB 02 Prompts ---
    def generate_track_description_prompt(self, title: str, start_description: str, catalog: str) -> tuple[str, str]:
        """
        Generates prompt for the 3-Sentence Arc (Head of A&R + audits by Lead Editor/Gatekeeper).
        Returns: (system_instruction, task_prompt)
        """
        ar_voice = self.personas.get("Head_of_AR", "")
        ed_voice = self.personas.get("Lead_Video_Editor", "")
        gate_voice = self.personas.get("Brand_Gatekeeper", "")
        
        system_instruction = f"""
        You are the Head of A&R ({ar_voice}).
        Your output is being audited by the Lead Video Editor ({ed_voice}) and the Brand Gatekeeper ({gate_voice}).
        Catalog Context: {catalog}.
        
        STRICT RULES:
        1. You must write EXACTLY 3 sentences.
        2. Sentence 1: Hook/Ingestion (Must describe immediate feel/instrumentation).
        3. Sentence 2: Development (How the track builds or shifts).
        4. Sentence 3: Utility/Resolution (How it should be used in editing/sync).
        5. ANTIGRAVITY PROTOCOL: The very first word of the first sentence CANNOT be an article ("A", "An", "The"). Start immediately with an adjective or noun.
        """
        
        task_prompt = f"""
        Refine the following rough description for the track '{title}' into the 3-Sentence Arc.
        
        Rough Description:
        {start_description}
        """
        return system_instruction, task_prompt

    # --- TAB 03 Prompts ---
    def generate_album_description_prompt(self, all_track_descriptions: List[str], catalog: str) -> tuple[str, str]:
        """
        Arbitrator synthesizes Tabs 01 and 02 into exactly ONE powerful, punchy sentence.
        """
        arb_voice = self.personas.get("Arbitrator", "")
        
        system_instruction = f"""
        You are the Arbitrator ({arb_voice}).
        Based on the provided track descriptions for the new '{catalog}' album, synthesize everything into EXACTLY ONE powerful, punchy sentence that summarizes the entire album's vibe and utility. Do not write more than one sentence.
        """
        
        descriptions_text = "\n".join([f"- {desc}" for desc in all_track_descriptions])
        task_prompt = f"Track Descriptions:\n{descriptions_text}"
        
        return system_instruction, task_prompt

    # --- TAB 04 Prompts ---
    def generate_album_name_prompt(self, album_description: str, catalog: str) -> tuple[str, str]:
        """
        Verbose Sampling. 5 highly original concepts.
        """
        gate_voice = self.personas.get("Brand_Gatekeeper", "")
        arb_voice = self.personas.get("Arbitrator", "")
        
        system_instruction = f"""
        You are working as the Arbitrator ({arb_voice}) and the Brand Gatekeeper ({gate_voice}).
        Catalog: {catalog}.
        
        Task: Brainstorm exactly 5 highly original, non-linear concept titles for this album.
        Rule: Ban all library music cliches (e.g., "Cinematic Journeys", "Epic Battles", "Emotional Piano"). Think Different.
        Format your response as a numbered list of exactly 5 titles.
        """
        
        task_prompt = f"Album Description (Vibe): {album_description}"
        return system_instruction, task_prompt

    # --- TAB 05 Prompts ---
    def generate_cover_art_prompt(self, album_name: str, album_description: str, catalog: str, ref_urls: List[str]) -> tuple[str, str]:
        """
        Art Director generates 4 MidJourney v7 prompts.
        """
        art_voice = self.personas.get("Art_Director", "")
        gate_voice = self.personas.get("Brand_Gatekeeper", "")
        
        system_instruction = f"""
        You are the Art Director ({art_voice}) constrained by the Brand Gatekeeper ({gate_voice}).
        Catalog: {catalog}
        
        Task: Write exactly 4 MidJourney v7 prompts for this album's cover art.
        Use abstract, emotional metaphors and detailed camera/lighting terminology. Provide ONLY the 4 prompts as text separated by double newlines. Do not add conversational intro text.
        
        STRICT RULE: Every prompt must end exactly with: --v 7.0 --ar 1:1 --sref [URL]
        Substitute [URL] with one of the provided reference URLs sequentially.
        """
        
        url_text = "\n".join([f"URL {i+1}: {u}" for i, u in enumerate(ref_urls)])
        
        task_prompt = f"""
        Album Name: {album_name}
        Album Description: {album_description}
        
        Available Reference URLs to append:
        {url_text}
        """
        return system_instruction, task_prompt
        
    # --- TAB 06 Prompts ---
    def generate_mailchimp_intro_prompt(self, album_name: str, album_description: str, catalog: str) -> tuple[str, str]:
         """
         Copywriter, Supervisor, Gatekeeper debate -> Arbitrator 3-4 sentence memo.
         """
         cw_voice = self.personas.get("Copywriter", "")
         sup_voice = self.personas.get("Music_Supervisor", "")
         gate_voice = self.personas.get("Brand_Gatekeeper", "")
         arb_voice = self.personas.get("Arbitrator", "")
         
         system_instruction = f"""
         You are a council: Copywriter ({cw_voice}), Supervisor ({sup_voice}), and Gatekeeper ({gate_voice}).
         The Arbitrator ({arb_voice}) will synthesize your ideas.
         
         Task: Write a final 3-to-4 sentence promotional intro for MailChimp about the new {catalog} album.
         Rule: It must read like a professional studio memo to music supervisors, NOT a cheap sales pitch. Respect the intelligence of the reader.
         """
         
         task_prompt = f"""
         Album Name: {album_name}
         Album Description: {album_description}
         """
         return system_instruction, task_prompt
