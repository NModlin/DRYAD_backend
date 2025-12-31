"""
Register JDE Audit Forensic Analyst Agent Template

This script validates and displays the JDE Audit Forensic Analyst agent template
for the DRYAD Agent Creation Studio.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def register_jde_forensic_agent():
    """Register the JDE Audit Forensic Analyst agent template."""

    print("🔧 Validating JDE Audit Forensic Analyst Agent Template...")
    print("=" * 70)

    # Load the agent template JSON
    template_path = Path(__file__).parent.parent / "agent_templates" / "jde_audit_forensic_analyst.json"

    if not template_path.exists():
        print(f"❌ Template file not found: {template_path}")
        return False

    with open(template_path, 'r') as f:
        template_data = json.load(f)

    print(f"✅ Loaded template: {template_data['metadata']['display_name']}")

    # Basic validation
    try:
        required_sections = ['agent_sheet_version', 'metadata', 'agent_definition',
                           'capabilities', 'behavior', 'llm_preferences', 'tools',
                           'integration', 'constraints', 'validation']

        for section in required_sections:
            if section not in template_data:
                raise ValueError(f"Missing required section: {section}")

        print("✅ Agent sheet structure validation passed")
    except Exception as e:
        print(f"❌ Agent sheet validation failed: {e}")
        return False

    # Display template information
    try:
        print(f"\n✅ Template validated successfully!")
        print(f"   Name: {template_data['metadata']['name']}")
        print(f"   Display Name: {template_data['metadata']['display_name']}")
        print(f"   Category: {template_data['metadata']['category']}")
        print(f"   Version: {template_data['metadata']['version']}")

        print("\n📋 Template Summary:")
        print(f"   Name: {template_data['metadata']['display_name']}")
        print(f"   Category: {template_data['metadata']['category']}")
        print(f"   Expertise Areas: {len(template_data['capabilities']['expertise_areas'])}")
        print(f"   Skills: {len(template_data['capabilities']['skills'])}")
        print(f"   Tools: {len(template_data['tools'])}")
        print(f"   JDE Tables: {len(template_data['jde_table_knowledge'])}")
        print(f"   Fraud Patterns: {len(template_data['common_fraud_patterns'])}")
        
        print("\n🎯 Agent Capabilities:")
        for area in template_data['capabilities']['expertise_areas'][:5]:
            print(f"   • {area}")
        print(f"   ... and {len(template_data['capabilities']['expertise_areas']) - 5} more")
        
        print("\n🔍 Forensic Analysis Templates:")
        for template_name, template_info in template_data['forensic_analysis_templates'].items():
            print(f"   • {template_info['name']}")
            print(f"     {template_info['description']}")
        
        print("\n🛠️ Available Tools:")
        for tool in template_data['tools']:
            print(f"   • {tool['name']}: {tool['description']}")
        
        print("\n📊 JDE Tables Covered:")
        for table_name, table_info in template_data['jde_table_knowledge'].items():
            print(f"   • {table_name}: {table_info['name']}")
            print(f"     Focus: {table_info['forensic_focus']}")
        
        print("\n⚠️ Common Fraud Patterns Detected:")
        for pattern in template_data['common_fraud_patterns']:
            print(f"   • {pattern['name']}")
            print(f"     {pattern['description']}")
        
        print("\n✅ JDE Audit Forensic Analyst agent template registered successfully!")
        print("\n📝 Next Steps:")
        print("   1. Deploy this template to the database")
        print("   2. Test with sample JDE audit data")
        print("   3. Create agent instances for specific investigations")
        print("   4. Integrate with DRYAD knowledge exploration")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create template: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_sample_investigation_queries():
    """Create sample investigation queries for testing."""
    
    print("\n\n🔬 Sample Investigation Queries:")
    print("=" * 70)
    
    queries = [
        {
            "name": "Fraud Detection - Round Dollar Amounts",
            "query": "Analyze F0911 for suspicious round-dollar transactions in the last 90 days",
            "expected_output": "List of transactions with round amounts, risk scores, and recommendations"
        },
        {
            "name": "After-Hours Activity Investigation",
            "query": "Find all transactions created outside business hours (6 PM - 6 AM) in F0911",
            "expected_output": "Timeline of after-hours activity with user details and transaction types"
        },
        {
            "name": "Vendor Master Data Audit",
            "query": "Detect unauthorized changes to vendor records in F0101 in the last 30 days",
            "expected_output": "List of vendor changes with before/after values and change authors"
        },
        {
            "name": "Duplicate Invoice Detection",
            "query": "Find duplicate invoices in F0411 that may indicate payment fraud",
            "expected_output": "Duplicate invoice pairs with amounts, dates, and vendors"
        },
        {
            "name": "Segregation of Duties Violation",
            "query": "Identify cases where the same user created and approved transactions",
            "expected_output": "List of SOD violations with user details and transaction information"
        },
        {
            "name": "Sales Order Anomaly Detection",
            "query": "Detect unusual pricing or discount patterns in F4111 sales orders",
            "expected_output": "Anomalous transactions with statistical analysis and risk assessment"
        },
        {
            "name": "User Activity Timeline",
            "query": "Build a complete activity timeline for user 'JSMITH' in the last week",
            "expected_output": "Chronological timeline with all user actions and affected records"
        },
        {
            "name": "Compliance Audit - SOX",
            "query": "Perform SOX compliance check on financial transactions in F0911",
            "expected_output": "Compliance report with violations, risk scores, and remediation steps"
        }
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. {query['name']}")
        print(f"   Query: {query['query']}")
        print(f"   Expected: {query['expected_output']}")
    
    # Save queries to file
    queries_path = Path(__file__).parent.parent / "agent_templates" / "jde_forensic_sample_queries.json"
    with open(queries_path, 'w') as f:
        json.dump(queries, f, indent=2)
    
    print(f"\n✅ Sample queries saved to: {queries_path}")


def create_agent_usage_guide():
    """Create a usage guide for the JDE Forensic Agent."""
    
    guide = """
