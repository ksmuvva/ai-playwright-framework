"""
Data Generator Module (AI-Powered).

Provides intelligent test data generation for automation.
Supports schema-based generation, data variation, and Power Apps entities.
"""

import os
import json
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
import re


@dataclass
class DataConfig:
    """Configuration for data generation."""

    locale: str = "en_US"
    seed: Optional[int] = None
    include_special_chars: bool = True
    min_length: int = 1
    max_length: int = 50


class DataGenerator:
    """
    AI-powered data generator for test automation.

    Features:
    - Schema-based generation
    - Field-aware data generation
    - Data variation and uniqueness
    - Power Apps entity support
    - Culturally appropriate data
    """

    FIRST_NAMES = [
        "James",
        "Mary",
        "Robert",
        "Patricia",
        "John",
        "Jennifer",
        "Michael",
        "Linda",
        "David",
        "Elizabeth",
        "William",
        "Barbara",
        "Richard",
        "Susan",
        "Joseph",
        "Jessica",
        "Thomas",
        "Sarah",
    ]

    LAST_NAMES = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
    ]

    CITIES = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
    ]

    STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"]

    COMPANIES = [
        "Acme Corporation",
        "Tech Solutions Inc",
        "Global Industries",
        "Innovation Labs",
        "Digital Ventures",
        "Future Systems",
        "Smart Solutions",
        "Prime Technologies",
        "Elite Software",
        "Advanced Computing",
    ]

    def __init__(self, config: Optional[DataConfig] = None):
        """
        Initialize the data generator.

        Args:
            config: Data generation configuration
        """
        self.config = config or DataConfig()
        if self.config.seed:
            random.seed(self.config.seed)

    def generate_random_email(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """
        Generate a random email address.

        Args:
            first_name: First name to use
            last_name: Last name to use
            domain: Email domain (optional)

        Returns:
            Random email address
        """
        first = (first_name or random.choice(self.FIRST_NAMES)).lower()
        last = (last_name or random.choice(self.LAST_NAMES)).lower()
        domain = domain or f"{random.choice(['gmail', 'yahoo', 'outlook', 'company'])}.com"

        timestamp = datetime.now().strftime("%M%S")
        separators = [".", "_", ""]
        sep = random.choice(separators)

        return f"{first}{sep}{last}{timestamp}@{domain}"

    def generate_phone_number(self, country_code: str = "+1", format_type: str = "US") -> str:
        """
        Generate a random phone number.

        Args:
            country_code: Country code prefix
            format_type: Format style (US, INTERNATIONAL)

        Returns:
            Random phone number
        """
        area = str(random.randint(200, 999))
        exchange = str(random.randint(200, 999))
        subscriber = str(random.randint(1000, 9999))

        if format_type == "US":
            return f"({area}) {exchange}-{subscriber}"
        return f"{country_code} {area} {exchange} {subscriber}"

    def generate_company_data(self) -> Dict[str, str]:
        """
        Generate company information.

        Returns:
            Dictionary with company details
        """
        name = random.choice(self.COMPANIES)
        return {
            "name": name,
            "email": self.generate_random_email(domain="company.com"),
            "phone": self.generate_phone_number(),
            "address": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar'])} Street",
            "city": random.choice(self.CITIES),
            "state": random.choice(self.STATES),
            "zip_code": str(random.randint(10000, 99999)),
            "industry": random.choice(
                ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing"]
            ),
        }

    def generate_address(self) -> Dict[str, str]:
        """
        Generate a random address.

        Returns:
            Dictionary with address details
        """
        return {
            "street": f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Cedar', 'Pine'])} {random.choice(['Street', 'Avenue', 'Boulevard', 'Drive'])}",
            "city": random.choice(self.CITIES),
            "state": random.choice(self.STATES),
            "zip_code": str(random.randint(10000, 99999)),
            "country": "United States",
        }

    def generate_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data based on a schema definition.

        Args:
            schema: Dictionary describing field types and constraints

        Returns:
            Generated data dictionary
        """
        result = {}

        for field_name, field_config in schema.items():
            if isinstance(field_config, str):
                field_type = field_config
                constraints = {}
            elif isinstance(field_config, dict):
                field_type = field_config.get("type", "string")
                constraints = {k: v for k, v in field_config.items() if k != "type"}
            else:
                field_type = "string"
                constraints = {}

            result[field_name] = self._generate_field(field_name, field_type, constraints)

        return result

    def _generate_field(self, field_name: str, field_type: str, constraints: Dict[str, Any]) -> Any:
        """Generate a single field based on type and constraints."""
        min_val = constraints.get("min", 1)
        max_val = constraints.get("max", 100)
        length = constraints.get("length", 10)

        field_type_lower = field_type.lower()

        if "email" in field_name.lower() or field_type_lower == "email":
            return self.generate_random_email()
        elif "phone" in field_name.lower() or field_type_lower == "phone":
            return self.generate_phone_number()
        elif "name" in field_name.lower() or field_type_lower == "name":
            if "first" in field_name.lower():
                return random.choice(self.FIRST_NAMES)
            elif "last" in field_name.lower():
                return random.choice(self.LAST_NAMES)
            return f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}"
        elif "address" in field_name.lower() or field_type_lower == "address":
            return self.generate_address()
        elif "company" in field_name.lower() or field_type_lower == "company":
            return self.generate_company_data()["name"]
        elif "city" in field_name.lower():
            return random.choice(self.CITIES)
        elif "state" in field_name.lower():
            return random.choice(self.STATES)
        elif "zip" in field_name.lower() or "postal" in field_name.lower():
            return str(random.randint(10000, 99999))
        elif "date" in field_type_lower or "dob" in field_name.lower():
            return self.generate_date(start_years_ago=30, end_years_ago=18)
        elif "number" in field_type_lower or "int" in field_type_lower:
            return random.randint(min_val, max_val)
        elif "price" in field_type_lower or "amount" in field_type_lower:
            return round(random.uniform(min_val, max_val), 2)
        elif "boolean" in field_type_lower or "bool" in field_type_lower:
            return random.choice([True, False])
        elif "choice" in field_type_lower or "select" in field_type_lower:
            options = constraints.get("options", ["Option 1", "Option 2", "Option 3"])
            return random.choice(options)
        else:
            return self.generate_random_string(length)

    def generate_random_string(self, length: int = 10) -> str:
        """
        Generate a random string.

        Args:
            length: Length of the string

        Returns:
            Random string
        """
        chars = string.ascii_letters + string.digits
        if self.config.include_special_chars:
            chars += string.punctuation
        return "".join(random.choice(chars) for _ in range(length))

    def generate_date(
        self, start_years_ago: int = 30, end_years_ago: int = 18, format_type: str = "ISO"
    ) -> str:
        """
        Generate a random date.

        Args:
            start_years_ago: Years back from today (start range)
            end_years_ago: Years back from today (end range)
            format_type: Output format (ISO, US, EU)

        Returns:
            Formatted date string
        """
        today = datetime.now()
        start_date = today.replace(year=today.year - start_years_ago)
        end_date = today.replace(year=today.year - end_years_ago)

        days_range = (end_date - start_date).days
        random_days = random.randint(0, days_range)
        random_date = start_date + timedelta(days=random_days)

        if format_type == "ISO":
            return random_date.strftime("%Y-%m-%d")
        elif format_type == "US":
            return random_date.strftime("%m/%d/%Y")
        elif format_type == "EU":
            return random_date.strftime("%d/%m/%Y")
        return random_date.strftime("%Y-%m-%d")

    def generate_power_apps_entity_data(self, entity_type: str) -> Dict[str, Any]:
        """
        Generate Power Apps entity-specific data.

        Args:
            entity_type: Type of Power Apps entity (contact, account, opportunity, etc.)

        Returns:
            Entity data dictionary
        """
        entity_type = entity_type.lower()

        if entity_type in ["contact", "contacts"]:
            return {
                "firstname": random.choice(self.FIRST_NAMES),
                "lastname": random.choice(self.LAST_NAMES),
                "emailaddress1": self.generate_random_email(),
                "telephone1": self.generate_phone_number(),
                "address1_line1": self.generate_address()["street"],
                "city": random.choice(self.CITIES),
                "statecode": random.choice(self.STATES),
                "postalcode": str(random.randint(10000, 99999)),
            }
        elif entity_type in ["account", "accounts", "company"]:
            company_data = self.generate_company_data()
            return {
                "name": company_data["name"],
                "emailaddress1": company_data["email"],
                "telephone1": company_data["phone"],
                "address1_line1": company_data["address"],
                "city": company_data["city"],
                "stateorregion": company_data["state"],
                "postalcode": company_data["zip_code"],
            }
        elif entity_type in ["opportunity", "opportunities"]:
            return {
                "name": f"Opportunity - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "estimatedvalue": round(random.uniform(1000, 100000), 2),
                "description": self.generate_random_string(50),
                "statuscode": random.choice(["Open", "In Progress", "Closed Won", "Closed Lost"]),
            }
        elif entity_type in ["lead", "leads"]:
            return {
                "subject": f"Lead Inquiry - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "firstname": random.choice(self.FIRST_NAMES),
                "lastname": random.choice(self.LAST_NAMES),
                "emailaddress1": self.generate_random_email(),
                "telephone1": self.generate_phone_number(),
                "companyname": random.choice(self.COMPANIES),
                "statuscode": random.choice(["New", "Contacted", "Qualified", "Unqualified"]),
            }
        else:
            return {
                "name": f"{entity_type.title()} - {datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": self.generate_random_string(50),
                "createdon": self.generate_date(),
            }

    def generate_unique_data_batch(
        self, schema: Dict[str, Any], count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate a batch of unique data records.

        Args:
            schema: Data schema for generation
            count: Number of records to generate

        Returns:
            List of unique data dictionaries
        """
        generated = []
        for _ in range(count):
            data = self.generate_from_schema(schema)
            while data in generated:
                data = self.generate_from_schema(schema)
            generated.append(data)
        return generated
