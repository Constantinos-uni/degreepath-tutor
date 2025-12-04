"""
Unit Search Module
Fetches unit information from Macquarie University unit guides.
Extracts unit code, title, description, prerequisites, and learning outcomes.
"""

import re
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://unitguides.mq.edu.au"
HANDBOOK_URL = "https://handbook.mq.edu.au"


@dataclass
class UnitInfo:
    """Structured unit information."""
    unit_code: str
    title: str
    description: str
    credit_points: int
    year_level: int
    prerequisites: List[str]
    corequisites: List[str]
    raw_prerequisites: str
    raw_corequisites: str
    learning_outcomes: List[str]
    offering_period: str
    source_url: str


class UnitSearcher:
    """Search and fetch unit information from Macquarie University."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._cache: Dict[str, UnitInfo] = {}
    
    def search_unit(self, unit_code: str) -> Optional[UnitInfo]:
        """Search for a unit by code. Returns structured unit information."""
        unit_code = unit_code.upper().strip()
        
        if unit_code in self._cache:
            return self._cache[unit_code]
        
        unit_info = self._search_department_listing(unit_code)
        
        if unit_info:
            self._cache[unit_code] = unit_info
            return unit_info
        
        unit_info = self._search_handbook(unit_code)
        
        if unit_info:
            self._cache[unit_code] = unit_info
            
        return unit_info
    
    def _search_department_listing(self, unit_code: str) -> Optional[UnitInfo]:
        """Search department listing page for the unit."""
        try:
            dept_url = f"{BASE_URL}/units/show_year/2025/School%20of%20Computing"
            response = self.session.get(dept_url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            unit_link = None
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                href = a['href']
                
                if unit_code in text and '/unit_offerings/' in href and '/unit_guide' in href:
                    unit_link = href if href.startswith('http') else BASE_URL + href
                    break
            
            if not unit_link:
                return None
            
            return self._scrape_unit_guide(unit_link, unit_code)
            
        except Exception:
            return None
    
    def _scrape_unit_guide(self, url: str, expected_code: str) -> Optional[UnitInfo]:
        """Scrape detailed unit information from a unit guide page."""
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            unit_code = None
            title = None
            
            for h1 in soup.find_all('h1'):
                text = h1.get_text(strip=True)
                match = re.search(r"([A-Z]{4}\d{4})\s*[–\-—]\s*(.*)", text)
                if match:
                    unit_code = match.group(1)
                    title = match.group(2).strip()
                    break
            
            if not unit_code:
                unit_code = expected_code
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.get_text()
                    match = re.search(r"([A-Z]{4}\d{4})\s*[–\-—]\s*(.*?)(?:\||$)", title_text)
                    if match:
                        title = match.group(2).strip()
            
            if not title:
                title = f"Unit {unit_code}"
            
            description = self._extract_description(soup)
            prereqs, raw_prereqs = self._extract_prerequisites(soup)
            coreqs, raw_coreqs = self._extract_corequisites(soup)
            outcomes = self._extract_learning_outcomes(soup)
            credit_points = self._extract_credit_points(soup)
            offering = self._extract_offering_period(soup)
            year_level = int(unit_code[4]) if len(unit_code) > 4 and unit_code[4].isdigit() else 1
            
            return UnitInfo(
                unit_code=unit_code,
                title=title,
                description=description,
                credit_points=credit_points,
                year_level=year_level,
                prerequisites=prereqs,
                corequisites=coreqs,
                raw_prerequisites=raw_prereqs,
                raw_corequisites=raw_coreqs,
                learning_outcomes=outcomes,
                offering_period=offering,
                source_url=url
            )
            
        except Exception:
            return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract unit description"""
        description = ""
        
        # Look for "General Information" section
        gen_info = soup.find('h2', string=re.compile(r"General\s+Information", re.I))
        if gen_info:
            content_parts = []
            curr = gen_info.next_sibling
            while curr and getattr(curr, 'name', None) != 'h2':
                if hasattr(curr, 'get_text'):
                    text = curr.get_text(strip=True)
                    # Filter out noise
                    if text and len(text) > 20 and 'Download as PDF' not in text:
                        content_parts.append(text)
                curr = getattr(curr, 'next_sibling', None)
            description = " ".join(content_parts)
        
        # Try to find description in a div with class containing 'description' or 'overview'
        if not description or len(description) < 50:
            for div in soup.find_all('div'):
                div_class = ' '.join(div.get('class', []))
                if 'description' in div_class.lower() or 'overview' in div_class.lower():
                    text = div.get_text(strip=True)
                    if len(text) > 50 and 'Download as PDF' not in text:
                        description = text
                        break
        
        # Try to find any paragraph that looks like a description
        if not description or len(description) < 50:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 100 and 'Download as PDF' not in text:
                    description = text
                    break
        
        # Fallback: look for meta description
        if not description or len(description) < 50:
            meta = soup.find('meta', attrs={'name': 'description'})
            if meta and meta.get('content'):
                description = meta['content']
        
        # Clean up description
        description = ' '.join(description.split())
        
        return description[:1000] if description else "No description available"
    
    def _extract_prerequisites(self, soup: BeautifulSoup) -> tuple:
        """Extract prerequisites - returns (list of codes, raw text)"""
        prereq_codes = []
        raw_text = ""
        
        body_text = soup.get_text()
        
        # Method 1: Look for Prerequisites section followed by unit codes
        # The pattern is: "Prerequisites" then possibly more text, then unit codes like COMP1010
        prereq_section = re.search(
            r'Prerequisites\s*\n*\s*Prerequisites?\s*\n*\s*(.*?)(?:Corequisites|Co-requisites|Co-badged|Assessment|$)',
            body_text,
            re.IGNORECASE | re.DOTALL
        )
        
        if prereq_section:
            section_text = prereq_section.group(1).strip()
            # Extract all unit codes from this section
            codes = re.findall(r'[A-Z]{4}\d{4}', section_text)
            prereq_codes.extend(codes)
            raw_text = section_text[:500]
        
        # Method 2: Also check for simpler patterns
        if not prereq_codes:
            simple_match = re.search(
                r'(?:Prerequisite[s]?|Pre-requisite[s]?)\s*[:]?\s*([A-Z]{4}\d{4}(?:\s*(?:and|or|,)\s*[A-Z]{4}\d{4})*)',
                body_text,
                re.IGNORECASE
            )
            if simple_match:
                raw_text = simple_match.group(1)
                codes = re.findall(r'[A-Z]{4}\d{4}', raw_text)
                prereq_codes.extend(codes)
        
        # Method 3: Look for "Admission to" or "Enrolment in" patterns (for postgrad units)
        if not prereq_codes:
            admission_match = re.search(
                r'(?:Admission\s+to|Enrolment\s+in)\s+([^\.]+)',
                body_text,
                re.IGNORECASE
            )
            if admission_match:
                raw_text = admission_match.group(1).strip()[:200]
        
        # Deduplicate while preserving order
        seen = set()
        unique_codes = []
        for code in prereq_codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)
        
        # Clean up raw_text
        raw_text = ' '.join(raw_text.split())  # Normalize whitespace
        
        return unique_codes, raw_text if raw_text else "None"
    
    def _extract_corequisites(self, soup: BeautifulSoup) -> tuple:
        """Extract corequisites - returns (list of codes, raw text)"""
        coreq_codes = []
        raw_text = ""
        
        body_text = soup.get_text()
        
        # Look for Corequisites section
        coreq_section = re.search(
            r'Corequisites\s*\n*\s*Corequisites?\s*\n*\s*(.*?)(?:Co-badged|Assessment|Incompatible|$)',
            body_text,
            re.IGNORECASE | re.DOTALL
        )
        
        if coreq_section:
            section_text = coreq_section.group(1).strip()
            codes = re.findall(r'[A-Z]{4}\d{4}', section_text)
            coreq_codes.extend(codes)
            raw_text = section_text[:500]
        
        # Simple pattern fallback
        if not coreq_codes:
            simple_match = re.search(
                r'(?:Corequisite[s]?|Co-requisite[s]?)\s*[:]?\s*([A-Z]{4}\d{4}(?:\s*(?:and|or|,)\s*[A-Z]{4}\d{4})*)',
                body_text,
                re.IGNORECASE
            )
            if simple_match:
                raw_text = simple_match.group(1)
                codes = re.findall(r'[A-Z]{4}\d{4}', raw_text)
                coreq_codes.extend(codes)
        
        # Clean up
        raw_text = ' '.join(raw_text.split())
        
        return list(set(coreq_codes)), raw_text if raw_text else "None"
    
    def _extract_learning_outcomes(self, soup: BeautifulSoup) -> List[str]:
        """Extract learning outcomes"""
        outcomes = []
        
        lo_header = soup.find('h2', string=re.compile(r"Learning\s+Outcomes?", re.I))
        if lo_header:
            curr = lo_header.next_sibling
            while curr and getattr(curr, 'name', None) != 'h2':
                if getattr(curr, 'name', None) in ['ul', 'ol']:
                    for li in curr.find_all('li'):
                        text = li.get_text(strip=True)
                        if text:
                            outcomes.append(text)
                    break
                elif getattr(curr, 'name', None) == 'div':
                    ul = curr.find('ul') or curr.find('ol')
                    if ul:
                        for li in ul.find_all('li'):
                            text = li.get_text(strip=True)
                            if text:
                                outcomes.append(text)
                        break
                curr = getattr(curr, 'next_sibling', None)
        
        return outcomes
    
    def _extract_credit_points(self, soup: BeautifulSoup) -> int:
        """Extract credit points"""
        body_text = soup.get_text()
        
        # Look for "Credit Points: 10" or similar patterns
        match = re.search(r'Credit\s*Points?\s*[:\-]?\s*(\d+)', body_text, re.IGNORECASE)
        if match:
            cp = int(match.group(1))
            # Sanity check - credit points should be reasonable (1-60)
            if 1 <= cp <= 60:
                return cp
        
        # Look for "10cp" or "10 cp" pattern
        match = re.search(r'(\d+)\s*cp\b', body_text, re.IGNORECASE)
        if match:
            cp = int(match.group(1))
            if 1 <= cp <= 60:
                return cp
        
        return 10  # Default for most MQ units
    
    def _extract_offering_period(self, soup: BeautifulSoup) -> str:
        """Extract offering period (e.g., S1 2025, S2 2025)"""
        body_text = soup.get_text()
        
        # Look for session patterns
        match = re.search(r"(S[1-2]\s*\d{4}|Session\s*[1-2]\s*\d{4}|Semester\s*[1-2]\s*\d{4})", body_text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return "2025"
    
    def _search_handbook(self, unit_code: str) -> Optional[UnitInfo]:
        """Fallback search in the MQ handbook"""
        try:
            # Try handbook URL
            handbook_url = f"{HANDBOOK_URL}/2025/units/{unit_code}"
            response = self.session.get(handbook_url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else f"Unit {unit_code}"
            
            # Remove unit code from title if present
            title = re.sub(rf"^{unit_code}\s*[–\-—]\s*", "", title)
            
            # Extract description
            desc_section = soup.find('div', class_=re.compile(r'description|overview', re.I))
            description = desc_section.get_text(strip=True) if desc_section else ""
            
            # Extract prerequisites
            prereq_section = soup.find(string=re.compile(r"prerequisite", re.I))
            prereqs = []
            raw_prereqs = ""
            if prereq_section:
                parent = prereq_section.find_parent()
                if parent:
                    raw_prereqs = parent.get_text(strip=True)
                    prereqs = re.findall(r"[A-Z]{4}\d{4}", raw_prereqs)
            
            year_level = int(unit_code[4]) if len(unit_code) > 4 and unit_code[4].isdigit() else 1
            
            return UnitInfo(
                unit_code=unit_code,
                title=title,
                description=description[:1000],
                credit_points=10,
                year_level=year_level,
                prerequisites=prereqs,
                corequisites=[],
                raw_prerequisites=raw_prereqs,
                raw_corequisites="",
                learning_outcomes=[],
                offering_period="2025",
                source_url=handbook_url
            )
            
        except Exception as e:
            print(f"[ERROR] Handbook search failed: {e}")
            return None
    
    def get_all_computing_units(self) -> List[str]:
        """Get list of all computing unit codes from the School of Computing"""
        try:
            dept_url = f"{BASE_URL}/units/show_year/2025/School%20of%20Computing"
            response = self.session.get(dept_url, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            unit_codes = set()
            for a in soup.find_all('a', href=True):
                text = a.get_text(strip=True)
                codes = re.findall(r"[A-Z]{4}\d{4}", text)
                unit_codes.update(codes)
            
            return sorted(list(unit_codes))
            
        except Exception as e:
            print(f"[ERROR] Failed to get unit list: {e}")
            return []


unit_searcher = UnitSearcher()


def search_unit(unit_code: str) -> Optional[Dict[str, Any]]:
    """
    Search for a unit by code.
    Returns dictionary with unit information or None.
    """
    result = unit_searcher.search_unit(unit_code)
    
    if result:
        return {
            "unit_code": result.unit_code,
            "title": result.title,
            "description": result.description,
            "credit_points": result.credit_points,
            "year_level": result.year_level,
            "prerequisites": result.prerequisites,
            "corequisites": result.corequisites,
            "raw_prerequisites": result.raw_prerequisites,
            "raw_corequisites": result.raw_corequisites,
            "learning_outcomes": result.learning_outcomes,
            "offering_period": result.offering_period,
            "source_url": result.source_url
        }
    
    return None


if __name__ == "__main__":
    test_units = ["COMP1010", "COMP1000"]
    
    for code in test_units:
        print(f"\nSearching for: {code}")
        result = search_unit(code)
        
        if result:
            print(f"  Title: {result['title']}")
            print(f"  Prerequisites: {result['prerequisites']}")
        else:
            print(f"  Not found")
        
        time.sleep(1)
