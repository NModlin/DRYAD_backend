# app/core/domain_contexts.py
"""
Domain context configurations for multi-client MCP tools.
Provides domain-specific terminology, patterns, and rules for different client types.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

class DomainContextManager:
    """Manages domain-specific contexts for MCP tools."""
    
    def __init__(self):
        self.contexts = self._load_domain_contexts()
    
    def _load_domain_contexts(self) -> Dict[str, Dict[str, Any]]:
        """Load domain context configurations."""
        return {
            "government_contracting": {
                "name": "Government Contracting",
                "description": "Federal acquisition and contracting domain",
                "terminology": {
                    "clin": "Contract Line Item Number",
                    "sow": "Statement of Work",
                    "rfp": "Request for Proposal",
                    "far": "Federal Acquisition Regulation",
                    "dfars": "Defense Federal Acquisition Regulation Supplement",
                    "naics": "North American Industry Classification System",
                    "psc": "Product Service Code",
                    "cage": "Commercial and Government Entity Code",
                    "duns": "Data Universal Numbering System",
                    "sam": "System for Award Management",
                    "fpds": "Federal Procurement Data System"
                },
                "classification_schemes": {
                    "far_dfars_taxonomy": [
                        "FAR Part 1 - Federal Acquisition Regulations System",
                        "FAR Part 2 - Definitions of Words and Terms",
                        "FAR Part 3 - Improper Business Practices and Personal Conflicts of Interest",
                        "FAR Part 4 - Administrative and Information Matters",
                        "FAR Part 5 - Publicizing Contract Actions",
                        "DFARS Part 201 - Federal Acquisition Regulations System",
                        "DFARS Part 202 - Definitions of Words and Terms",
                        "Security Clearance Requirements",
                        "Set-Aside Classifications",
                        "Contract Type Classifications"
                    ]
                },
                "extraction_schemas": {
                    "clin_structure": {
                        "fields": [
                            {"name": "clin_number", "type": "string", "description": "Contract Line Item Number (e.g., 0001, 0002)"},
                            {"name": "description", "type": "string", "description": "Detailed description of the CLIN"},
                            {"name": "quantity", "type": "number", "description": "Quantity if specified"},
                            {"name": "unit_of_measure", "type": "string", "description": "Unit of measurement (each, hour, month, etc.)"},
                            {"name": "unit_price", "type": "number", "description": "Price per unit if specified"},
                            {"name": "total_price", "type": "number", "description": "Total price for the CLIN"}
                        ]
                    },
                    "personnel_requirements": {
                        "fields": [
                            {"name": "position_title", "type": "string", "description": "Job title or position"},
                            {"name": "clearance_level", "type": "string", "description": "Required security clearance"},
                            {"name": "education_requirements", "type": "array", "description": "Required education levels"},
                            {"name": "experience_years", "type": "number", "description": "Years of experience required"},
                            {"name": "certifications", "type": "array", "description": "Required certifications"},
                            {"name": "skills", "type": "array", "description": "Required technical skills"}
                        ]
                    }
                },
                "similarity_weights": {
                    "agency": 0.25,
                    "naics_code": 0.20,
                    "text_content": 0.30,
                    "set_aside_type": 0.15,
                    "contract_value": 0.10
                },
                "pattern_indicators": {
                    "temporal": ["fiscal year", "quarter", "annual", "monthly", "deadline"],
                    "seasonal": ["Q1", "Q2", "Q3", "Q4", "FY", "end of year"],
                    "behavioral": ["procurement cycle", "award pattern", "competition level"]
                }
            },
            
            "legal_contracts": {
                "name": "Legal Contracts",
                "description": "Legal document analysis and contract management",
                "terminology": {
                    "party": "Legal entity in a contract",
                    "consideration": "Something of value exchanged",
                    "breach": "Violation of contract terms",
                    "indemnification": "Protection from liability",
                    "jurisdiction": "Legal authority over disputes",
                    "force_majeure": "Unforeseeable circumstances clause",
                    "liquidated_damages": "Pre-agreed penalty for breach"
                },
                "classification_schemes": {
                    "contract_risk_taxonomy": [
                        "High Risk - Unlimited Liability",
                        "Medium Risk - Limited Liability",
                        "Low Risk - Standard Terms",
                        "Intellectual Property Risk",
                        "Compliance Risk",
                        "Financial Risk",
                        "Operational Risk"
                    ]
                },
                "extraction_schemas": {
                    "contract_parties": {
                        "fields": [
                            {"name": "party_name", "type": "string", "description": "Legal name of the party"},
                            {"name": "party_type", "type": "string", "description": "Individual, Corporation, LLC, etc."},
                            {"name": "role", "type": "string", "description": "Buyer, Seller, Contractor, etc."},
                            {"name": "address", "type": "string", "description": "Legal address"},
                            {"name": "representative", "type": "string", "description": "Authorized representative"}
                        ]
                    }
                },
                "similarity_weights": {
                    "contract_type": 0.30,
                    "parties": 0.20,
                    "text_content": 0.25,
                    "value": 0.15,
                    "jurisdiction": 0.10
                }
            },
            
            "ecommerce": {
                "name": "E-commerce",
                "description": "Online retail and customer behavior analysis",
                "terminology": {
                    "sku": "Stock Keeping Unit",
                    "aov": "Average Order Value",
                    "ltv": "Lifetime Value",
                    "cac": "Customer Acquisition Cost",
                    "conversion_rate": "Percentage of visitors who purchase",
                    "cart_abandonment": "Leaving items in cart without purchasing"
                },
                "classification_schemes": {
                    "product_taxonomy": [
                        "Electronics",
                        "Clothing & Accessories",
                        "Home & Garden",
                        "Sports & Outdoors",
                        "Books & Media",
                        "Health & Beauty"
                    ]
                },
                "similarity_weights": {
                    "category": 0.25,
                    "price_range": 0.20,
                    "text_content": 0.30,
                    "brand": 0.15,
                    "customer_rating": 0.10
                }
            },
            
            "research_academic": {
                "name": "Research & Academic",
                "description": "Academic research and scientific literature analysis",
                "terminology": {
                    "doi": "Digital Object Identifier",
                    "impact_factor": "Journal citation metric",
                    "peer_review": "Expert evaluation process",
                    "citation": "Reference to another work",
                    "methodology": "Research approach and methods",
                    "hypothesis": "Testable prediction"
                },
                "classification_schemes": {
                    "research_taxonomy": [
                        "Computer Science",
                        "Biology & Life Sciences",
                        "Physics & Astronomy",
                        "Chemistry",
                        "Mathematics",
                        "Social Sciences",
                        "Engineering"
                    ]
                },
                "similarity_weights": {
                    "subject_area": 0.30,
                    "methodology": 0.25,
                    "text_content": 0.25,
                    "author": 0.10,
                    "publication_year": 0.10
                }
            }
        }
    
    def get_context(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get domain context configuration."""
        return self.contexts.get(domain)
    
    def get_terminology(self, domain: str) -> Dict[str, str]:
        """Get domain-specific terminology."""
        context = self.get_context(domain)
        return context.get("terminology", {}) if context else {}
    
    def get_classification_schemes(self, domain: str) -> Dict[str, List[str]]:
        """Get domain-specific classification schemes."""
        context = self.get_context(domain)
        return context.get("classification_schemes", {}) if context else {}
    
    def get_extraction_schema(self, domain: str, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get domain-specific extraction schema."""
        context = self.get_context(domain)
        if context and "extraction_schemas" in context:
            return context["extraction_schemas"].get(schema_name)
        return None
    
    def get_similarity_weights(self, domain: str) -> Dict[str, float]:
        """Get domain-specific similarity weights."""
        context = self.get_context(domain)
        return context.get("similarity_weights", {}) if context else {}
    
    def list_domains(self) -> List[str]:
        """List all available domain contexts."""
        return list(self.contexts.keys())
    
    def get_domain_info(self, domain: str) -> Dict[str, str]:
        """Get basic information about a domain."""
        context = self.get_context(domain)
        if context:
            return {
                "name": context.get("name", domain),
                "description": context.get("description", "")
            }
        return {}

# Global domain context manager instance
domain_context_manager = DomainContextManager()
