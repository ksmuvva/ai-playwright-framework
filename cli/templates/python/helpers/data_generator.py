"""
Test Data Generator - AI-powered realistic test data generation
Generates unique, contextually appropriate test data for every run
"""

from typing import Dict, Any, List
import json
import os
import random
import string
from datetime import datetime, timedelta

# Try to import Faker
try:
    from faker import Faker
    FAKER_AVAILABLE = True
    fake = Faker()
except ImportError:
    FAKER_AVAILABLE = False
    print("⚠️  Faker not installed. Install with: pip install faker")

# Try to import AI client
AI_PROVIDER = os.getenv('AI_PROVIDER', 'anthropic')

if AI_PROVIDER == 'anthropic':
    try:
        from anthropic import Anthropic
        AI_CLIENT = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
elif AI_PROVIDER == 'openai':
    try:
        from openai import OpenAI
        AI_CLIENT = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        AI_AVAILABLE = True
    except ImportError:
        AI_AVAILABLE = False
else:
    AI_AVAILABLE = False


class TestDataGenerator:
    """AI-powered test data generation"""

    def __init__(self):
        self.ai_available = AI_AVAILABLE
        self.faker_available = FAKER_AVAILABLE

    def generate_from_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate test data from field schema

        Args:
            schema: Field definitions with types and constraints

        Returns:
            Generated test data

        Example schema:
        {
            "email": {"type": "email", "required": True},
            "phone": {"type": "phone", "country": "US"},
            "company_name": {"type": "text", "context": "company"}
        }
        """
        data = {}

        for field_name, field_spec in schema.items():
            data[field_name] = self._generate_field_value(field_name, field_spec)

        return data

    def _generate_field_value(self, field_name: str, spec: Dict) -> Any:
        """
        Generate value for a single field

        Args:
            field_name: Name of the field
            spec: Field specification

        Returns:
            Generated value
        """
        field_type = spec.get('type', 'text')

        # Use Faker for common types if available
        if self.faker_available:
            generators = {
                'email': lambda: fake.email(),
                'phone': lambda: fake.phone_number(),
                'name': lambda: fake.name(),
                'first_name': lambda: fake.first_name(),
                'last_name': lambda: fake.last_name(),
                'address': lambda: fake.address(),
                'street_address': lambda: fake.street_address(),
                'city': lambda: fake.city(),
                'state': lambda: fake.state(),
                'zipcode': lambda: fake.zipcode(),
                'country': lambda: fake.country(),
                'company': lambda: fake.company(),
                'job_title': lambda: fake.job(),
                'url': lambda: fake.url(),
                'date': lambda: fake.date(),
                'datetime': lambda: fake.date_time().isoformat(),
                'number': lambda: random.randint(1, 1000),
                'integer': lambda: random.randint(1, 1000),
                'float': lambda: round(random.uniform(1, 1000), 2),
                'boolean': lambda: random.choice([True, False]),
                'text': lambda: fake.text(max_nb_chars=50),
                'paragraph': lambda: fake.paragraph(),
                'sentence': lambda: fake.sentence(),
            }

            if field_type in generators:
                return generators[field_type]()

        # Fallback generators without Faker
        simple_generators = {
            'email': lambda: f"test{random.randint(1000, 9999)}@example.com",
            'phone': lambda: f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            'name': lambda: f"Test User {random.randint(1, 999)}",
            'number': lambda: random.randint(1, 1000),
            'text': lambda: f"Test Data {random.randint(1, 999)}",
        }

        if field_type in simple_generators:
            return simple_generators[field_type]()

        # Use AI for context-specific generation
        if self.ai_available:
            return self._ai_generate_field(field_name, spec)

        # Ultimate fallback
        return f"TestData_{field_name}_{random.randint(1, 999)}"

    def _ai_generate_field(self, field_name: str, spec: Dict) -> str:
        """
        Use AI to generate contextual field value

        Args:
            field_name: Field name
            spec: Field specification

        Returns:
            Generated value
        """
        try:
            prompt = f"""Generate a realistic value for the following field:
