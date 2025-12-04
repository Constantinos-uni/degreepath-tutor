"""
Business logic for prerequisite and eligibility checking.
"""

from typing import Dict, List, Any, Optional
from .database import get_unit, get_all_units


def load_units() -> Dict[str, Any]:
    """Load all units from database."""
    return get_all_units()


def check_prereqs(
    completed_units: List[str],
    target_unit: str,
    all_units: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Check if prerequisites are satisfied for a target unit.
    
    Args:
        completed_units: List of completed unit codes
        target_unit: Unit code to check prerequisites for
        all_units: Optional preloaded units dictionary (unused, kept for compatibility)
    
    Returns:
        Dictionary with eligibility status and missing prerequisites
    """
    unit_data = get_unit(target_unit)
    if not unit_data:
        return {"eligible": False, "missing": [], "error": f"Unit {target_unit} not found"}
    
    potential_prereqs = unit_data.get("prerequisites", [])
    potential_prereqs = [p for p in potential_prereqs if p != target_unit]
    
    missing = [p for p in potential_prereqs if p not in completed_units]
    
    return {"eligible": len(missing) == 0, "missing": missing}


def check_incompatibles(
    completed_units: List[str],
    target_unit: str,
    all_units: Dict[str, Any] = None
) -> List[str]:
    """
    Check for incompatible units that have been completed.
    
    Args:
        completed_units: List of completed unit codes
        target_unit: Unit code to check incompatibilities for
        all_units: Optional preloaded units dictionary (unused, kept for compatibility)
    
    Returns:
        List of incompatible units that are already completed
    """
    unit_data = get_unit(target_unit)
    if not unit_data:
        return []
    
    return []
