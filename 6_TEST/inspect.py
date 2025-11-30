"""
🔍 EMERGENCY RESPONSE SYSTEM - COMPLETE DIAGNOSTIC TOOL
This script inspects your entire system and identifies all problems
"""

import os
import sys
import re
from pathlib import Path
import importlib.util

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# ============================================================================
# INSPECTION FUNCTIONS
# ============================================================================

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_success(f"{description} exists: {filepath}")
        return True
    else:
        print_error(f"{description} NOT FOUND: {filepath}")
        return False

def check_python_imports(filepath):
    """Check if a Python file has correct imports"""
    if not os.path.exists(filepath):
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for common imports
        required_imports = {
            'requests.py': ['from app.database.postgis import db', 'from app.services.distance_calculator import'],
            'postgis.py': ['from contextlib import contextmanager', 'class PostGISDatabase'],
            'distance_calculator.py': ['async def calculate_distance_and_eta'],
        }
        
        filename = os.path.basename(filepath)
        if filename in required_imports:
            all_found = True
            for import_str in required_imports[filename]:
                if import_str in content:
                    print_success(f"  Import found: {import_str[:50]}...")
                else:
                    print_error(f"  Import MISSING: {import_str}")
                    all_found = False
            return all_found
        return True
    except Exception as e:
        print_error(f"  Error reading file: {e}")
        return False

