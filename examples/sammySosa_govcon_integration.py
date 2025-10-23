#!/usr/bin/env python3
"""
Example: sammySosa Apollo GovCon Integration with DRYAD.AI MCP Server

This example demonstrates how sammySosa (a government contracting platform) 
would use DRYAD.AI's generic MCP tools for domain-specific GovCon tasks.

The key insight: DRYAD.AI provides generic, configurable AI tools while 
sammySosa implements GovCon-specific logic using those tools.
"""

import json
import asyncio
from typing import Dict, List, Any

# Mock MCP client for demonstration
class MCPClient:
    """Mock MCP client for sammySosa integration."""
    
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool (mock implementation)."""
        # In real implementation, this would make HTTP requests to DRYAD.AI MCP server
        print(f"🔧 Calling MCP tool: {tool_name}")
        print(f"📋 Arguments: {json.dumps(arguments, indent=2)}")
        
        # Mock response based on tool
        if tool_name == "extract_structured_data":
            return self._mock_extraction_response(arguments)
        elif tool_name == "analyze_patterns":
            return self._mock_pattern_response(arguments)
        elif tool_name == "classify_content":
            return self._mock_classification_response(arguments)
        elif tool_name == "calculate_similarity":
            return self._mock_similarity_response(arguments)
        else:
            return {"content": [{"type": "text", "text": f"Mock response for {tool_name}"}]}
    
    def _mock_extraction_response(self, args):
        return {
            "content": [{
                "type": "text",
                "text": """**Structured Data Extraction**
Domain: government_contracting

```json
{
  "clin_number": "0001",
  "description": "Software Development Services",
  "quantity": 12,
  "unit_of_measure": "months",
  "unit_price": 50000,
  "total_price": 600000
}
```"""
            }]
        }
    
    def _mock_pattern_response(self, args):
        return {
            "content": [{
                "type": "text", 
                "text": """**Pattern Analysis**
Context: government_procurement_cycles

**Patterns Found:**
• Temporal pattern: Regular RFP releases every 90 days
• Seasonal pattern: Peak activity in Q1 and Q4
• Behavioral pattern: Increasing small business set-asides"""
            }]
        }
    
    def _mock_classification_response(self, args):
        return {
            "content": [{
                "type": "text",
                "text": """**Content Classification**
Scheme: far_dfars_taxonomy

**Classifications:**
• FAR Part 12 - Acquisition of Commercial Items
• Security Clearance Required: Secret
• Set-Aside: Small Business

**Risk Assessment:** Medium"""
            }]
        }
    
    def _mock_similarity_response(self, args):
        return {
            "content": [{
                "type": "text",
                "text": """**Similarity Analysis**
Domain: government_contracting
Factors: text, metadata

**Results:**
• Score: 0.892 - DoD Software Modernization Initiative
• Score: 0.847 - Navy IT Infrastructure Upgrade
• Score: 0.823 - Air Force Cloud Migration Project"""
            }]
        }

class SammySosaGovConAnalyzer:
    """sammySosa's GovCon-specific analyzer using generic DRYAD.AI MCP tools."""
    
    def __init__(self, mcp_client: MCPClient):
        self.mcp = mcp_client
        
        # GovCon-specific schemas and configurations
        self.govcon_schemas = {
            "clin_extraction": {
                "fields": [
                    {"name": "clin_number", "type": "string", "description": "Contract Line Item Number"},
                    {"name": "description", "type": "string", "description": "CLIN description"},
                    {"name": "quantity", "type": "number", "description": "Quantity if specified"},
                    {"name": "unit_of_measure", "type": "string", "description": "Unit of measurement"},
                    {"name": "unit_price", "type": "number", "description": "Price per unit"},
                    {"name": "total_price", "type": "number", "description": "Total CLIN value"}
                ]
            },
            "personnel_requirements": {
                "fields": [
                    {"name": "position_title", "type": "string", "description": "Job title"},
                    {"name": "clearance_level", "type": "string", "description": "Security clearance required"},
                    {"name": "education_requirements", "type": "array", "description": "Education requirements"},
                    {"name": "experience_years", "type": "number", "description": "Years of experience"},
                    {"name": "certifications", "type": "array", "description": "Required certifications"}
                ]
            }
        }
        
        self.govcon_similarity_weights = {
            "agency": 0.25,
            "naics_code": 0.20,
            "text_content": 0.30,
            "set_aside_type": 0.15,
            "contract_value": 0.10
        }
    
    async def analyze_sow_document(self, sow_text: str) -> Dict[str, Any]:
        """Analyze a Statement of Work using generic MCP tools."""
        print("🏛️ sammySosa: Analyzing SOW Document")
        
        # 1. Extract CLIN structure using generic structured data extraction
        clin_data = await self.mcp.call_tool("extract_structured_data", {
            "text": sow_text,
            "schema": self.govcon_schemas["clin_extraction"],
            "domain_context": "government_contracting"
        })
        
        # 2. Extract personnel requirements
        personnel_data = await self.mcp.call_tool("extract_structured_data", {
            "text": sow_text,
            "schema": self.govcon_schemas["personnel_requirements"],
            "domain_context": "government_contracting"
        })
        
        # 3. Classify for FAR/DFARS compliance
        compliance_analysis = await self.mcp.call_tool("classify_content", {
            "content": sow_text,
            "classification_scheme": "far_dfars_taxonomy",
            "risk_assessment": True,
            "domain_rules": "government_contracting_compliance"
        })
        
        return {
            "clin_structure": clin_data,
            "personnel_requirements": personnel_data,
            "compliance_analysis": compliance_analysis
        }
    
    async def find_similar_opportunities(self, target_opportunity: str, historical_opportunities: List[str]) -> Dict[str, Any]:
        """Find similar opportunities using configurable similarity analysis."""
        print("🔍 sammySosa: Finding Similar Opportunities")
        
        similarity_results = await self.mcp.call_tool("calculate_similarity", {
            "target_item": target_opportunity,
            "comparison_items": historical_opportunities,
            "similarity_factors": ["text", "metadata"],
            "weighting_scheme": self.govcon_similarity_weights,
            "domain_context": "government_contracting"
        })
        
        return similarity_results
    
    async def analyze_agency_patterns(self, agency_data: str) -> Dict[str, Any]:
        """Analyze agency procurement patterns."""
        print("📊 sammySosa: Analyzing Agency Patterns")
        
        pattern_analysis = await self.mcp.call_tool("analyze_patterns", {
            "data": agency_data,
            "pattern_types": ["temporal", "seasonal", "behavioral"],
            "analysis_context": "government_procurement_cycles",
            "prediction_horizon": "12_months"
        })
        
        return pattern_analysis
    
    async def process_performance_locations(self, opportunity_text: str) -> Dict[str, Any]:
        """Extract and process performance locations."""
        print("🗺️ sammySosa: Processing Performance Locations")
        
        geographic_data = await self.mcp.call_tool("process_geographic_data", {
            "text": opportunity_text,
            "extraction_types": ["addresses", "regions", "locations"],
            "geocoding": True,
            "context_type": "government_contracting_performance_locations"
        })
        
        return geographic_data