# JDE Audit Forensic Analyst Agent - Usage Guide

## Overview

The JDE Audit Forensic Analyst is a specialized AI agent designed for forensic analysis
of JD Edwards Enterprise One audit tables, transaction logs, and compliance investigations.

## Quick Start

### 1. Submit Agent for Approval

```python
import requests

# Load the agent template
with open('agent_templates/jde_audit_forensic_analyst.json', 'r') as f:
    agent_sheet = json.load(f)

# Submit to Agent Creation Studio
response = requests.post(
    "http://localhost:8000/api/v1/agents/submit",
    headers={"Authorization": "Bearer <your_token>"},
    json={"agent_sheet": agent_sheet}
)

submission_id = response.json()['submission_id']
print(f"Submitted agent for review: {submission_id}")
```

### 2. Execute Forensic Analysis

```python
# After approval, execute the agent
response = requests.post(
    "http://localhost:8000/api/v1/agents/execute",
    headers={"Authorization": "Bearer <your_token>"},
    json={
        "agent_name": "JDE_Audit_Forensic_Analyst",
        "query": "Analyze F0911 for suspicious round-dollar transactions in the last 90 days",
        "context": "Financial audit for Q4 2024"
    }
)

result = response.json()
print(result['response'])
```

## Use Cases

### 1. Fraud Detection
- Round-dollar amount detection
- After-hours transaction analysis
- Duplicate transaction identification
- Unusual pattern detection

### 2. Compliance Audits
- SOX compliance verification
- GDPR data access audits
- HIPAA compliance checks
- PCI-DSS transaction audits

### 3. User Activity Investigations
- Timeline reconstruction
- Unauthorized access detection
- Activity pattern analysis
- Privilege escalation detection

### 4. Financial Reconciliation
- Journal entry analysis
- Unbalanced transaction detection
- Manual adjustment tracking
- Missing entry identification

## JDE Tables Analyzed

- **F0911**: Account Ledger (General Ledger)
- **F4111**: Sales Order Detail
- **F0101**: Address Book Master (Customers/Vendors)
- **F0411**: Accounts Payable Ledger
- **F4801**: Work Order Master
- **F42119**: Sales Order History

## Sample Queries

See `jde_forensic_sample_queries.json` for comprehensive examples.

## Best Practices

1. **Scope Your Investigation**: Be specific about time ranges and tables
2. **Provide Context**: Include business context for better analysis
3. **Review Evidence**: Always review the SQL queries and data samples
4. **Document Findings**: Use the report generation feature
5. **Follow Up**: Investigate flagged items with domain experts

## Security Considerations

- Agent has READ-ONLY access to audit tables
- Cannot modify or delete records
- All queries are logged for audit trail
- Sensitive data is redacted in reports

## Support

For questions or issues, contact the DRYAD.AI support team.
"""
    
    guide_path = Path(__file__).parent.parent / "agent_templates" / "JDE_FORENSIC_AGENT_USAGE_GUIDE.md"
    with open(guide_path, 'w') as f:
        f.write(guide)
    
    print(f"\n✅ Usage guide created: {guide_path}")


if __name__ == "__main__":
    print("\n🚀 JDE Audit Forensic Analyst Agent Registration")
    print("=" * 70)

    # Register the agent template
    success = register_jde_forensic_agent()

    if success:
        # Create sample queries
        create_sample_investigation_queries()

        # Create usage guide
        create_agent_usage_guide()

        print("\n\n✅ All tasks completed successfully!")
        print("\n📚 Files Created:")
        print("   • agent_templates/jde_audit_forensic_analyst.json")
        print("   • agent_templates/jde_forensic_sample_queries.json")
        print("   • agent_templates/JDE_FORENSIC_AGENT_USAGE_GUIDE.md")
        print("   • scripts/register_jde_forensic_agent.py")
    else:
        print("\n❌ Registration failed. Please check errors above.")
        sys.exit(1)

