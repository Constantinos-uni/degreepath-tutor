"""
Complete System Test Suite

Tests both Part 1 and Part 2 APIs with real integration scenarios.
Run this after starting both API services.
"""

import requests
import json
import time
import sys

BASE_PART1 = "http://localhost:8000"
BASE_PART2 = "http://localhost:8001"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}[PASS] {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


def wait_for_api(url: str, name: str, timeout: int = 30) -> bool:
    """Wait for an API to be ready."""
    print_info(f"Waiting for {name}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                print_success(f"{name} is ready")
                return True
        except Exception:
            time.sleep(1)
            sys.stdout.write('.')
            sys.stdout.flush()
    print_error(f"{name} failed to start")
    return False


def test_part1_basic() -> bool:
    """Test Part 1 basic functionality."""
    print_header("Part 1: Basic Tests")
    
    try:
        # Health check
        r = requests.get(f"{BASE_PART1}/health", timeout=5)
        assert r.status_code == 200
        print_success("Health check passed")
        
        # Get unit
        r = requests.get(f"{BASE_PART1}/unit/COMP1000", timeout=5)
        assert r.status_code == 200
        unit = r.json()
        assert "details" in unit
        print_success(f"Unit fetch: {unit['details']['title']}")
        
        # Get another unit
        r = requests.get(f"{BASE_PART1}/unit/COMP1010", timeout=5)
        assert r.status_code == 200
        unit = r.json()
        print_success(f"Unit fetch: {unit['details']['title']}")
        
        return True
    except Exception as e:
        print_error(f"Part 1 basic test failed: {e}")
        return False


def test_part1_eligibility() -> bool:
    """Test Part 1 eligibility checking."""
    print_header("Part 1: Eligibility Tests")
    
    try:
        # Test 1: Should be eligible (has prerequisites)
        r = requests.post(f"{BASE_PART1}/eligibility", json={
            "degree": "Bachelor of IT",
            "completed_units": ["COMP1000"],
            "query_units": ["COMP1010"]
        }, timeout=5)
        
        result = r.json()
        assert result["eligible"] == True
        print_success("Eligibility check: PASS (has prerequisites)")
        
        # Test 2: Should NOT be eligible (missing prerequisites)
        r = requests.post(f"{BASE_PART1}/eligibility", json={
            "degree": "Bachelor of IT",
            "completed_units": [],
            "query_units": ["COMP1010"]
        }, timeout=5)
        
        result = r.json()
        assert result["eligible"] == False
        assert "COMP1000" in result["missing_prerequisites"]
        print_success("Eligibility check: FAIL (missing prerequisites) - Correct!")
        
        return True
    except Exception as e:
        print_error(f"Part 1 eligibility test failed: {e}")
        return False


def test_part2_basic() -> bool:
    """Test Part 2 basic functionality."""
    print_header("Part 2: Basic Tests")
    
    try:
        # Health check
        r = requests.get(f"{BASE_PART2}/health", timeout=5)
        assert r.status_code == 200
        health = r.json()
        print_success(f"Health check: {health['status']}")
        print_info(f"  AI Ready: {health.get('ai_ready', 'N/A')}")
        print_info(f"  Search Ready: {health.get('search_ready', 'N/A')}")
        
        # Root endpoint
        r = requests.get(f"{BASE_PART2}/", timeout=5)
        info = r.json()
        print_success(f"Service: {info['service']} v{info['version']}")
        
        return True
    except Exception as e:
        print_error(f"Part 2 basic test failed: {e}")
        return False


def test_student_management() -> bool:
    """Test student management features."""
    print_header("Part 2: Student Management")
    
    try:
        # List students
        r = requests.get(f"{BASE_PART2}/students", timeout=5)
        students = r.json()
        assert len(students) >= 2
        print_success(f"Found {len(students)} demo students")
        
        # Get specific students
        for student_id in ["demo001", "demo002"]:
            r = requests.get(f"{BASE_PART2}/students/{student_id}", timeout=5)
            student = r.json()
            print_success(f"  - {student['name']}: {student['degree']}")
            print_info(f"    Completed: {len(student['completed_units'])} units")
            print_info(f"    Enrolled: {len(student['enrolled_units'])} units")
        
        return True
    except Exception as e:
        print_error(f"Student management test failed: {e}")
        return False


def test_report_generation() -> bool:
    """Test report generation with AI and web search."""
    print_header("Part 2: Report Generation (This may take 30-60s)")
    
    try:
        print_info("Generating report for COMP1010 with student demo001...")
        print_info("(Watch for web search activity in Part 2 terminal)")
        
        start_time = time.time()
        
        r = requests.post(f"{BASE_PART2}/tutor-report", json={
            "unit_code": "COMP1010",
            "student_id": "demo001"
        }, timeout=120)
        
        elapsed = time.time() - start_time
        
        assert r.status_code == 200
        report = r.json()
        
        print_success(f"Report generated in {elapsed:.1f}s")
        
        # Verify structure
        assert report["unit_code"] == "COMP1010"
        print_success(f"Unit code: {report['unit_code']}")
        
        assert "summary" in report
        print_success(f"Summary: {report['summary'][:80]}...")
        
        assert report["difficulty"] in ["easy", "medium", "hard"]
        print_success(f"Difficulty: {report['difficulty'].upper()}")
        
        assert len(report.get("core_skills", [])) > 0
        print_success(f"Core skills: {len(report['core_skills'])} skills")
        
        assert len(report.get("key_concepts", [])) > 0
        print_success(f"Key concepts: {len(report['key_concepts'])} concepts")
        
        assert len(report.get("study_plan", [])) == 4
        print_success("Study plan: 4 weeks")
        
        assert len(report.get("quizzes", [])) > 0
        print_success(f"Quizzes: {len(report['quizzes'])} questions")
        
        assert len(report.get("public_resources", [])) > 0
        print_success(f"Resources: {len(report['public_resources'])} resources")
        
        # Check if resources are real web results
        print_info("\n  Real web search results:")
        for i, resource in enumerate(report["public_resources"][:3], 1):
            print_info(f"    {i}. [{resource['type'].upper()}] {resource['title'][:50]}...")
            print_info(f"       {resource['url'][:60]}...")
        
        return True
    except Exception as e:
        print_error(f"Report generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_report_without_student() -> bool:
    """Test report generation without student profile."""
    print_header("Part 2: Report Without Student Profile")
    
    try:
        print_info("Generating report for COMP1000 (no student)...")
        
        r = requests.get(f"{BASE_PART2}/tutor-report/COMP1000", timeout=120)
        
        assert r.status_code == 200
        report = r.json()
        
        print_success("Report generated successfully")
        print_success(f"Difficulty: {report['difficulty']}")
        print_success(f"Resources: {len(report['public_resources'])} found")
        
        return True
    except Exception as e:
        print_error(f"Report without student test failed: {e}")
        return False


def test_integration() -> bool:
    """Test full Part 1 + Part 2 integration."""
    print_header("Integration Test: Part 1 + Part 2")
    
    try:
        # Step 1: Check eligibility in Part 1
        print_info("Step 1: Checking eligibility in Part 1...")
        r = requests.post(f"{BASE_PART1}/eligibility", json={
            "degree": "Bachelor of IT",
            "completed_units": ["COMP1000"],
            "query_units": ["COMP1010"]
        }, timeout=5)
        
        eligibility = r.json()
        assert eligibility["eligible"] == True
        print_success("Student is eligible for COMP1010")
        
        # Step 2: Generate study plan in Part 2
        print_info("Step 2: Generating study plan in Part 2...")
        r = requests.post(f"{BASE_PART2}/tutor-report", json={
            "unit_code": "COMP1010",
            "completed_units": ["COMP1000"]
        }, timeout=120)
        
        report = r.json()
        print_success("Study plan generated")
        
        # Step 3: Verify consistency
        print_info("Step 3: Verifying data consistency...")
        assert report["unit_code"] == "COMP1010"
        
        print_success("Integration test passed!")
        return True
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        return False


def run_all_tests() -> bool:
    """Run complete test suite."""
    print("\n" + "="*70)
    print(f"{Colors.BOLD}  DegreePath Tutor - Complete Test Suite{Colors.RESET}")
    print("="*70)
    
    # Check if services are running
    print_header("Pre-flight Checks")
    
    if not wait_for_api(BASE_PART1, "Part 1 API"):
        print_error("\nPart 1 API is not running!")
        print_info("Start it with: cd backend && python main.py")
        return False
    
    if not wait_for_api(BASE_PART2, "Part 2 API", timeout=60):
        print_error("\nPart 2 API is not running!")
        print_info("Start it with: cd part2 && python main.py")
        return False
    
    # Run tests
    results = []
    
    results.append(("Part 1 Basic", test_part1_basic()))
    results.append(("Part 1 Eligibility", test_part1_eligibility()))
    results.append(("Part 2 Basic", test_part2_basic()))
    results.append(("Student Management", test_student_management()))
    results.append(("Report Generation", test_report_generation()))
    results.append(("Report (No Student)", test_report_without_student()))
    results.append(("Integration", test_integration()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name:<30} PASSED")
        else:
            print_error(f"{name:<30} FAILED")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED! System is working correctly.{Colors.RESET}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed. Check errors above.{Colors.RESET}\n")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
