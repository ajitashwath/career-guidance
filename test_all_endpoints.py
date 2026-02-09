"""
Comprehensive API Endpoint Testing Script for Career Intelligence Backend

This script tests all endpoints including:
- System endpoints (health, root)
- Student endpoints (profile, skills, education, experience, projects, certifications)
- Event endpoints
- AI endpoints (with OpenRouter)
- Recruiter endpoints
- Admin endpoints

Requirements:
- Set up .env with valid credentials including OPENROUTER_API_KEY
- Have a test user token
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
# You need to get these from Supabase Auth
STUDENT_TOKEN = os.getenv("TEST_STUDENT_TOKEN", "")
RECRUITER_TOKEN = os.getenv("TEST_RECRUITER_TOKEN", "")
ADMIN_TOKEN = os.getenv("TEST_ADMIN_TOKEN", "")

# Colors for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class EndpointTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "tests": []
        }
        self.test_data = {}  # Store created resource IDs for cleanup/testing
    
    def log_test(self, endpoint: str, method: str, status: str, message: str = "", response_data: any = None):
        """Log test result"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "message": message,
            "response": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.results["tests"].append(result)
        
        if status == "PASS":
            self.results["passed"] += 1
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} {method} {endpoint}: {Colors.OKGREEN}{message}{Colors.ENDC}")
        elif status == "FAIL":
            self.results["failed"] += 1
            print(f"{Colors.FAIL}✗{Colors.ENDC} {method} {endpoint}: {Colors.FAIL}{message}{Colors.ENDC}")
        elif status == "SKIP":
            self.results["skipped"] += 1
            print(f"{Colors.WARNING}⊘{Colors.ENDC} {method} {endpoint}: {Colors.WARNING}{message}{Colors.ENDC}")
    
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title.center(80)}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
    
    async def make_request(self, method: str, endpoint: str, token: Optional[str] = None, json_data: Optional[dict] = None, params: Optional[dict] = None):
        """Make HTTP request"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    response = await client.get(f"{self.base_url}{endpoint}", headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(f"{self.base_url}{endpoint}", headers=headers, json=json_data)
                elif method == "PATCH":
                    response = await client.patch(f"{self.base_url}{endpoint}", headers=headers, json=json_data)
                elif method == "PUT":
                    response = await client.put(f"{self.base_url}{endpoint}", headers=headers, json=json_data)
                elif method == "DELETE":
                    response = await client.delete(f"{self.base_url}{endpoint}", headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                return response
            except Exception as e:
                return {"error": str(e)}
    
    # =========================================================================
    # System Endpoints
    # =========================================================================
    
    async def test_system_endpoints(self):
        """Test system health and root endpoints"""
        self.print_section("System Endpoints")
        
        # Test health check
        response = await self.make_request("GET", "/health")
        if isinstance(response, dict) and "error" in response:
            self.log_test("/health", "GET", "FAIL", f"Request failed: {response['error']}")
        elif response.status_code == 200:
            self.log_test("/health", "GET", "PASS", f"Status: {response.json()['status']}", response.json())
        else:
            self.log_test("/health", "GET", "FAIL", f"Status code: {response.status_code}")
        
        # Test root
        response = await self.make_request("GET", "/")
        if isinstance(response, dict) and "error" in response:
            self.log_test("/", "GET", "FAIL", f"Request failed: {response['error']}")
        elif response.status_code == 200:
            data = response.json()
            self.log_test("/", "GET", "PASS", f"Name: {data.get('name')}, Version: {data.get('version')}", data)
        else:
            self.log_test("/", "GET", "FAIL", f"Status code: {response.status_code}")
    
    # =========================================================================
    # Student Endpoints
    # =========================================================================
    
    async def test_student_endpoints(self, token: str):
        """Test all student endpoints"""
        if not token:
            self.print_section("Student Endpoints")
            self.log_test("/students/*", "ALL", "SKIP", "No student token provided")
            return
        
        self.print_section("Student Endpoints - Profile")
        
        # Get profile
        response = await self.make_request("GET", "/students/me", token)
        if isinstance(response, dict) and "error" in response:
            self.log_test("/students/me", "GET", "FAIL", f"Request failed: {response['error']}")
        elif response.status_code == 200:
            self.log_test("/students/me", "GET", "PASS", "Profile retrieved successfully", response.json())
        else:
            self.log_test("/students/me", "GET", "FAIL", f"Status code: {response.status_code}, {response.text}")
        
        # Update profile
        update_data = {
            "bio": f"Updated bio at {datetime.now().isoformat()}",
            "target_roles": ["Software Engineer", "Full Stack Developer"]
        }
        response = await self.make_request("PATCH", "/students/me", token, update_data)
        if isinstance(response, dict) and "error" in response:
            self.log_test("/students/me", "PATCH", "FAIL", f"Request failed: {response['error']}")
        elif response.status_code == 200:
            self.log_test("/students/me", "PATCH", "PASS", "Profile updated successfully", response.json())
        else:
            self.log_test("/students/me", "PATCH", "FAIL", f"Status code: {response.status_code}, {response.text}")
        
        # Test Skills
        await self.test_student_skills(token)
        
        # Test Education
        await self.test_student_education(token)
        
        # Test Experience
        await self.test_student_experience(token)
        
        # Test Projects
        await self.test_student_projects(token)
        
        # Test Certifications
        await self.test_student_certifications(token)
    
    async def test_student_skills(self, token: str):
        """Test student skills endpoints"""
        self.print_section("Student Endpoints - Skills")
        
        # Get skills
        response = await self.make_request("GET", "/students/me/skills", token)
        if response.status_code == 200:
            self.log_test("/students/me/skills", "GET", "PASS", f"Retrieved {len(response.json())} skills")
        else:
            self.log_test("/students/me/skills", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Add skill
        skill_data = {
            "skill_name": "Python",
            "proficiency_level": 4,
            "years_of_experience": 3
        }
        response = await self.make_request("POST", "/students/me/skills", token, skill_data)
        if response.status_code == 201:
            skill_id = response.json().get("id")
            self.test_data["skill_id"] = skill_id
            self.log_test("/students/me/skills", "POST", "PASS", f"Skill added with ID: {skill_id}", response.json())
            
            # Update skill
            if skill_id:
                update_data = {"proficiency_level": 5}
                response = await self.make_request("PATCH", f"/students/me/skills/{skill_id}", token, update_data)
                if response.status_code == 200:
                    self.log_test(f"/students/me/skills/{skill_id}", "PATCH", "PASS", "Skill updated")
                else:
                    self.log_test(f"/students/me/skills/{skill_id}", "PATCH", "FAIL", f"Status: {response.status_code}")
                
                # Delete skill
                response = await self.make_request("DELETE", f"/students/me/skills/{skill_id}", token)
                if response.status_code == 204:
                    self.log_test(f"/students/me/skills/{skill_id}", "DELETE", "PASS", "Skill deleted")
                else:
                    self.log_test(f"/students/me/skills/{skill_id}", "DELETE", "FAIL", f"Status: {response.status_code}")
        else:
            self.log_test("/students/me/skills", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    async def test_student_education(self, token: str):
        """Test student education endpoints"""
        self.print_section("Student Endpoints - Education")
        
        # Get education
        response = await self.make_request("GET", "/students/me/education", token)
        if response.status_code == 200:
            self.log_test("/students/me/education", "GET", "PASS", f"Retrieved {len(response.json())} education entries")
        else:
            self.log_test("/students/me/education", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Add education
        education_data = {
            "institution_name": "Test University",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "start_date": "2020-09-01",
            "is_current": False,
            "end_date": "2024-05-01"
        }
        response = await self.make_request("POST", "/students/me/education", token, education_data)
        if response.status_code == 201:
            edu_id = response.json().get("id")
            self.test_data["education_id"] = edu_id
            self.log_test("/students/me/education", "POST", "PASS", f"Education added with ID: {edu_id}")
        else:
            self.log_test("/students/me/education", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    async def test_student_experience(self, token: str):
        """Test student experience endpoints"""
        self.print_section("Student Endpoints - Experience")
        
        # Get experience
        response = await self.make_request("GET", "/students/me/experience", token)
        if response.status_code == 200:
            self.log_test("/students/me/experience", "GET", "PASS", f"Retrieved {len(response.json())} experience entries")
        else:
            self.log_test("/students/me/experience", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Add experience
        experience_data = {
            "company_name": "Test Company",
            "position_title": "Software Engineer Intern",
            "employment_type": "Internship",
            "start_date": "2023-06-01",
            "is_current": False,
            "end_date": "2023-08-31",
            "description": "Worked on backend APIs and database optimization"
        }
        response = await self.make_request("POST", "/students/me/experience", token, experience_data)
        if response.status_code == 201:
            exp_id = response.json().get("id")
            self.test_data["experience_id"] = exp_id
            self.log_test("/students/me/experience", "POST", "PASS", f"Experience added with ID: {exp_id}")
        else:
            self.log_test("/students/me/experience", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    async def test_student_projects(self, token: str):
        """Test student projects endpoints"""
        self.print_section("Student Endpoints - Projects")
        
        # Get projects
        response = await self.make_request("GET", "/students/me/projects", token)
        if response.status_code == 200:
            self.log_test("/students/me/projects", "GET", "PASS", f"Retrieved {len(response.json())} projects")
        else:
            self.log_test("/students/me/projects", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Add project
        project_data = {
            "project_name": "AI Career Intelligence Platform",
            "description": "Full-stack application for career guidance using AI",
            "technologies_used": ["Python", "FastAPI", "React", "Supabase"],
            "project_url": "https://github.com/test/career-platform",
            "start_date": "2024-01-01",
            "is_ongoing": False,
            "end_date": "2024-06-01"
        }
        response = await self.make_request("POST", "/students/me/projects", token, project_data)
        if response.status_code == 201:
            project_id = response.json().get("id")
            self.test_data["project_id"] = project_id
            self.log_test("/students/me/projects", "POST", "PASS", f"Project added with ID: {project_id}")
        else:
            self.log_test("/students/me/projects", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    async def test_student_certifications(self, token: str):
        """Test student certifications endpoints"""
        self.print_section("Student Endpoints - Certifications")
        
        # Get certifications
        response = await self.make_request("GET", "/students/me/certifications", token)
        if response.status_code == 200:
            self.log_test("/students/me/certifications", "GET", "PASS", f"Retrieved {len(response.json())} certifications")
        else:
            self.log_test("/students/me/certifications", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Add certification
        cert_data = {
            "certification_name": "AWS Certified Developer",
            "issuing_organization": "Amazon Web Services",
            "issue_date": "2024-01-15",
            "expiration_date": "2027-01-15",
            "credential_id": "AWS-12345",
            "credential_url": "https://aws.amazon.com/certification/verify"
        }
        response = await self.make_request("POST", "/students/me/certifications", token, cert_data)
        if response.status_code == 201:
            cert_id = response.json().get("id")
            self.test_data["certification_id"] = cert_id
            self.log_test("/students/me/certifications", "POST", "PASS", f"Certification added with ID: {cert_id}")
        else:
            self.log_test("/students/me/certifications", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    # =========================================================================
    # Event Endpoints
    # =========================================================================
    
    async def test_event_endpoints(self, token: str):
        """Test event endpoints"""
        if not token:
            self.print_section("Event Endpoints")
            self.log_test("/events/*", "ALL", "SKIP", "No student token provided")
            return
        
        self.print_section("Event Endpoints")
        
        # List event types
        response = await self.make_request("GET", "/events/types")
        if response.status_code == 200:
            data = response.json()
            total_types = sum(len(v) for v in data.values() if isinstance(v, list))
            self.log_test("/events/types", "GET", "PASS", f"Retrieved {total_types} event types", data)
        else:
            self.log_test("/events/types", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Emit event
        event_data = {
            "event_type": "profile_updated",
            "event_payload": {
                "field": "bio",
                "action": "update",
                "timestamp": datetime.now().isoformat()
            }
        }
        response = await self.make_request("POST", "/events", token, event_data)
        if response.status_code == 201:
            self.log_test("/events", "POST", "PASS", "Event emitted successfully", response.json())
        else:
            self.log_test("/events", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    # =========================================================================
    # AI Endpoints (with OpenRouter)
    # =========================================================================
    
    async def test_ai_endpoints(self, token: str):
        """Test AI endpoints using OpenRouter"""
        if not token:
            self.print_section("AI Endpoints (OpenRouter)")
            self.log_test("/ai/*", "ALL", "SKIP", "No student token provided")
            return
        
        self.print_section("AI Endpoints (OpenRouter)")
        
        # Profile analysis
        print(f"\n{Colors.OKCYAN}Testing AI Profile Analysis...{Colors.ENDC}")
        response = await self.make_request("GET", "/ai/profile-analysis", token)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/ai/profile-analysis", "GET", "PASS", f"Analysis completed", data)
        else:
            self.log_test("/ai/profile-analysis", "GET", "FAIL", f"Status: {response.status_code}, {response.text}")
        
        # Career advice
        print(f"\n{Colors.OKCYAN}Testing AI Career Advice...{Colors.ENDC}")
        advice_request = {
            "question": "What skills should I focus on to become a senior software engineer?"
        }
        response = await self.make_request("POST", "/ai/career-advice", token, advice_request)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/ai/career-advice", "POST", "PASS", "Advice generated", data)
        else:
            self.log_test("/ai/career-advice", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
        
        # Interview prep
        print(f"\n{Colors.OKCYAN}Testing AI Interview Preparation...{Colors.ENDC}")
        interview_request = {
            "target_role": "Senior Backend Engineer"
        }
        response = await self.make_request("POST", "/ai/interview-prep", token, interview_request)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/ai/interview-prep", "POST", "PASS", "Interview questions generated", data)
        else:
            self.log_test("/ai/interview-prep", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
        
        # Skill gaps
        print(f"\n{Colors.OKCYAN}Testing AI Skill Gap Analysis...{Colors.ENDC}")
        skill_gap_request = {
            "target_role": "Machine Learning Engineer"
        }
        response = await self.make_request("POST", "/ai/skill-gaps", token, skill_gap_request)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/ai/skill-gaps", "POST", "PASS", "Skill gap analysis completed", data)
        else:
            self.log_test("/ai/skill-gaps", "POST", "FAIL", f"Status: {response.status_code}, {response.text}")
        
        # Resume suggestions
        print(f"\n{Colors.OKCYAN}Testing AI Resume Suggestions...{Colors.ENDC}")
        response = await self.make_request("GET", "/ai/resume-suggestions", token)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/ai/resume-suggestions", "GET", "PASS", "Resume suggestions generated", data)
        else:
            self.log_test("/ai/resume-suggestions", "GET", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    # =========================================================================
    # Recruiter Endpoints
    # =========================================================================
    
    async def test_recruiter_endpoints(self, token: str):
        """Test recruiter endpoints"""
        if not token:
            self.print_section("Recruiter Endpoints")
            self.log_test("/recruiters/*", "ALL", "SKIP", "No recruiter token provided")
            return
        
        self.print_section("Recruiter Endpoints")
        
        # Search candidates
        response = await self.make_request("GET", "/recruiters/candidates", token, params={"page": 1, "page_size": 10})
        if response.status_code == 200:
            data = response.json()
            self.log_test("/recruiters/candidates", "GET", "PASS", f"Found {data.get('total_count', 0)} candidates")
            
            # If we have candidates, test individual views
            if data.get("candidates") and len(data["candidates"]) > 0:
                candidate_id = data["candidates"][0].get("id")
                if candidate_id:
                    self.test_data["candidate_id"] = candidate_id
                    
                    # Get candidate profile
                    response = await self.make_request("GET", f"/recruiters/candidates/{candidate_id}", token)
                    if response.status_code == 200:
                        self.log_test(f"/recruiters/candidates/{candidate_id}", "GET", "PASS", "Candidate profile retrieved")
                    else:
                        self.log_test(f"/recruiters/candidates/{candidate_id}", "GET", "FAIL", f"Status: {response.status_code}")
                    
                    # Get intelligence summary
                    response = await self.make_request("GET", f"/recruiters/candidates/{candidate_id}/summary", token)
                    if response.status_code == 200:
                        self.log_test(f"/recruiters/candidates/{candidate_id}/summary", "GET", "PASS", "Intelligence summary retrieved")
                    else:
                        self.log_test(f"/recruiters/candidates/{candidate_id}/summary", "GET", "FAIL", f"Status: {response.status_code}")
                    
                    # Get timeline
                    response = await self.make_request("GET", f"/recruiters/candidates/{candidate_id}/timeline", token, params={"days": 30})
                    if response.status_code == 200:
                        self.log_test(f"/recruiters/candidates/{candidate_id}/timeline", "GET", "PASS", "Timeline retrieved")
                    else:
                        self.log_test(f"/recruiters/candidates/{candidate_id}/timeline", "GET", "FAIL", f"Status: {response.status_code}")
        else:
            self.log_test("/recruiters/candidates", "GET", "FAIL", f"Status: {response.status_code}, {response.text}")
    
    # =========================================================================
    # Admin Endpoints
    # =========================================================================
    
    async def test_admin_endpoints(self, token: str, user_id: Optional[str] = None):
        """Test admin endpoints"""
        if not token:
            self.print_section("Admin Endpoints")
            self.log_test("/admin/*", "ALL", "SKIP", "No admin token provided")
            return
        
        self.print_section("Admin Endpoints")
        
        # Get scoring version
        response = await self.make_request("GET", "/admin/scoring/version", token)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/admin/scoring/version", "GET", "PASS", f"Version: {data.get('current_version')}", data)
        else:
            self.log_test("/admin/scoring/version", "GET", "FAIL", f"Status: {response.status_code}")
        
        # Get system stats
        response = await self.make_request("GET", "/admin/system/stats", token)
        if response.status_code == 200:
            data = response.json()
            self.log_test("/admin/system/stats", "GET", "PASS", "System stats retrieved", data)
        else:
            self.log_test("/admin/system/stats", "GET", "FAIL", f"Status: {response.status_code}")
        
        # User-specific endpoints (if user_id provided)
        if user_id:
            # Get raw events
            response = await self.make_request("GET", f"/admin/users/{user_id}/events", token, params={"limit": 10})
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"/admin/users/{user_id}/events", "GET", "PASS", f"Retrieved {data.get('total_count', 0)} events")
            else:
                self.log_test(f"/admin/users/{user_id}/events", "GET", "FAIL", f"Status: {response.status_code}")
            
            # Get scoring debug
            response = await self.make_request("GET", f"/admin/scoring/debug/{user_id}", token)
            if response.status_code == 200:
                self.log_test(f"/admin/scoring/debug/{user_id}", "GET", "PASS", "Scoring debug retrieved")
            else:
                self.log_test(f"/admin/scoring/debug/{user_id}", "GET", "FAIL", f"Status: {response.status_code}")
            
            # Force recompute
            response = await self.make_request("POST", f"/admin/users/{user_id}/recompute", token)
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"/admin/users/{user_id}/recompute", "POST", "PASS", f"Recompute: {data.get('message')}")
            else:
                self.log_test(f"/admin/users/{user_id}/recompute", "POST", "FAIL", f"Status: {response.status_code}")
    
    # =========================================================================
    # Main Test Runner
    # =========================================================================
    
    async def run_all_tests(self):
        """Run all test suites"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "Career Intelligence API - Comprehensive Endpoint Testing".center(78) + "║")
        print("║" + f"Base URL: {self.base_url}".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╚" + "═" * 78 + "╝")
        print(f"{Colors.ENDC}\n")
        
        # System tests (no auth required)
        await self.test_system_endpoints()
        
        # Student tests
        await self.test_student_endpoints(STUDENT_TOKEN)
        
        # Event tests
        await self.test_event_endpoints(STUDENT_TOKEN)
        
        # AI tests (with OpenRouter)
        await self.test_ai_endpoints(STUDENT_TOKEN)
        
        # Recruiter tests
        await self.test_recruiter_endpoints(RECRUITER_TOKEN)
        
        # Admin tests
        await self.test_admin_endpoints(ADMIN_TOKEN)
        
        # Print summary
        self.print_summary()
        
        # Save detailed report
        self.save_report()
    
    def print_summary(self):
        """Print test summary"""
        total = self.results["passed"] + self.results["failed"] + self.results["skipped"]
        
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 78 + "║")
        print("║" + "TEST SUMMARY".center(78) + "║")
        print("║" + " " * 78 + "║")
        print("╠" + "═" * 78 + "╣")
        print(f"║  Total Tests:    {str(total).ljust(60)} ║")
        print(f"║  {Colors.OKGREEN}✓ Passed:       {str(self.results['passed']).ljust(60)}{Colors.HEADER} ║")
        print(f"║  {Colors.FAIL}✗ Failed:       {str(self.results['failed']).ljust(60)}{Colors.HEADER} ║")
        print(f"║  {Colors.WARNING}⊘ Skipped:      {str(self.results['skipped']).ljust(60)}{Colors.HEADER} ║")
        print("║" + " " * 78 + "║")
        
        if self.results["passed"] > 0:
            pass_rate = (self.results["passed"] / (total - self.results["skipped"])) * 100 if total > self.results["skipped"] else 0
            print(f"║  Pass Rate:      {pass_rate:.1f}%".ljust(79) + " ║")
        
        print("╚" + "═" * 78 + "╝")
        print(f"{Colors.ENDC}\n")
    
    def save_report(self):
        """Save detailed test report to file"""
        report_path = "test_report.json"
        with open(report_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"{Colors.OKCYAN}Detailed test report saved to: {report_path}{Colors.ENDC}\n")


async def main():
    """Main entry point"""
    # Check if server is running
    print(f"{Colors.OKCYAN}Checking server availability...{Colors.ENDC}")
    
    tester = EndpointTester(BASE_URL)
    
    # Check tokens
    print(f"\n{Colors.BOLD}Token Status:{Colors.ENDC}")
    print(f"  Student Token:   {'✓ Provided' if STUDENT_TOKEN else '✗ Missing'}")
    print(f"  Recruiter Token: {'✓ Provided' if RECRUITER_TOKEN else '✗ Missing'}")
    print(f"  Admin Token:     {'✓ Provided' if ADMIN_TOKEN else '✗ Missing'}")
    
    if not STUDENT_TOKEN:
        print(f"\n{Colors.WARNING}Warning: Some tests will be skipped without proper tokens.{Colors.ENDC}")
        print(f"{Colors.WARNING}Set TEST_STUDENT_TOKEN, TEST_RECRUITER_TOKEN, and TEST_ADMIN_TOKEN in .env{Colors.ENDC}\n")
    
    # Run tests
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
