#!/usr/bin/env python3
"""
Script to create Linear tasks for the Data Broker Removal Agent implementation plan.
"""

import os
import requests
import json
from typing import Dict, List, Optional

class LinearTaskCreator:
    def __init__(self, api_key: str, team_id: str):
        self.api_key = api_key
        self.team_id = team_id
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def create_task(self, title: str, description: str, priority: int = 3, estimate: Optional[int] = None) -> Dict:
        """Create a Linear task using GraphQL API"""
        
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    title
                    identifier
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "teamId": self.team_id,
                "title": title,
                "description": description,
                "priority": priority
            }
        }
        
        if estimate:
            variables["input"]["estimate"] = estimate
            
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": mutation, "variables": variables}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data", {}).get("issueCreate", {}).get("success"):
                return result["data"]["issueCreate"]["issue"]
            else:
                print(f"Error creating task: {result}")
                return {}
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return {}

    def create_epic(self, title: str, description: str) -> Dict:
        """Create a Linear project/epic"""
        
        mutation = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "teamIds": [self.team_id],
                "name": title,
                "description": description
            }
        }
        
        response = requests.post(
            self.base_url,
            headers=self.headers,
            json={"query": mutation, "variables": variables}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("data", {}).get("projectCreate", {}).get("success"):
                return result["data"]["projectCreate"]["project"]
            else:
                print(f"Error creating epic: {result}")
                return {}
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return {}

def get_phase_tasks() -> List[Dict]:
    """Define all tasks to be created in Linear"""
    
    tasks = [
        # Phase 1: Foundation Setup
        {
            "title": "Phase 1: Foundation Setup - Infrastructure",
            "description": """**Infrastructure Setup Tasks:**
- Set up Python development environment with Poetry/pipenv
- Create Supabase project and configure database
- Configure email service provider account (Mailgun/SendGrid)
- Set up monitoring infrastructure (Prometheus/Grafana)
- Set up Linear workspace for internal development tracking

**Acceptance Criteria:**
- Development environment is fully configured
- Supabase project is created and accessible
- Email service is configured and tested
- Basic monitoring is in place
- All team members have access to development tools""",
            "priority": 1,
            "estimate": 8
        },
        {
            "title": "Phase 1: Database Design & Core Framework",
            "description": """**Database Design & Framework Setup:**
- Design all database schemas (Users, Data Brokers, Patterns, Requests, etc.)
- Implement Row Level Security (RLS) policies
- Create database indexes for performance optimization
- Install and configure LangGraph
- Set up base agent structure
- Configure LLM provider (OpenAI/Anthropic)
- Create basic FastAPI application structure
- Set up authentication and authorization

**Acceptance Criteria:**
- All database tables are created with proper schemas
- RLS policies are implemented and tested
- Core framework is operational
- Authentication system is working
- Basic API structure is in place""",
            "priority": 1,
            "estimate": 13
        },
        
        # Phase 2: Core Agent Development
        {
            "title": "Phase 2: Pattern Matching & Learning Agents",
            "description": """**Pattern System Development:**
- Implement pattern retrieval system for known data brokers
- Create pattern similarity matching algorithms
- Develop pattern confidence scoring and selection logic
- Implement successful removal process capture
- Create pattern extraction from successful workflows
- Build pattern storage and versioning system
- Implement pattern optimization and refinement logic

**Acceptance Criteria:**
- Pattern matching system can identify and score relevant patterns
- Pattern learning system captures successful workflows
- Pattern versioning and storage is functional
- Confidence scoring accurately reflects pattern reliability""",
            "priority": 1,
            "estimate": 21
        },
        {
            "title": "Phase 2: Website Analysis & Form Submission Agents",
            "description": """**Web Scraping & Form Handling:**
- Implement web scraper using Playwright
- Create content analysis pipeline using LLM
- Develop removal form detection algorithms
- Build contact information extraction logic
- Implement pattern-first form submission logic
- Develop form field mapping and filling for new discoveries
- Handle different form types and CAPTCHA challenges
- Create form submission validation and success detection
- Add screenshot capture and retry logic

**Acceptance Criteria:**
- Web scraper can analyze data broker websites
- Form detection accurately identifies removal forms
- Form submission works for both known patterns and new discoveries
- Success/failure detection is reliable
- Screenshots are captured for documentation""",
            "priority": 1,
            "estimate": 21
        },
        {
            "title": "Phase 2: Email & Communication Agents",
            "description": """**Email Communication System:**
- Integrate with email service provider API
- Implement email template generation and sending
- Create email parsing and understanding logic
- Develop email inbox monitoring system
- Implement email classification (confirmation, rejection, etc.)
- Create confirmation response automation
- Build user communication system for escalations
- Implement reply processing with natural language understanding
- Handle conversation threading and state management

**Acceptance Criteria:**
- Email sending and receiving is functional
- Inbox monitoring detects and classifies emails correctly
- User escalation emails are contextual and helpful
- Reply processing understands user instructions
- Conversation state is properly managed""",
            "priority": 1,
            "estimate": 21
        },
        
        # Phase 3: Data Broker Integration
        {
            "title": "Phase 3: Data Broker Research & Cataloging",
            "description": """**Broker Database & Initial Patterns:**
- Research top 50 data brokers and document removal processes
- Create standardized broker profiles in database
- Test removal processes manually to understand patterns
- Create initial learned patterns from manual testing
- Build seed pattern database for common removal workflows
- Document each broker's removal method (email/form/phone)

**Acceptance Criteria:**
- 50+ data brokers are researched and documented
- Standardized broker profiles are created
- Initial patterns are tested and validated
- Seed pattern database is populated with working patterns
- Documentation includes success rates and timing estimates""",
            "priority": 2,
            "estimate": 21
        },
        {
            "title": "Phase 3: Automated Broker Processing",
            "description": """**Pattern-First Processing Implementation:**
- Implement pattern-first broker processing workflow
- Create broker discovery workflow for unknown brokers
- Develop success/failure detection and pattern validation
- Implement pattern learning from each successful removal
- Build progressive retry strategies with pattern adaptation
- Create broker-specific rate limiting
- Add user email escalation triggers for complex cases
- Implement pattern performance monitoring and optimization

**Acceptance Criteria:**
- System prioritizes learned patterns over discovery
- New broker discovery works reliably
- Pattern learning improves with each successful removal
- Retry strategies handle temporary failures
- Escalation triggers work for complex cases
- Performance monitoring tracks pattern effectiveness""",
            "priority": 2,
            "estimate": 21
        },
        
        # Phase 4: Status Tracking
        {
            "title": "Phase 4: Request Status & Tracking System",
            "description": """**Comprehensive Status Management:**
- Implement comprehensive status tracking for all requests
- Create status update workflows and automation
- Build automated status checking mechanisms
- Implement notification systems for status changes
- Create status reporting dashboards
- Add manual status override capabilities
- Optional: Implement Linear integration for internal bug tracking

**Acceptance Criteria:**
- All request statuses are tracked accurately
- Status updates happen automatically based on agent actions
- Notifications are sent for important status changes
- Dashboard provides clear overview of all requests
- Manual overrides work when needed""",
            "priority": 2,
            "estimate": 13
        },
        
        # Phase 5: User Interface
        {
            "title": "Phase 5: Frontend & API Development",
            "description": """**User Interface & API:**
- Create user registration and onboarding flow
- Build personal information input forms
- Develop removal request dashboard
- Create progress tracking interface
- Implement email inbox management UI
- Add request history and logs viewer
- Create RESTful API endpoints for all operations
- Implement proper authentication and authorization
- Add rate limiting and request validation
- Create comprehensive API documentation

**Acceptance Criteria:**
- User can register and input personal information
- Dashboard shows real-time progress of removals
- Request history is accessible and detailed
- API endpoints are secure and well-documented
- Rate limiting prevents abuse
- User experience is intuitive and responsive""",
            "priority": 2,
            "estimate": 21
        },
        
        # Phase 6: Testing & QA
        {
            "title": "Phase 6: Testing & Quality Assurance",
            "description": """**Comprehensive Testing Suite:**
- Unit tests for all agent components
- Integration tests for agent workflows
- End-to-end tests for complete removal processes
- Performance testing for concurrent requests
- Security testing for data handling
- User acceptance testing
- Comprehensive error handling implementation
- Circuit breaker patterns and resilience features
- Request queuing and retry mechanisms
- Monitoring and alerting systems

**Acceptance Criteria:**
- Test coverage is >90% for critical components
- Integration tests cover all major workflows
- Performance tests validate scalability targets
- Security tests ensure data protection
- Error handling gracefully manages failures
- System is resilient to external service failures""",
            "priority": 2,
            "estimate": 21
        },
        
        # Phase 7: Deployment
        {
            "title": "Phase 7: Production Deployment & Launch",
            "description": """**Production Readiness & Launch:**
- Set up production environment (AWS/GCP/Azure)
- Configure CI/CD pipelines
- Implement environment-specific configurations
- Set up production monitoring and logging
- Create backup and disaster recovery procedures
- Implement security hardening
- Create user documentation and guides
- Implement analytics and usage tracking
- Set up customer support systems
- Create legal compliance documentation
- Implement GDPR/CCPA compliance features

**Acceptance Criteria:**
- Production environment is secure and scalable
- CI/CD pipeline automates deployments
- Monitoring and logging provide operational visibility
- Backup and recovery procedures are tested
- Documentation is complete and user-friendly
- Legal compliance requirements are met
- System is ready for public launch""",
            "priority": 3,
            "estimate": 21
        }
    ]
    
    return tasks

def main():
    """Main function to create Linear tasks"""
    
    # Get API credentials from environment variables
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")
    
    if not api_key or not team_id:
        print("Error: Please set LINEAR_API_KEY and LINEAR_TEAM_ID environment variables")
        print("\nTo get your Linear API key:")
        print("1. Go to Linear Settings → API")
        print("2. Create a new Personal API key")
        print("3. Export it: export LINEAR_API_KEY=your_api_key_here")
        print("\nTo get your Team ID:")
        print("1. Go to your Linear team")
        print("2. Look at the URL: linear.app/team/[TEAM_ID]/...")
        print("3. Export it: export LINEAR_TEAM_ID=your_team_id_here")
        return
    
    creator = LinearTaskCreator(api_key, team_id)
    
    # Create project/epic for the entire initiative
    epic = creator.create_epic(
        "Data Broker Removal Agent",
        """Complete implementation of an AI-powered data broker removal service using LangGraph agents.

**Key Features:**
- Automated removal request processing
- Pattern learning and reuse for efficiency  
- Email-based human-in-the-loop escalation
- Comprehensive status tracking
- Scalable architecture supporting multiple users

**Target Timeline:** 16 weeks
**Expected Outcome:** Production-ready service capable of processing 100+ removal requests per hour"""
    )
    
    if epic:
        print(f"Created epic: {epic['name']} ({epic['url']})")
    
    # Create all phase tasks
    tasks = get_phase_tasks()
    created_tasks = []
    
    for task in tasks:
        print(f"Creating task: {task['title']}")
        created_task = creator.create_task(
            title=task['title'],
            description=task['description'],
            priority=task['priority'],
            estimate=task['estimate']
        )
        
        if created_task:
            created_tasks.append(created_task)
            print(f"✅ Created: {created_task['identifier']} - {created_task['title']}")
            print(f"   URL: {created_task['url']}")
        else:
            print(f"❌ Failed to create: {task['title']}")
        
        print()
    
    print(f"\nSummary: Created {len(created_tasks)} out of {len(tasks)} tasks")
    
    if created_tasks:
        print("\n📋 Created Tasks:")
        for task in created_tasks:
            print(f"  • {task['identifier']}: {task['title']}")

if __name__ == "__main__":
    main()