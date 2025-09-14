#!/usr/bin/env python3
"""
Test script for the Orch service
Tests both V1 and V2 API endpoints
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class OrchServiceTester:
    """Test suite for the Orch service"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
    
    def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Health Check", True, "Service is healthy")
                    return True
                else:
                    self.log_test("Health Check", False, f"Service unhealthy: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_v2_health_check(self) -> bool:
        """Test V2 health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v2/status/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("V2 Health Check", True, "V2 service is healthy")
                    return True
                else:
                    self.log_test("V2 Health Check", False, f"V2 service unhealthy: {data}")
                    return False
            else:
                self.log_test("V2 Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("V2 Health Check", False, str(e))
            return False
    
    def test_api_documentation(self) -> bool:
        """Test API documentation endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v2/docs/")
            if response.status_code == 200:
                data = response.json()
                if 'endpoints' in data and 'resource' in data['endpoints']:
                    self.log_test("API Documentation", True, "Documentation available")
                    return True
                else:
                    self.log_test("API Documentation", False, "Invalid documentation format")
                    return False
            else:
                self.log_test("API Documentation", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Documentation", False, str(e))
            return False
    
    def test_resource_mappings(self) -> bool:
        """Test resource mappings endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v2/status/mappings")
            if response.status_code == 200:
                data = response.json()
                if 'mappings' in data:
                    mappings = data['mappings']
                    self.log_test("Resource Mappings", True, f"Found {len(mappings)} mappings")
                    return True
                else:
                    self.log_test("Resource Mappings", False, "No mappings in response")
                    return False
            else:
                self.log_test("Resource Mappings", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Resource Mappings", False, str(e))
            return False
    
    def test_invalid_uuid_validation(self) -> bool:
        """Test UUID validation with invalid UUID"""
        try:
            invalid_uuid = "invalid-uuid-format"
            response = self.session.post(f"{self.base_url}/api/v2/resource/{invalid_uuid}")
            if response.status_code == 400:
                data = response.json()
                if 'error' in data and 'VALIDATION_ERROR' in data['error'].get('code', ''):
                    self.log_test("Invalid UUID Validation", True, "Properly rejected invalid UUID")
                    return True
                else:
                    self.log_test("Invalid UUID Validation", False, f"Unexpected error format: {data}")
                    return False
            else:
                self.log_test("Invalid UUID Validation", False, f"Expected 400, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Invalid UUID Validation", False, str(e))
            return False
    
    def test_nonexistent_resource(self) -> bool:
        """Test accessing non-existent resource"""
        try:
            fake_uuid = "00000000-0000-0000-0000-000000000000"
            response = self.session.post(f"{self.base_url}/api/v2/resource/{fake_uuid}")
            if response.status_code == 404:
                data = response.json()
                if 'error' in data and 'RESOURCE_NOT_FOUND' in data['error'].get('code', ''):
                    self.log_test("Non-existent Resource", True, "Properly handled non-existent resource")
                    return True
                else:
                    self.log_test("Non-existent Resource", False, f"Unexpected error format: {data}")
                    return False
            else:
                self.log_test("Non-existent Resource", False, f"Expected 404, got {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Non-existent Resource", False, str(e))
            return False
    
    def test_v1_backward_compatibility(self) -> bool:
        """Test V1 API backward compatibility"""
        try:
            # Test V1 principal endpoint
            response = self.session.get(f"{self.base_url}/api/v1/principal/test@KOJI.BOX")
            if response.status_code == 200:
                self.log_test("V1 Principal API", True, "V1 principal endpoint working")
                return True
            else:
                self.log_test("V1 Principal API", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("V1 Principal API", False, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print("Starting Orch Service Test Suite...")
        print("=" * 50)
        
        tests = [
            self.test_health_check,
            self.test_v2_health_check,
            self.test_api_documentation,
            self.test_resource_mappings,
            self.test_invalid_uuid_validation,
            self.test_nonexistent_resource,
            self.test_v1_backward_compatibility
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print("=" * 50)
        print(f"Test Results: {passed}/{total} tests passed")
        
        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'results': self.test_results
        }

def main():
    """Main test function"""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    tester = OrchServiceTester(base_url)
    results = tester.run_all_tests()
    
    if results['failed'] > 0:
        print(f"\n{results['failed']} tests failed!")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()

# The end.