async def main():
    """Demonstrate sammySosa integration with DRYAD.AI MCP."""
    print("🚀 sammySosa Apollo GovCon + DRYAD.AI MCP Integration Demo")
    print("=" * 70)
    
    # Initialize MCP client
    mcp_client = MCPClient(api_key="sammysosa_api_key_123")
    
    # Initialize sammySosa analyzer
    analyzer = SammySosaGovConAnalyzer(mcp_client)
    
    # Sample SOW text
    sample_sow = """
    STATEMENT OF WORK
    
    CLIN 0001: Software Development Services
    Quantity: 12 months
    Unit Price: $50,000 per month
    Total: $600,000
    
    The contractor shall provide software development services for the Department of Defense
    modernization initiative. Performance location: Pentagon, Arlington, VA.
    
    Personnel Requirements:
    - Senior Software Engineer: Secret clearance, 5+ years experience, AWS certification
    - Project Manager: Top Secret clearance, PMP certification, 8+ years experience
    
    This contract falls under FAR Part 12 - Acquisition of Commercial Items.
    Set-aside: Small Business
    """
    
    # Sample historical opportunities
    historical_opps = [
        "DoD Software Modernization Initiative - Cloud migration and application development",
        "Navy IT Infrastructure Upgrade - Network modernization and security enhancement",
        "Air Force Cloud Migration Project - Legacy system migration to AWS GovCloud"
    ]
    
    print("\n1. 📄 SOW Analysis")
    print("-" * 30)
    sow_analysis = await analyzer.analyze_sow_document(sample_sow)
    
    print("\n2. 🔍 Similar Opportunities")
    print("-" * 30)
    similarity_results = await analyzer.find_similar_opportunities(sample_sow, historical_opps)
    
    print("\n3. 📊 Agency Pattern Analysis")
    print("-" * 30)
    agency_data = json.dumps({
        "agency": "Department of Defense",
        "opportunities": [
            {"date": "2024-01-15", "value": 500000, "type": "IT Services"},
            {"date": "2024-04-20", "value": 750000, "type": "Software Development"},
            {"date": "2024-07-10", "value": 600000, "type": "Cloud Migration"}
        ]
    })
    pattern_results = await analyzer.analyze_agency_patterns(agency_data)
    
    print("\n4. 🗺️ Geographic Analysis")
    print("-" * 30)
    geographic_results = await analyzer.process_performance_locations(sample_sow)
    
    print("\n✅ sammySosa Integration Complete!")
    print("\n💡 Key Benefits:")
    print("• sammySosa gets powerful AI capabilities without building AI infrastructure")
    print("• DRYAD.AI serves multiple domains with the same generic tools")
    print("• Domain-specific logic stays in sammySosa client code")
    print("• Both systems can evolve independently")

if __name__ == "__main__":
    asyncio.run(main())
