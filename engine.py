"""
Publisher Final Delivery App - Ingestion Engine
Handles Local File System data ingestion, audio analysis via Gemini, Validation, and ZIP compilation.
"""
import os
import json
import time
import re
import io
import zipfile
import pandas as pd
import google.generativeai as genai
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from prompts import PromptEngine

DEFAULT_ROOT_PATH = Path(".")

class IngestionEngine:
    """Core engine for handling data ingestion and processing via Local File System."""
    
    def __init__(self, root_path: Optional[str] = None):
        self.root_path = Path(root_path) if root_path else DEFAULT_ROOT_PATH
        self.folders: Dict[str, Optional[Path]] = {
            "01_VISUAL_REFERENCES": None,
            "02_VOICE_GUIDES": None,
            "03_METADATA_MASTER": None
        }
        self.prompts = PromptEngine(str(self.root_path))
        
        if self.root_path.exists():
            self._resolve_subfolders()
        else:
            print(f"Warning: Root path '{self.root_path}' does not exist.")

    def set_root_path(self, root_path: str):
        self.root_path = Path(root_path)
        self.prompts = PromptEngine(str(self.root_path))
        if self.root_path.exists():
            self._resolve_subfolders()
        else:
            print(f"Warning: Root path '{self.root_path}' does not exist.")

    def _resolve_subfolders(self):
        try:
            subdirs = [d for d in self.root_path.iterdir() if d.is_dir()]
            for folder_key in self.folders.keys():
                match = next((d for d in subdirs if folder_key.lower() in d.name.lower()), None)
                if match:
                    self.folders[folder_key] = match
                else:
                    self.folders[folder_key] = None
        except Exception as error:
            print(f"Error resolving subfolders: {error}")

    def get_metadata_df(self, catalog: Optional[str] = None) -> Optional[pd.DataFrame]:
        folder_path = self.folders.get("03_METADATA_MASTER")
        if not folder_path or not folder_path.exists(): return None
        try:
            csv_files = list(folder_path.glob("*.csv"))
            if catalog:
                csv_files = [f for f in csv_files if catalog.lower() in f.name.lower()]
            if not csv_files: return None
            
            dfs = []
            for file_path in csv_files:
                try:
                    df = pd.read_csv(file_path)
                    dfs.append(df)
                except Exception: pass
            
            if dfs: return pd.concat(dfs, ignore_index=True)
            return None
        except Exception:
            return None

    def process_keywords(self, keywords_raw: str, catalog: str, api_key: str) -> str:
        """Processes and auto-corrects keywords to enforce the 3-word limit, Title Case, and removes banned words."""
        if not keywords_raw: return ""
        kw_list = [k.strip() for k in re.split(r'[,;]', keywords_raw) if k.strip()]
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') 
        
        corrected_keywords = []
        for kw in kw_list:
            if kw.count(' ') > 2:
                prompt = self.prompts.get_harvest_loop_prompt(kw)
                try:
                    res = model.generate_content(prompt)
                    new_kw = res.text.strip()
                    corrected_keywords.append(new_kw if new_kw else kw)
                except Exception:
                    corrected_keywords.append(kw)
            else:
                corrected_keywords.append(kw)

        # 2. Case-Insensitive Ban Check
        banned_from_catalog = set()
        folder_path = self.folders.get("02_VOICE_GUIDES")
        if folder_path and folder_path.exists():
            banned_file = folder_path / "Banned_Keywords.txt"
            if banned_file.exists():
                text = banned_file.read_text(encoding='utf-8')
                banned_from_catalog.update([line.strip().lower() for line in text.splitlines() if line.strip()])

        global_bans = {"epic", "huge", "massive", "awesome", "badass"}
        
        final_keywords = []
        for kw in corrected_keywords:
            kw_lower = kw.lower()
            words_in_kw = set(kw_lower.split())
            has_ban = any(ban in words_in_kw for ban in global_bans) or any(ban in kw_lower for ban in banned_from_catalog)
            if not has_ban and kw_lower not in global_bans and kw_lower not in banned_from_catalog:
                # Force Max 3 Words truncation just in case LLM failed
                parts = kw_lower.split()
                if len(parts) > 3:
                     final_kw = " ".join(parts[:3]).title()
                else:
                     final_kw = kw.title()
                final_keywords.append(final_kw)

        return ", ".join(final_keywords)

    def analyze_audio_file(self, file_path: str, catalog: str, api_key: str) -> Optional[Dict]:
        """Analyzes an audio file using Gemini to extract metadata."""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            audio_file = genai.upload_file(path=file_path)
            while audio_file.state.name == "PROCESSING":
                time.sleep(1)
                audio_file = genai.get_file(audio_file.name)
                
            if audio_file.state.name == "FAILED": return None
                
            analysis_prompt = self.prompts.generate_keywords_analysis_prompt(catalog)
            response = model.generate_content([analysis_prompt, audio_file])
            genai.delete_file(audio_file.name)
            
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.endswith("```"): text = text[:-3]
            
            metadata = json.loads(text.strip())
            if "Keywords" in metadata and metadata["Keywords"]:
                metadata["Keywords"] = self.process_keywords(metadata["Keywords"], catalog, api_key)
                
            return metadata
        except Exception as e:
            print(f"Error analyzing audio: {e}")
            return None

    def call_gemini(self, model_name: str, system_instr: str, prompt: str, api_key: str) -> str:
        """Helper to invoke Gemini."""
        genai.configure(api_key=api_key)
        # Combine system instruction and prompt for v1.5 API handling simplicity
        full_prompt = f"System Instruction:\n{system_instr}\n\nTask:\n{prompt}"
        model = genai.GenerativeModel(model_name)
        try:
            res = model.generate_content(full_prompt)
            return res.text.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    # --- THE FINAL EXPORT GATE (TAB 07) Validator ---
    def validate_data(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        The Clean Room Validator.
        Checks:
        1. Keywords: max 2 spaces (3 words)
        2. Descriptions: Antigravity Protocol (1st sentence cannot start with A, An, The)
        3. Banned words: cross-checks globally against catalog list.
        """
        errors = []
        
        # Load Ban list
        banned = {"epic", "huge", "massive", "awesome", "badass"}
        folder_path = self.folders.get("02_VOICE_GUIDES")
        if folder_path and folder_path.exists():
            banned_file = folder_path / "Banned_Keywords.txt"
            if banned_file.exists():
                text = banned_file.read_text(encoding='utf-8')
                banned.update([line.strip().lower() for line in text.splitlines() if line.strip()])

        # 1. Check Track Metadata (DataFrame or List of Dicts)
        tracks = data.get('tracks', [])
        for i, track in enumerate(tracks):
            title = track.get('Title', f'Track {i+1}')
            
            # Keywords Check
            kw_str = track.get('Keywords', '')
            if kw_str:
                for kw in kw_str.split(','):
                    kw = kw.strip()
                    if kw.count(' ') > 2:
                        errors.append(f"ERROR: Track '{title}' keyword '{kw}' contains too many spaces (>2).")
                    
                    # Ban Check
                    kw_lower = kw.lower()
                    if any(b in kw_lower for b in banned):
                        errors.append(f"ERROR: Track '{title}' keyword '{kw}' contains a banned word.")
            
            # Description (Antigravity Protocol)
            desc = track.get('Track Description', '').strip()
            if desc:
                first_word = desc.split(' ')[0].lower()
                # Remove punctuation from first word
                first_word = re.sub(r'^\W+|\W+$', '', first_word)
                if first_word in ['a', 'an', 'the']:
                     errors.append(f"ERROR: Track '{title}' description violates the Antigravity Protocol (Starts with '{first_word}').")
        
        # 2. Check Album Name & Description for Banned Words
        album_desc = data.get('album_description', '').lower()
        if any(b in album_desc for b in banned):
             errors.append("ERROR: Album Description contains a banned word.")
             
        album_name = data.get('album_name', '').lower()
        if any(b in album_name for b in banned):
             errors.append("ERROR: Album Name contains a banned word.")
             
        # Add basic requirement checks
        if not tracks:
            errors.append("ERROR: No track data found to export.")

        return len(errors) == 0, errors

    def compile_final_package(self, data: Dict) -> io.BytesIO:
        """
        The Master Zip Compiler.
        Creates exactly 6 folders with respective metadata inside a ZIP memory stream.
        """
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Folder 01 Track Keywords (Contains CSV)
            if 'tracks' in data and data['tracks']:
                df_kw = pd.DataFrame(data['tracks'])[['Title', 'Keywords']]
                zip_file.writestr('01 Track Keywords/Track_Keywords.csv', df_kw.to_csv(index=False))
            
            # Folder 02 Track Descriptions (Contains CSV)
            if 'tracks' in data and data['tracks']:
                df_desc = pd.DataFrame(data['tracks'])[['Title', 'Track Description']]
                zip_file.writestr('02 Track Descriptions/Track_Descriptions.csv', df_desc.to_csv(index=False))
            
            # Folder 03 Album Description (Contains TXT)
            album_desc = data.get('album_description', '')
            zip_file.writestr('03 Album Description/Album_Description.txt', album_desc)
            
            # Folder 04 Album Name (Contains TXT)
            album_name = data.get('album_name', '')
            zip_file.writestr('04 Album Name/Album_Name.txt', album_name)
            
            # Folder 05 Album Cover Art (ideas for MidJourney prompts) (Contains TXT)
            cover_art_prompts = data.get('cover_art', '')
            zip_file.writestr('05 Album Cover Art/MidJourney_Prompts.txt', cover_art_prompts)
            
            # Folder 06 MailChimp Intro (Contains TXT)
            mailchimp = data.get('mailchimp_intro', '')
            zip_file.writestr('06 MailChimp Intro/MailChimp_Copy.txt', mailchimp)
            
        zip_buffer.seek(0)
        return zip_buffer
