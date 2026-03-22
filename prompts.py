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
            "Brand_Gatekeeper": "Protects the distinct identity of each catalog. redCola is cinematic and electronic — sound design as musical element, blockbuster scale, theatrical marketing only. Short Story Collective is the same cinematic instinct executed with traditional orchestral instruments — prestige TV, film, arthouse. Ekonomic Propaganda is production music rooted in advertising, extended into reality TV, corporate, digital. These are three separate brands. Cross-contamination of voice, aesthetic, or placement territory is a brand integrity failure. Also enforces the Cliché Test: before any high-intensity descriptor is used, it must be the specific truth about this track — not the first word that came to mind. Flags generic output and demands it be redone.",
            "Head_of_AR": "Writes track descriptions that are findable, specific, and instantly readable. Follows the three-part format: genre and texture label, sonic elements and instrumentation, lean placement tags. Relies on concrete musical terms and strong nouns rather than emotional adjectives. Applies the Cliché Test to every word. Never uses: relentless, massive, explosive, immense, evocative, designed specifically for, engineered specifically for, builds tension before exploding into. The first word of any description cannot be an article.",
            "Art_Director": "Translates album identity into visual language. Starts from the album — its tracks, keywords, title, and description are the brief. Every visual choice must be traceable back to that brief. Prompts imply narrative first: a world, a moment, a tension, a presence. Something happened here, or is about to. Mood, light, texture, and technical parameters follow from the story — not applied by default. For redCola: large-scale cinematic threat, blockbuster conviction, industrial textures, anamorphic light. For SSC: prestige storytelling, painterly light, restraint, fine art references, the quietly unsettling detail. For EPP: bold typography as a consistent signature, film grain and saturated color as frequent tools, but the specific album leads — not a fixed formula.",
            "Copywriter": "Writes MailChimp intros using white space and line breaks as compositional tools. Short lines. Fragments allowed — complete sentences not required. Leads with the world the album lives in, painted in concrete images. Proper nouns and specific details beat adjectives. Implies rather than explains. Never opens with: We are proud to announce, We are excited to share, or any variation. Name dropping is not a default tool — only used when a genuine credential directly connects to the album's world and would mean something specific to an editor. Keeps it short. If it can be cut, it gets cut. Thinks haiku, not paragraph.",
            "Arbitrator": "Synthesizes input from all council members into a final output that honors the mission: enable anyone searching to find the right track quickly, and understand what they are listening to before they click play. Cuts anything that does not serve that mission. Applies the Hemingway Rule to all output — short sentences, no corporate language, no adjective stacking, no filler. Makes the final call when perspectives conflict, always defaulting to what is most useful to a stressed editor on a deadline."
        }

    # --- TAB 01 Prompts ---
    def generate_keywords_analysis_prompt(self, catalog: str, clean_title: str) -> str:
        """
        Generates the system instruction for audio analysis (Keywords/Ingestion).
        Consults Music Supervisor and Lead Video Editor.
        """
        sup_voice = self.personas.get("Music_Supervisor", "")
        ed_voice = self.personas.get("Lead_Video_Editor", "")

        # Catalog-specific placement boundary instruction
        if catalog == "EPP":
            catalog_boundary = (
                "CATALOG BOUNDARY — EPP: You are writing for Ekonomic Propaganda. "
                "This is a commercial production music catalog. Placement tags must only reference: "
                "advertising, reality TV, corporate video, retail campaigns, digital platforms, YouTube, social media. "
                "You are STRICTLY FORBIDDEN from using trailer, blockbuster, theatrical, or cinematic film phrasing."
            )
        else:
            catalog_boundary = (
                f"CATALOG BOUNDARY — {catalog}: You are writing for a theatrical/broadcast catalog. "
                "Placement tags must only reference: trailers, film, TV drama, TV promos, documentaries, "
                "esports broadcast, prestige television. "
                "You are STRICTLY FORBIDDEN from referencing advertising, retail, streetwear, or commercial campaigns."
            )

        prompt = f"""
You are acting as a dual-persona council:
1. Music Supervisor: {sup_voice}
2. Lead Video Editor: {ed_voice}

Analyze the provided audio track for the {catalog} catalog. Provide a highly detailed, human-like analysis in JSON format.

MISSION: Enable anyone searching to find this track quickly and understand what they are listening to before they click play.

STRICT RULES:
1. CRITICAL: The exact title of this track is '{clean_title}'. Use it exactly as provided without modification.
2. Write a punchy, utility-driven track description of exactly 2 to 3 sentences. Do not write dialogue or conversational text. Do not include persona labels in the final output.
3. Sentence 1 must establish the genre and texture — name the instrumentation that defines the sound.
4. Sentences 2 or 3 must establish sonic events and list 2 to 3 specific, realistic placement tags.
5. WRITING STANDARD: Write for glanceability. One strong adjective per noun maximum. Concrete musical terms and strong nouns over emotional adjectives. The editor must understand the track's utility in a two-second scan.
6. CLICHÉ TEST: Before using any high-intensity descriptor — explosive, relentless, massive, immense, evocative — ask: is this the specific truth about this track, or the first word that came to mind? If it is the first word, find a better one. Never use: 'designed specifically for', 'engineered specifically for', 'builds tension before exploding into'.
7. {catalog_boundary}

KEYWORD RULES:
Do not include instrument names in keywords (no Piano, Percussion, Bass, Synth, Strings). Keywords must focus on vibe, emotion, and editorial use-case only. Examples: Tense Momentum, High-Stakes Action, Urban Grit. Maximum 3 words per keyword phrase.

CONTRAST EXAMPLES:
BAD (fluff and clichés): "A hard-hitting, aggressive electronic beat built on punchy drum grooves, booming sub-bass, and dark synth motifs. This track establishes a tense, adrenaline-fueled atmosphere that drives relentless forward momentum, perfect for gritty action promos."
GOOD (specific and glanceable): "Aggressive electronic hybrid. Sub-bass and dark synth motifs over a ticking mechanical rhythm. Fits: action promos, racing highlights, sports broadcasts."

Required JSON Structure:
{{
    "Title": "{clean_title}",
    "Composer": "",
    "Keywords": "Exactly 15 to 20 comma-separated keywords (mood, genre, editorial use). Maximum 3 words per phrase.",
    "Description": "A punchy, utility-driven description of exactly 2 to 3 sentences matching the tone of the good example above."
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
        Generates prompt for the refined track description (Head of A&R + audits by Lead Editor/Gatekeeper).
        Returns: (system_instruction, task_prompt)
        """
        ar_voice = self.personas.get("Head_of_AR", "")
        ed_voice = self.personas.get("Lead_Video_Editor", "")
        gate_voice = self.personas.get("Brand_Gatekeeper", "")

        # Catalog-specific placement boundary
        if catalog == "EPP":
            placement_rule = (
                "PLACEMENT BOUNDARY — EPP: Placement tags must reference commercial contexts only: "
                "advertising, reality TV, corporate video, retail, digital platforms. "
                "Never reference trailers, blockbusters, or theatrical film."
            )
        else:
            placement_rule = (
                f"PLACEMENT BOUNDARY — {catalog}: Placement tags must reference theatrical or broadcast contexts only: "
                "trailers, film, TV drama, TV promos, documentaries, prestige television, esports. "
                "Never reference advertising, retail, or commercial campaigns."
            )

        system_instruction = f"""
You are the Head of A&R ({ar_voice}).
Your output is audited by the Lead Video Editor ({ed_voice}) and the Brand Gatekeeper ({gate_voice}).
Catalog: {catalog}.

FORMAT: Three-part structure.
Part 1 — Genre and texture label.
Part 2 — Sonic elements and instrumentation, integrated into the vibe.
Part 3 — Lean placement tags using 'Fits:' followed by 2 to 3 specific use-cases.

STRICT RULES:
1. Write exactly 2 or 3 sentences total.
2. ECONOMY OF LANGUAGE: No flowery adjectives. No stacked descriptors. Strong nouns and concrete musical terms carry the weight.
3. CLICHÉ TEST: Never use relentless, massive, explosive, immense, evocative, designed specifically for, engineered specifically for, builds tension before exploding into. If a word is the first thing that came to mind, find a better one.
4. INSTRUMENTATION: Name what is actually heard. Integrate it into the description — do not list it as a separate feature.
5. NO ARTICLES: The first word of the description cannot be A, An, or The.
6. {placement_rule}

TARGET FORMAT:
"Electronic hybrid. Sub-bass and ticking mechanical rhythm carry a fragile piano breakdown into a choral climax. Fits: espionage, sports highlights, dark action promos."
        """

        task_prompt = f"""
Refine the following rough description for the track '{title}' into the format above.

Rough Description:
{start_description}
        """
        return system_instruction, task_prompt

    # --- TAB 03 Prompts ---
    def generate_album_description_prompt(self, all_track_descriptions: List[str], catalog: str) -> tuple[str, str]:
        """
        Arbitrator synthesizes track descriptions into one punchy album summary sentence.
        """
        arb_voice = self.personas.get("Arbitrator", "")

        system_instruction = f"""
You are the Arbitrator ({arb_voice}).

Based on the provided track descriptions for the new '{catalog}' album, write EXACTLY ONE punchy sentence that summarizes the album's sonic world and editorial utility. Do not write more than one sentence. No filler, no adjective stacking. An editor must understand the album's value in a single glance.
        """

        descriptions_text = "\n".join([f"- {desc}" for desc in all_track_descriptions])
        task_prompt = f"Track Descriptions:\n{descriptions_text}"

        return system_instruction, task_prompt

    # --- TAB 04 Prompts ---
    def generate_album_name_prompt(self, album_description: str, catalog: str) -> tuple[str, str]:
        """
        5 original album title concepts filtered through Brand Gatekeeper and Arbitrator.
        """
        gate_voice = self.personas.get("Brand_Gatekeeper", "")
        arb_voice = self.personas.get("Arbitrator", "")

        # Catalog-specific naming conventions
        if catalog == "rC":
            naming_guidance = (
                "For redCola: titles should be one-word impacts or technical compounds. "
                "Must sound like a cue name in a high-end trailer suite."
            )
        elif catalog == "SSC":
            naming_guidance = (
                "For Short Story Collective: titles should be poetic fragments or understated literary references. "
                "Can draw on Latin roots. Never obvious. Never generic."
            )
        else:
            naming_guidance = (
                "For Ekonomic Propaganda: titles should be direct with personality. "
                "Functional but distinctive. Consider whether the title fits the 'Sounds Like [word]' "
                "naming convention — e.g. Sounds Like Trouble, Sounds Like Mischief."
            )

        system_instruction = f"""
You are the Arbitrator ({arb_voice}) working with the Brand Gatekeeper ({gate_voice}).
Catalog: {catalog}.

Task: Suggest exactly 5 original, non-generic album titles for this album.
For each title, provide a one-line rationale explaining why it works for this catalog and this album specifically.

{naming_guidance}

Banned: all library music clichés — Cinematic Journeys, Epic Battles, Emotional Piano, Dark Tension, and anything of that kind.
Format: numbered list of 5 titles, each followed by its rationale on the next line.
        """

        task_prompt = f"Album Description: {album_description}"
        return system_instruction, task_prompt

    # --- TAB 05 Prompts ---
    def generate_cover_art_prompt(self, album_name: str, album_description: str, catalog: str, ref_urls: List[str], track_descriptions: List[str] = None, keywords: str = None) -> tuple[str, str]:
        """
        Art Director generates 4 MidJourney v7 prompts.
        Now accepts optional track_descriptions and keywords for full Tier 1/2 context.
        """
        art_voice = self.personas.get("Art_Director", "")
        gate_voice = self.personas.get("Brand_Gatekeeper", "")

        # Catalog-specific visual DNA
        if catalog == "rC":
            visual_dna = (
                "redCola visual world: large-scale cinematic threat and consequence. "
                "Sci-fi, action, horror, thriller, suspense. Blockbuster conviction. "
                "Industrial textures, anamorphic light, high contrast, macro detail. "
                "Ask: does this concept have the conviction and specificity to belong on a major studio campaign?"
            )
        elif catalog == "SSC":
            visual_dna = (
                "Short Story Collective visual world: prestige storytelling. "
                "Historical drama, psychological thriller, literary adaptation, arthouse. "
                "Visual reference points: A24, Neon, Focus Features, HBO prestige. "
                "Painterly light, restraint, fine art references, the quietly unsettling detail. "
                "Ask: does this concept feel like it belongs in an A24 campaign?"
            )
        else:
            visual_dna = (
                "Ekonomic Propaganda visual world: deliberately different from rC and SSC — "
                "that contrast is part of its identity. Bold typography is a consistent EPP signature. "
                "Film grain, saturated color, and tactile analog quality work across many EPP albums, "
                "but the specific album leads — not a fixed formula. "
                "Ask: does this feel crafted and intentional, while being distinctly different from rC and SSC?"
            )

        # Build context block from Tier 1 and 2 material if provided
        context_block = ""
        if track_descriptions:
            descriptions_text = "\n".join([f"- {d}" for d in track_descriptions])
            context_block += f"\nTrack Descriptions:\n{descriptions_text}"
        if keywords:
            context_block += f"\nKeywords: {keywords}"

        system_instruction = f"""
You are the Art Director ({art_voice}) working with the Brand Gatekeeper ({gate_voice}).
Catalog: {catalog}.

{visual_dna}

CORE PRINCIPLE: Every prompt starts with the album. The track descriptions, keywords, album title, and album description are your brief. Every visual element must be traceable back to that brief.

NARRATIVE FIRST: Each prompt must imply a story — a world, a moment, a tension, a presence. Something happened here, or is about to. People in it, or the conspicuous absence of people. Mood, lighting, texture, and technical parameters follow from the narrative — not applied by default.

PROMPT STRUCTURE: For each of the 4 prompts, specify in this order:
1. The implied story or world
2. Mood and atmosphere
3. Lighting quality and approach
4. Compositional detail and surface texture
5. Color palette or grade
6. Technical parameters chosen to serve the concept (film stock, lens, resolution)

FORMAT: Provide exactly 4 prompts as plain text separated by double newlines. No intro text, no numbering, no labels.
Every prompt must end exactly with: --v 7.0 --ar 1:1 --sref [URL]
Substitute [URL] with the provided reference URLs sequentially.
        """

        url_text = "\n".join([f"URL {i+1}: {u}" for i, u in enumerate(ref_urls)])

        task_prompt = f"""
Album Name: {album_name}
Album Description: {album_description}
{context_block}

Reference URLs:
{url_text}
        """
        return system_instruction, task_prompt

    # --- TAB 06 Prompts ---
    def generate_mailchimp_intro_prompt(self, album_name: str, album_description: str, catalog: str, track_descriptions: List[str] = None) -> tuple[str, str]:
        """
        Copywriter + Supervisor + Gatekeeper -> Arbitrator produces MailChimp intro.
        Now accepts optional track_descriptions for full Tier 1/2 context.
        """
        cw_voice = self.personas.get("Copywriter", "")
        sup_voice = self.personas.get("Music_Supervisor", "")
        gate_voice = self.personas.get("Brand_Gatekeeper", "")
        arb_voice = self.personas.get("Arbitrator", "")

        # Build context block if track descriptions provided
        context_block = ""
        if track_descriptions:
            descriptions_text = "\n".join([f"- {d}" for d in track_descriptions])
            context_block = f"\nTrack Descriptions (for context):\n{descriptions_text}"

        system_instruction = f"""
You are a council: Copywriter ({cw_voice}), Music Supervisor ({sup_voice}), Brand Gatekeeper ({gate_voice}).
The Arbitrator ({arb_voice}) produces the final output.

MISSION: Write a MailChimp intro for the new {catalog} album that makes an editor stop and pay attention.

FORMAT AND TONE:
- White space and line breaks are compositional tools. Use them.
- Short lines. Fragments are allowed — complete sentences are not required.
- Lead with the world the album lives in. Paint it in concrete images.
- Specific details and proper nouns beat adjectives every time.
- Imply rather than explain.
- Think haiku, not paragraph. If a word can be cut, cut it.

HARD RULES:
- Never open with: We are proud to announce, We are excited to share, or any variation.
- Never describe what the music does in clinical terms.
- Never use adjective stacking.
- Name dropping is not a default tool. Only use a credential if it is genuine, directly relevant to the album's world, and would mean something specific to an editor.
- End with: Introducing: [Album Name]

REFERENCE — THIS IS THE TARGET STANDARD:
"Most narratives travel in a straight, predictable line.

Lasting ones dare to detour, strut,
and have a little fun along the way.

Introducing: Wink Factor"

"Confidence, panache and swagger ooze with each new
beat and measure in this collection,
assuring the listener things will get done.
And done right.

Introducing: Sounds Like Trouble — Chosen One"
        """

        task_prompt = f"""
Album Name: {album_name}
Album Description: {album_description}
{context_block}
        """
        return system_instruction, task_prompt