Field Name: {field_name}
Type: {spec.get('type', 'text')}
Context: {spec.get('context', 'general')}

Return ONLY the generated value, nothing else. No explanation, no quotes, just the raw value."""

            if AI_PROVIDER == 'anthropic':
                response = AI_CLIENT.messages.create(
                    model='claude-sonnet-4-5-20250929',
                    max_tokens=100,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response.content[0].text.strip()

            elif AI_PROVIDER == 'openai':
                response = AI_CLIENT.chat.completions.create(
                    model='gpt-4',
                    max_tokens=100,
                    messages=[{'role': 'user', 'content': prompt}]
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️  AI data generation failed: {e}")
            return f"TestData_{field_name}"

    def generate_power_apps_entity_data(self, entity_type: str) -> Dict[str, Any]:
        """
        Generate data specific to Power Apps entities

        Args:
            entity_type: Type of entity (contact, account, lead, etc.)

        Returns:
            Generated entity data
        """
        # Common Power Apps entity schemas
        schemas = {
            'contact': {
                'firstname': {'type': 'first_name'},
                'lastname': {'type': 'last_name'},
                'emailaddress1': {'type': 'email'},
                'telephone1': {'type': 'phone'},
                'jobtitle': {'type': 'job_title'},
                'address1_line1': {'type': 'street_address'},
                'address1_city': {'type': 'city'},
                'address1_stateorprovince': {'type': 'state'},
                'address1_postalcode': {'type': 'zipcode'},
            },
            'account': {
                'name': {'type': 'company'},
                'emailaddress1': {'type': 'email'},
                'telephone1': {'type': 'phone'},
                'websiteurl': {'type': 'url'},
                'address1_line1': {'type': 'street_address'},
                'address1_city': {'type': 'city'},
            },
            'lead': {
                'firstname': {'type': 'first_name'},
                'lastname': {'type': 'last_name'},
                'companyname': {'type': 'company'},
                'emailaddress1': {'type': 'email'},
                'telephone1': {'type': 'phone'},
                'jobtitle': {'type': 'job_title'},
            },
            'opportunity': {
                'name': {'type': 'sentence'},
                'description': {'type': 'paragraph'},
                'estimatedvalue': {'type': 'float'},
                'estimatedclosedate': {'type': 'date'},
            }
        }

        schema = schemas.get(entity_type.lower(), {})

        if not schema:
            print(f"⚠️  Unknown entity type: {entity_type}")
            return {}

        return self.generate_from_schema(schema)

    def generate_random_string(
        self,
        length: int = 10,
        include_digits: bool = True,
        include_special: bool = False
    ) -> str:
        """
        Generate random string

        Args:
            length: String length
            include_digits: Include numbers
            include_special: Include special characters

        Returns:
            Random string
        """
        chars = string.ascii_letters

        if include_digits:
            chars += string.digits

        if include_special:
            chars += string.punctuation

        return ''.join(random.choice(chars) for _ in range(length))

    def generate_date_range(
        self,
        start_days_ago: int = 30,
        end_days_ahead: int = 30
    ) -> Dict[str, str]:
        """
        Generate date range

        Args:
            start_days_ago: Start date (days in past)
            end_days_ahead: End date (days in future)

        Returns:
            Dict with start_date and end_date
        """
        today = datetime.now()
        start_date = today - timedelta(days=start_days_ago)
        end_date = today + timedelta(days=end_days_ahead)

        return {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }

    def load_from_file(self, filename: str) -> Dict[str, Any]:
        """
        Load test data from JSON file

        Args:
            filename: Path to JSON file

        Returns:
            Test data dictionary
        """
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Failed to load test data from {filename}: {e}")
            return {}

    def save_to_file(self, data: Dict[str, Any], filename: str):
        """
        Save test data to JSON file

        Args:
            data: Data to save
            filename: Output file path
        """
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Test data saved to {filename}")
        except Exception as e:
            print(f"⚠️  Failed to save test data: {e}")


# Global instance for easy access
data_generator = TestDataGenerator()