def check_database_functions(filepath):
    """Check if postgis.py has all required functions"""
    if not os.path.exists(filepath):
        return {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = {
            'count_refusals': 'def count_refusals',
            'count_available_services': 'def count_available_services',
            'get_recent_accepts': 'def get_recent_accepts',
            'mark_response_canceled': 'def mark_response_canceled',
            'record_service_response': 'def record_service_response',
            'get_service_by_id': 'def get_service_by_id',
            'create_emergency_request': 'def create_emergency_request',
            'get_request_by_id': 'def get_request_by_id',
        }
        
        results = {}
        for func_name, func_signature in required_functions.items():
            if func_signature in content:
                # Check if it's a class method (indented) or standalone
                class_method_pattern = f"    {func_signature}"
                standalone_pattern = f"^{func_signature}"
                
                is_class_method = class_method_pattern in content
                is_standalone = re.search(standalone_pattern, content, re.MULTILINE)
                
                if is_class_method:
                    results[func_name] = 'class_method'
                    print_success(f"  {func_name}: Found as CLASS METHOD ✅")
                elif is_standalone:
                    results[func_name] = 'standalone'
                    print_warning(f"  {func_name}: Found as STANDALONE (may cause AttributeError)")
                else:
                    results[func_name] = 'unknown'
            else:
                results[func_name] = 'missing'
                print_error(f"  {func_name}: NOT FOUND")
        
        return results
    except Exception as e:
        print_error(f"  Error analyzing file: {e}")
        return {}

def check_function_calls(filepath, function_name):
    """Check how a function is being called in a file"""
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for different call patterns
        patterns = [
            (f"db.{function_name}\\(", 'class_method'),
            (f"{function_name}\\(", 'standalone'),
        ]
        
        calls = []
        for pattern, call_type in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Get line number
                line_num = content[:match.start()].count('\n') + 1
                calls.append({
                    'line': line_num,
                    'type': call_type,
                    'pattern': pattern
                })
        
        return calls
    except Exception as e:
        print_error(f"  Error analyzing calls: {e}")
        return []

def check_record_service_response_calls(filepath):
    """Check how record_service_response is called"""
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        in_call = False
        call_start = 0
        call_lines = []
        
        for i, line in enumerate(lines, 1):
            if 'db.record_service_response({' in line or 'record_service_response({' in line:
                in_call = True
                call_start = i
                call_lines = [line]
            elif in_call:
                call_lines.append(line)
                if '})' in line:
                    # End of call, analyze it
                    call_text = ''.join(call_lines)
                    
                    # Check for required fields
                    has_request_id = 'request_id' in call_text
                    has_service_id = 'service_id' in call_text
                    has_response_type = 'response_type' in call_text
                    has_notes = 'notes' in call_text or '"notes"' in call_text
                    
                    if not has_notes:
                        issues.append({
                            'line': call_start,
                            'issue': 'Missing "notes" field (may cause KeyError)',
                            'has_request_id': has_request_id,
                            'has_service_id': has_service_id,
                            'has_response_type': has_response_type
                        })
                    
                    in_call = False
                    call_lines = []
        
        return issues
    except Exception as e:
        print_error(f"  Error checking calls: {e}")
        return []

def check_database_structure():
    """Check if database tables exist"""
    print_info("To check database tables, run this SQL in pgAdmin:")
    print("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """)
    print_info("Required tables: service_providers, emergency_requests, service_responses")

def inspect_system():
    """Main inspection function"""
    
    print_header("🔍 EMERGENCY RESPONSE SYSTEM DIAGNOSTIC")
    
    # Base directory
    base_dir = Path("3_BACKEND")
    if not base_dir.exists():
        base_dir = Path(".")
    
    # ========================================================================
    # STEP 1: Check File Structure
    # ========================================================================
    print_header("STEP 1: File Structure")
    
    files_to_check = {
        'requests.py': base_dir / 'app' / 'routers' / 'requests.py',
        'postgis.py': base_dir / 'app' / 'database' / 'postgis.py',
        'distance_calculator.py': base_dir / 'app' / 'services' / 'distance_calculator.py',
        'main.py': base_dir / 'app' / 'main.py',
        'config.py': base_dir / 'app' / 'config.py',
        '.env': base_dir / '.env',
    }
    
    existing_files = {}
    for name, filepath in files_to_check.items():
        exists = check_file_exists(filepath, name)
        if exists:
            existing_files[name] = filepath
    
    # ========================================================================
    # STEP 2: Check Database Functions
    # ========================================================================
    print_header("STEP 2: Database Functions (postgis.py)")
    
    if 'postgis.py' in existing_files:
        func_status = check_database_functions(existing_files['postgis.py'])
        
        # Check for critical issues
        critical_funcs = ['count_refusals', 'count_available_services', 'get_recent_accepts', 'mark_response_canceled']
        has_issues = False
        
        for func in critical_funcs:
            if func not in func_status or func_status[func] == 'missing':
                print_error(f"\n🚨 CRITICAL: {func} is MISSING!")
                has_issues = True
            elif func_status[func] == 'standalone':
                print_warning(f"\n⚠️  WARNING: {func} is STANDALONE (should be class method)")
                print_info(f"   This will cause: AttributeError: 'PostGISDatabase' object has no attribute '{func}'")
                has_issues = True
        
        if not has_issues:
            print_success("\n✅ All critical functions are present and correctly defined as class methods!")
    
    # ========================================================================
    # STEP 3: Check Function Calls
    # ========================================================================
    print_header("STEP 3: Function Calls (requests.py)")
    
    if 'requests.py' in existing_files:
        critical_funcs = ['count_refusals', 'count_available_services', 'get_recent_accepts', 'mark_response_canceled']
        
        for func in critical_funcs:
            calls = check_function_calls(existing_files['requests.py'], func)
            if calls:
                print_info(f"\n{func} is called {len(calls)} time(s):")
                for call in calls:
                    if call['type'] == 'class_method':
                        print_success(f"  Line {call['line']}: db.{func}() ✅")
                    else:
                        print_warning(f"  Line {call['line']}: {func}() (standalone)")
            else:
                print_warning(f"  {func}: Not called in requests.py")
    
    # ========================================================================
    # STEP 4: Check record_service_response Calls
    # ========================================================================
    print_header("STEP 4: record_service_response Calls")
    
    if 'requests.py' in existing_files:
        issues = check_record_service_response_calls(existing_files['requests.py'])
        if issues:
            print_error(f"\nFound {len(issues)} potential issue(s):")
            for issue in issues:
                print_error(f"  Line {issue['line']}: {issue['issue']}")
                print_info(f"    Fields present: request_id={issue['has_request_id']}, "
                          f"service_id={issue['has_service_id']}, "
                          f"response_type={issue['has_response_type']}")
        else:
            print_success("\nNo issues found in record_service_response calls")
    
    # ========================================================================
    # STEP 5: Check Distance Calculator
    # ========================================================================
    print_header("STEP 5: Distance Calculator")
    
    if 'distance_calculator.py' in existing_files:
        check_python_imports(existing_files['distance_calculator.py'])
        
        with open(existing_files['distance_calculator.py'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'async def calculate_distance_and_eta' in content:
            print_success("calculate_distance_and_eta function found (async)")
        else:
            print_error("calculate_distance_and_eta function not found or not async")
        
        if 'calculate_route_osrm' in content:
            print_success("OSRM routing function found")
        else:
            print_warning("OSRM routing function not found")
    
    # ========================================================================
    # STEP 6: Summary and Recommendations
    # ========================================================================
    print_header("SUMMARY AND RECOMMENDATIONS")
    
    # Collect all issues
    all_issues = []
    
    # Check for missing files
    for name, filepath in files_to_check.items():
        if name not in existing_files:
            all_issues.append(f"Missing file: {name}")
    
    # Check function definitions
    if 'postgis.py' in existing_files:
        func_status = check_database_functions(existing_files['postgis.py'])
        for func in ['count_refusals', 'count_available_services', 'get_recent_accepts', 'mark_response_canceled']:
            if func not in func_status or func_status[func] == 'missing':
                all_issues.append(f"Missing function: {func} in postgis.py")
            elif func_status[func] == 'standalone':
                all_issues.append(f"Function {func} is standalone (should be class method)")
    
    # Print summary
    if all_issues:
        print_error(f"\n🚨 FOUND {len(all_issues)} ISSUE(S):")
        for i, issue in enumerate(all_issues, 1):
            print_error(f"  {i}. {issue}")
        
        print("\n" + "="*70)
        print_warning("RECOMMENDED FIX:")
        print_info("Download and replace postgis.py from:")
        print_info("  /mnt/user-data/outputs/postgis_fixed.py")
        print_info("\nThis file contains:")
        print_info("  ✅ All functions as class methods")
        print_info("  ✅ Fixed record_service_response with default values")
        print_info("  ✅ All FIFO logic functions")
        print("="*70)
    else:
        print_success("\n🎉 NO CRITICAL ISSUES FOUND!")
        print_success("Your system should be working correctly.")
    
    # ========================================================================
    # STEP 7: Database Check Reminder
    # ========================================================================
    print_header("STEP 7: Database Tables Check")
    check_database_structure()
    
    print("\n" + "="*70)
    print_header("🔍 DIAGNOSTIC COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        inspect_system()
    except KeyboardInterrupt:
        print("\n\nInspection cancelled by user.")
    except Exception as e:
        print_error(f"\n\nUnexpected error during inspection: {e}")
        import traceback
        traceback.print_exc()