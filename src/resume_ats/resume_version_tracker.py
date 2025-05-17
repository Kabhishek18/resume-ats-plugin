"""
Resume version tracking functionality for Resume ATS Plugin.
"""

import os
import json
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple
import difflib

class ResumeVersionTracker:
    """Class to track and compare different versions of a resume."""
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize the version tracker.
        
        Args:
            storage_dir: Directory to store version data (defaults to user home)
        """
        if storage_dir is None:
            self.storage_dir = os.path.join(os.path.expanduser("~"), ".resume_ats")
        else:
            self.storage_dir = storage_dir
            
        # Ensure storage directory exists
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Path to the version database
        self.versions_db_path = os.path.join(self.storage_dir, "versions.json")
        
        # Initialize database if it doesn't exist
        if not os.path.exists(self.versions_db_path):
            self._write_db({})
    
    def _read_db(self) -> Dict:
        """Read the versions database."""
        try:
            with open(self.versions_db_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_db(self, data: Dict) -> None:
        """Write to the versions database."""
        with open(self.versions_db_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _calculate_hash(self, file_path: str) -> str:
        """Calculate a hash for a file."""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    
    def save_version(self, resume_path: str, analysis_result: Dict[str, Any], 
                    version_name: Optional[str] = None) -> str:
        """
        Save a resume version.
        
        Args:
            resume_path: Path to the resume file
            analysis_result: Analysis result from ResumeATS
            version_name: Optional name for this version
            
        Returns:
            Version ID
        """
        # Get file hash
        file_hash = self._calculate_hash(resume_path)
        
        # Generate a version ID
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        version_id = f"{timestamp}_{file_hash[:8]}"
        
        # Get file extension
        _, ext = os.path.splitext(resume_path)
        
        # Copy the resume file to storage
        storage_filename = f"{version_id}{ext}"
        storage_path = os.path.join(self.storage_dir, storage_filename)
        
        # Copy file
        with open(resume_path, 'rb') as src, open(storage_path, 'wb') as dst:
            dst.write(src.read())
        
        # Store metadata
        db = self._read_db()
        
        if version_name is None:
            version_name = f"Version {len(db) + 1}"
        
        db[version_id] = {
            "filename": os.path.basename(resume_path),
            "storage_path": storage_path,
            "timestamp": datetime.datetime.now().isoformat(),
            "version_name": version_name,
            "analysis_summary": {
                "overall_ats_score": analysis_result.get("stats", {}).get("overall_ats_score", 0),
                "keyword_match_score": analysis_result.get("stats", {}).get("keyword_match_score", 0),
                "format_score": analysis_result.get("stats", {}).get("format_score", 0),
                "word_count": analysis_result.get("stats", {}).get("word_count", 0),
                "sections_detected": analysis_result.get("sections_detected", [])
            }
        }
        
        self._write_db(db)
        return version_id
    
    def get_versions(self) -> List[Dict[str, Any]]:
        """
        Get all saved resume versions.
        
        Returns:
            List of version data
        """
        db = self._read_db()
        versions = []
        
        for version_id, data in db.items():
            versions.append({
                "version_id": version_id,
                "version_name": data["version_name"],
                "filename": data["filename"],
                "timestamp": data["timestamp"],
                "overall_ats_score": data["analysis_summary"].get("overall_ats_score", 0)
            })
        
        # Sort by timestamp, newest first
        versions.sort(key=lambda x: x["timestamp"], reverse=True)
        return versions
    
    def get_version_details(self, version_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific version.
        
        Args:
            version_id: Version ID
            
        Returns:
            Version details
        """
        db = self._read_db()
        if version_id not in db:
            raise ValueError(f"Version {version_id} not found")
        
        return db[version_id]
    
    def compare_versions(self, version_id1: str, version_id2: str) -> Dict[str, Any]:
        """
        Compare two resume versions.
        
        Args:
            version_id1: First version ID
            version_id2: Second version ID
            
        Returns:
            Comparison data
        """
        db = self._read_db()
        
        if version_id1 not in db:
            raise ValueError(f"Version {version_id1} not found")
        if version_id2 not in db:
            raise ValueError(f"Version {version_id2} not found")
        
        v1 = db[version_id1]
        v2 = db[version_id2]
        
        # Determine which is newer
        dt1 = datetime.datetime.fromisoformat(v1["timestamp"])
        dt2 = datetime.datetime.fromisoformat(v2["timestamp"])
        
        if dt1 > dt2:
            newer, older = v1, v2
            newer_id, older_id = version_id1, version_id2
        else:
            newer, older = v2, v1
            newer_id, older_id = version_id2, version_id1
        
        # Compare scores
        score_diff = {}
        for key in ["overall_ats_score", "keyword_match_score", "format_score"]:
            old_val = older["analysis_summary"].get(key, 0)
            new_val = newer["analysis_summary"].get(key, 0)
            
            # Convert to float for consistent comparison
            old_val = float(old_val)
            new_val = float(new_val)
            
            score_diff[key] = {
                "old": old_val,
                "new": new_val,
                "difference": new_val - old_val,
                "percentage_change": ((new_val - old_val) / max(old_val, 1)) * 100 if old_val else 0
            }
        
        # Compare sections
        old_sections = set(older["analysis_summary"].get("sections_detected", []))
        new_sections = set(newer["analysis_summary"].get("sections_detected", []))
        
        section_comparison = {
            "added": list(new_sections - old_sections),
            "removed": list(old_sections - new_sections),
            "unchanged": list(old_sections.intersection(new_sections))
        }
        
        # Compare text content if text is available
        text_diff = None
        if "extracted_text" in older and "extracted_text" in newer:
            text_diff = self._compare_text(older["extracted_text"], newer["extracted_text"])
        
        # Prepare result
        return {
            "older_version": {
                "id": older_id,
                "name": older["version_name"],
                "timestamp": older["timestamp"]
            },
            "newer_version": {
                "id": newer_id,
                "name": newer["version_name"],
                "timestamp": newer["timestamp"]
            },
            "time_between_versions": str(dt2 - dt1) if dt2 > dt1 else str(dt1 - dt2),
            "scores": score_diff,
            "word_count": {
                "old": older["analysis_summary"].get("word_count", 0),
                "new": newer["analysis_summary"].get("word_count", 0),
                "difference": newer["analysis_summary"].get("word_count", 0) - 
                             older["analysis_summary"].get("word_count", 0)
            },
            "sections": section_comparison,
            "text_diff": text_diff
        }
    
    def delete_version(self, version_id: str) -> bool:
        """
        Delete a saved version.
        
        Args:
            version_id: Version ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        db = self._read_db()
        
        if version_id not in db:
            return False
        
        # Delete the stored file
        storage_path = db[version_id]["storage_path"]
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
        except OSError:
            pass
        
        # Remove from database
        del db[version_id]
        self._write_db(db)
        
        return True
    
    def _compare_text(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare two text contents and generate diff statistics.
        
        Args:
            text1: Original text
            text2: New text
            
        Returns:
            Diff statistics
        """
        # Generate diff
        differ = difflib.Differ()
        diff = list(differ.compare(text1.splitlines(), text2.splitlines()))
        
        # Count changes
        additions = len([line for line in diff if line.startswith('+ ')])
        deletions = len([line for line in diff if line.startswith('- ')])
        changes = len([line for line in diff if line.startswith('? ')])
        
        # Create unified diff for visualization
        unified_diff = '\n'.join(difflib.unified_diff(
            text1.splitlines(),
            text2.splitlines(),
            lineterm='',
            n=3  # Context lines
        ))
        
        return {
            "additions": additions,
            "deletions": deletions,
            "changes": changes,
            "diff_summary": f"{additions} additions, {deletions} deletions, {changes} changes",
            "unified_diff": unified_diff
        }