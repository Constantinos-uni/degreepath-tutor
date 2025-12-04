import requests
from bs4 import BeautifulSoup
import re
from .database import save_unit
import time

BASE_URL = "https://unitguides.mq.edu.au"

def scrape_unit_list(department_url: str):
    """
    Scrapes a list of unit guide URLs from a department page.
    Example URL: https://unitguides.mq.edu.au/units/show_year/2025/School%20of%20Computing
    """
    print(f"Fetching unit list from {department_url}...")
    response = requests.get(department_url)
    if response.status_code != 200:
        print(f"Failed to fetch {department_url}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    unit_links = []
    
    # Find all links that look like unit guides
    # The structure usually has links with class or specific pattern
    # Based on observation: <a href="/unit_offerings/173183/unit_guide">COMP1000 ...</a>
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if "/unit_offerings/" in href and "/unit_guide" in href:
            full_url = BASE_URL + href if href.startswith("/") else href
            unit_links.append(full_url)
            
    return list(set(unit_links)) # Deduplicate

def scrape_unit_detail(unit_url: str):
    """
    Scrapes details for a single unit.
    """
    print(f"Scraping unit: {unit_url}")
    try:
        response = requests.get(unit_url)
        if response.status_code != 200:
            print(f"Failed to fetch {unit_url}")
            return
    except Exception as e:
        print(f"Error fetching {unit_url}: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract Title and Code
    # Find all H1s and look for the pattern
    unit_code = None
    title = None
    
    for h1 in soup.find_all('h1'):
        text = h1.get_text(strip=True)
        # Pattern: 4 letters, 4 digits, optional space, hyphen/dash, space, title
        # e.g. "COMP1000 – Introduction to Computer Programming"
        # Note: The dash might be a hyphen -, en dash –, or em dash —
        match = re.search(r"([A-Z]{4}\d{4})\s*[–-—]\s*(.*)", text)
        if match:
            unit_code = match.group(1)
            title = match.group(2)
            break
            
    if not unit_code:
        print(f"Could not find unit code/title in H1s. Found: {[h.get_text(strip=True) for h in soup.find_all('h1')]}")
        return

    # Extract Description (General Information)
    description = ""
    # Look for h2 "General Information"
    gen_info = soup.find('h2', string=re.compile("General Information", re.I))
    if gen_info:
        # The content is usually in the next sibling div or the parent's next sibling
        # Let's try to get the text of the parent section if possible, or just next siblings
        # A robust way is to iterate next_siblings until the next h2
        content_parts = []
        curr = gen_info.next_sibling
        while curr and curr.name != 'h2':
            if curr.name: # if it's a tag
                content_parts.append(curr.get_text(strip=True))
            curr = curr.next_sibling
        description = " ".join(content_parts)
        
        # Fallback: if empty, try parent's text
        if not description.strip():
             parent = gen_info.find_parent('div') or gen_info.find_parent('section')
             if parent:
                 description = parent.get_text(strip=True).replace("General Information", "")

    # Extract Learning Outcomes
    outcomes = []
    lo_header = soup.find('h2', string=re.compile("Learning Outcomes", re.I))
    if lo_header:
        # Look for the list in the following siblings
        curr = lo_header.next_sibling
        while curr and curr.name != 'h2':
            if curr.name == 'ul' or curr.name == 'ol':
                outcomes = [li.get_text(strip=True) for li in curr.find_all('li')]
                break
            # If it's a div, check inside
            if curr.name == 'div':
                ul = curr.find('ul') or curr.find('ol')
                if ul:
                    outcomes = [li.get_text(strip=True) for li in ul.find_all('li')]
                    break
            curr = curr.next_sibling

    # Extract Prerequisites / Enrolment Requirements
    raw_prereqs = ""
    raw_coreqs = ""
    
    body_text = soup.get_text()
    
    # Regex for Prerequisites
    # "Prerequisite: COMP1000" or "Pre-requisite: ..." or "Prerequisites: Admission to MRes"
    # We need to be careful not to capture too much garbage.
    # Try to capture until the next major label or end of paragraph.
    prereq_match = re.search(r"(?:Prerequisite[s]?|Pre-requisite[s]?)\s*[:]?\s*(.*?)(?:\n\n|\n[A-Z]|$)", body_text, re.IGNORECASE | re.DOTALL)
    if prereq_match:
        # Take the first line or few sentences
        raw_prereqs = prereq_match.group(1).strip()
        
    coreq_match = re.search(r"(?:Corequisite[s]?|Co-requisite[s]?)\s*[:]?\s*(.*?)(?:\n\n|\n[A-Z]|$)", body_text, re.IGNORECASE | re.DOTALL)
    if coreq_match:
        raw_coreqs = coreq_match.group(1).strip()

    unit_data = {
        "unit_code": unit_code,
        "title": title,
        "description": description[:500],
        "learning_outcomes": outcomes,
        "raw_prerequisites": raw_prereqs,
        "raw_corequisites": raw_coreqs,
        "year_level": int(unit_code[4]) if len(unit_code) > 4 and unit_code[4].isdigit() else 1
    }
    
    print(f"Saving {unit_code}...")
    save_unit(unit_data)
    return unit_data

def run_scraper():
    # Example: Scrape School of Computing
    dept_url = "https://unitguides.mq.edu.au/units/show_year/2025/School%20of%20Computing"
    links = scrape_unit_list(dept_url)
    print(f"Found {len(links)} units.")
    
    count = 0
    for link in links:
        # if count >= 20: break # Limit removed to scrape all units
        pass
        scrape_unit_detail(link)
        count += 1
        time.sleep(1) # Be polite

    # Trigger RAG Ingestion
    print("Triggering RAG Ingestion...")
    try:
        # Import here to avoid potential circular imports at top level if any
        from .rag import rag_system
        import asyncio
        asyncio.run(rag_system.ingest_units())
        print("RAG Ingestion Complete.")
    except Exception as e:
        print(f"RAG Ingestion Failed: {e}")

if __name__ == "__main__":
    run_scraper()
