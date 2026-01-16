# -*- coding: utf-8 -*-
"""
Enhanced GLM 4.7 API Test Script
Tests like a human would - with URL processing, reasoning, and validation
"""

import os
import sys
import requests
import json
import time
import urllib.parse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, 'strict')


class EnhancedGLM47Tester:
    """Enhanced test suite for GLM 4.7 API with human-like testing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.conversation_history = []
        self.test_urls = [
            "https://www.anthropic.com",
            "https://github.com",
            "https://stackoverflow.com"
        ]
        
    def log_test(self, test_name: str, passed: bool, details: str = "", response_time: float = 0, extra_data: dict = None):
        """Log test result with detailed information"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "response_time": response_time,
            "extra_data": extra_data or {}
        }
        self.test_results.append(result)
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} | {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_time > 0:
            print(f"   Response Time: {response_time:.2f}s")
        if extra_data:
            print(f"   Extra: {json.dumps(extra_data, indent=2, ensure_ascii=False)}")
        print()
    
    def make_request(self, messages: List[Dict], model: str = "glm-4", **kwargs) -> Optional[Dict]:
        """Make API request with error handling"""
        start_time = time.time()
        
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return response.json(), response_time
            else:
                print(f"   Error Response: {response.status_code} - {response.text}")
                return None, response_time
                
        except requests.exceptions.Timeout:
            print("   [WARNING] Request timed out")
            return None, time.time() - start_time
        except requests.exceptions.RequestException as e:
            print(f"   [WARNING] Request error: {str(e)}")
            return None, time.time() - start_time
    
    def test_1_basic_connectivity(self):
        """Test 1: Basic API connectivity"""
        print("\n[TEST 1] Basic API Connectivity")
        print("-" * 60)
        
        messages = [
            {"role": "user", "content": "Hello! Can you hear me? Please respond with 'Yes, I can hear you clearly.'"}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result and len(result["choices"]) > 0:
            response_content = result["choices"][0]["message"]["content"]
            expected_phrase = "Yes, I can hear you clearly"
            contains_expected = expected_phrase.lower() in response_content.lower()
            
            # Save usage stats
            usage = result.get("usage", {})
            
            self.log_test(
                "Basic API Connectivity",
                True,
                f"Response: {response_content[:150]}...",
                response_time,
                {"usage": usage, "model": result.get("model"), "contains_expected_phrase": contains_expected}
            )
            return True
        else:
            self.log_test(
                "Basic API Connectivity",
                False,
                "Failed to get valid response",
                response_time
            )
            return False
    
    def test_2_url_processing(self):
        """Test 2: URL processing and understanding"""
        print("\n[TEST 2] URL Processing")
        print("-" * 60)
        
        test_url = self.test_urls[0]
        messages = [
            {"role": "user", "content": f"What is the domain name of this URL: {test_url}? Please respond with just the domain name."}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            expected_domain = "anthropic.com"
            domain_extracted = expected_domain.lower() in response_content.lower()
            
            self.log_test(
                "URL Domain Extraction",
                domain_extracted,
                f"URL: {test_url} | Extracted: {response_content[:100]}",
                response_time,
                {"url": test_url, "expected_domain": expected_domain, "extracted_correctly": domain_extracted}
            )
            return domain_extracted
        else:
            self.log_test("URL Domain Extraction", False, "No response", response_time)
            return False
    
    def test_3_url_validation(self):
        """Test 3: URL validation and analysis"""
        print("\n[TEST 3] URL Validation")
        print("-" * 60)
        
        test_url = self.test_urls[1]
        messages = [
            {"role": "user", "content": f"Analyze this URL: {test_url}. Tell me: 1) Is it a valid URL? 2) What protocol does it use? 3) What is the domain?"}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            # Check for key information
            has_valid = "valid" in response_content.lower()
            has_https = "https" in response_content.lower()
            has_domain = "github.com" in response_content.lower()
            
            all_present = has_valid and has_https and has_domain
            
            self.log_test(
                "URL Validation",
                all_present,
                f"Analysis: {response_content[:150]}...",
                response_time,
                {
                    "url": test_url,
                    "identifies_valid": has_valid,
                    "identifies_protocol": has_https,
                    "identifies_domain": has_domain
                }
            )
            return all_present
        else:
            self.log_test("URL Validation", False, "No response", response_time)
            return False
    
    def test_4_conversational_memory(self):
        """Test 4: Conversational memory across multiple turns"""
        print("\n[TEST 4] Conversational Memory")
        print("-" * 60)
        
        # Build conversation history
        messages = [
            {"role": "user", "content": "My favorite color is blue and I love Python programming."},
            {"role": "assistant", "content": "I've noted that your favorite color is blue and you love Python programming!"},
            {"role": "user", "content": "What did I tell you about myself?"},
            {"role": "assistant", "content": "You told me your favorite color is blue and you love Python programming."},
            {"role": "user", "content": "What is my favorite programming language?"}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            remembers_python = "python" in response_content.lower()
            
            self.log_test(
                "Conversational Memory",
                remembers_python,
                f"Response: {response_content[:150]}...",
                response_time,
                {"conversation_turns": 3, "remembers_python": remembers_python}
            )
            return remembers_python
        else:
            self.log_test("Conversational Memory", False, "No response", response_time)
            return False
    
    def test_5_code_generation_with_url(self):
        """Test 5: Generate code to process URLs"""
        print("\n[TEST 5] Code Generation for URL Processing")
        print("-" * 60)
        
        messages = [
            {"role": "user", "content": "Write a Python function that extracts the domain name from a URL. The function should take a URL string as input and return the domain name."}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            # Check for function definition and URL parsing
            has_function = "def " in response_content and ("extract" in response_content.lower() or "domain" in response_content.lower())
            has_url_parsing = "urllib" in response_content or "parse" in response_content.lower()
            
            self.log_test(
                "Code Generation (URL Processing)",
                has_function,
                f"Contains function: {has_function}, Uses URL parsing: {has_url_parsing}",
                response_time,
                {"has_function_def": has_function, "uses_url_library": has_url_parsing}
            )
            return has_function
        else:
            self.log_test("Code Generation (URL Processing)", False, "No response", response_time)
            return False
    
    def test_6_reasoning_with_urls(self):
        """Test 6: Reasoning about multiple URLs"""
        print("\n[TEST 6] Multi-URL Reasoning")
        print("-" * 60)
        
        urls_str = ", ".join(self.test_urls)
        messages = [
            {"role": "user", "content": f"I have these URLs: {urls_str}. Which one would you use for finding code examples and why? Please be specific."}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            # Check if it identifies GitHub as the code repository
            mentions_github = "github" in response_content.lower()
            provides_reasoning = "because" in response_content.lower() or "reason" in response_content.lower() or "code" in response_content.lower()
            
            self.log_test(
                "Multi-URL Reasoning",
                mentions_github and provides_reasoning,
                f"Mentions GitHub: {mentions_github}, Provides reasoning: {provides_reasoning}",
                response_time,
                {
                    "identifies_github": mentions_github,
                    "provides_reasoning": provides_reasoning,
                    "urls_tested": len(self.test_urls)
                }
            )
            return mentions_github and provides_reasoning
        else:
            self.log_test("Multi-URL Reasoning", False, "No response", response_time)
            return False
    
    def test_7_json_output_with_url(self):
        """Test 7: Request structured JSON output with URL data"""
        print("\n[TEST 7] Structured JSON Output with URL Data")
        print("-" * 60)
        
        test_url = self.test_urls[2]
        messages = [
            {"role": "user", "content": f'For the URL "{test_url}", respond with valid JSON containing: {{"domain": "extracted domain", "protocol": "protocol used", "tld": "top-level domain"}}. Only respond with the JSON, no other text.'}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                if "```json" in response_content:
                    response_content = response_content.split("```json")[1].split("```")[0].strip()
                elif "```" in response_content:
                    response_content = response_content.split("```")[1].split("```")[0].strip()
                
                parsed_json = json.loads(response_content)
                is_valid_json = True
                has_domain = "domain" in parsed_json
                has_protocol = "protocol" in parsed_json
                has_tld = "tld" in parsed_json
                
                complete = has_domain and has_protocol and has_tld
                
                self.log_test(
                    "Structured JSON Output",
                    complete,
                    f"Valid JSON: {is_valid_json}, Complete: {complete}",
                    response_time,
                    {
                        "parsed_json": parsed_json,
                        "has_domain": has_domain,
                        "has_protocol": has_protocol,
                        "has_tld": has_tld
                    }
                )
                return complete
            except json.JSONDecodeError:
                self.log_test(
                    "Structured JSON Output",
                    False,
                    f"Failed to parse JSON. Response: {response_content[:100]}",
                    response_time
                )
                return False
        else:
            self.log_test("Structured JSON Output", False, "No response", response_time)
            return False
    
    def test_8_url_security_check(self):
        """Test 8: Security analysis of URLs"""
        print("\n[TEST 8] URL Security Analysis")
        print("-" * 60)
        
        safe_url = "https://www.example.com/path?param=value"
        messages = [
            {"role": "user", "content": f"Analyze this URL for security: {safe_url}. Tell me if it uses HTTPS and if the parameters look safe."}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            mentions_https = "https" in response_content.lower()
            mentions_security = "secure" in response_content.lower() or "safe" in response_content.lower()
            
            self.log_test(
                "URL Security Analysis",
                mentions_https or mentions_security,
                f"Mentions HTTPS: {mentions_https}, Mentions security: {mentions_security}",
                response_time,
                {"url_analyzed": safe_url, "mentions_https": mentions_https, "mentions_security": mentions_security}
            )
            return True
        else:
            self.log_test("URL Security Analysis", False, "No response", response_time)
            return False
    
    def test_9_different_models(self):
        """Test 9: Test different GLM model variants"""
        print("\n[TEST 9] Different Model Variants")
        print("-" * 60)
        
        models_to_test = ["glm-4", "glm-4-flash"]
        model_results = {}
        
        for model in models_to_test:
            messages = [
                {"role": "user", "content": "Respond with 'OK' if you can understand this message."}
            ]
            
            result, response_time = self.make_request(messages, model=model)
            
            if result and "choices" in result:
                response_content = result["choices"][0]["message"]["content"]
                model_results[model] = {
                    "works": True,
                    "response": response_content[:50],
                    "response_time": response_time
                }
                print(f"   [{model.upper()}] Working: YES | Response Time: {response_time:.2f}s")
            else:
                model_results[model] = {
                    "works": False,
                    "error": "Failed to get response",
                    "response_time": response_time
                }
                print(f"   [{model.upper()}] Working: NO | Response Time: {response_time:.2f}s")
        
        working_models = sum(1 for r in model_results.values() if r["works"])
        
        self.log_test(
            "Model Variants Support",
            working_models > 0,
            f"Working models: {working_models}/{len(models_to_test)}",
            sum(r.get("response_time", 0) for r in model_results.values()),
            {"model_results": model_results, "working_models": working_models}
        )
        return working_models > 0
    
    def test_10_streaming_response(self):
        """Test 10: Test streaming responses (if supported)"""
        print("\n[TEST 10] Streaming Response Test")
        print("-" * 60)
        
        messages = [
            {"role": "user", "content": "Count from 1 to 10 slowly."}
        ]
        
        result, response_time = self.make_request(messages, stream=False)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            has_numbers = any(str(i) in response_content for i in range(1, 11))
            
            self.log_test(
                "Streaming/Long Response",
                has_numbers,
                f"Response contains numbers: {has_numbers}",
                response_time,
                {"response_length": len(response_content), "has_counting": has_numbers}
            )
            return True
        else:
            self.log_test("Streaming/Long Response", False, "No response", response_time)
            return False
    
    def test_11_multilingual_url_processing(self):
        """Test 11: Multilingual capabilities with URL context"""
        print("\n[TEST 11] Multilingual URL Processing")
        print("-" * 60)
        
        messages = [
            {"role": "user", "content": "你好！请用中文回答：这个URL 'https://github.com' 是什么网站？"}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in response_content)
            mentions_github = "github" in response_content.lower()
            
            self.log_test(
                "Chinese URL Processing",
                has_chinese and mentions_github,
                f"Chinese response: {has_chinese}, Mentions GitHub: {mentions_github}",
                response_time,
                {"has_chinese_chars": has_chinese, "mentions_github": mentions_github}
            )
            return has_chinese
        else:
            self.log_test("Chinese URL Processing", False, "No response", response_time)
            return False
    
    def test_12_complex_url_task(self):
        """Test 12: Complex multi-step task with URLs"""
        print("\n[TEST 12] Complex Multi-Step URL Task")
        print("-" * 60)
        
        messages = [
            {"role": "user", "content": f"I want to scrape data from {self.test_urls[0]}. Tell me: 1) What library would you use in Python? 2) Write a simple example of how to start. 3) What are the ethical considerations?"}
        ]
        
        result, response_time = self.make_request(messages)
        
        if result and "choices" in result:
            response_content = result["choices"][0]["message"]["content"]
            
            mentions_library = any(lib in response_content.lower() for lib in ["requests", "beautifulsoup", "selenium", "scrapy"])
            has_code = "def " in response_content or "import " in response_content
            mentions_ethics = "ethic" in response_content.lower() or "respect" in response_content.lower() or "robots.txt" in response_content.lower()
            
            all_elements = mentions_library and has_code and mentions_ethics
            
            self.log_test(
                "Complex Multi-Step Task",
                all_elements,
                f"Library: {mentions_library}, Code: {has_code}, Ethics: {mentions_ethics}",
                response_time,
                {
                    "mentions_web_scraping_lib": mentions_library,
                    "includes_code_example": has_code,
                    "mentions_ethical_considerations": mentions_ethics
                }
            )
            return all_elements
        else:
            self.log_test("Complex Multi-Step Task", False, "No response", response_time)
            return False
    
    def run_all_tests(self):
        """Run all tests and generate comprehensive report"""
        print("\n" + "="*70)
        print("[START] Enhanced GLM 4.7 API Test Suite with URL Testing")
        print("="*70)
        print(f"API Key: {self.api_key[:20]}...")
        print(f"Base URL: {self.base_url}")
        print(f"Test URLs: {', '.join(self.test_urls)}")
        print("="*70)
        
        self.start_time = time.time()
        
        # Run all tests
        tests = [
            ("Basic Connectivity", self.test_1_basic_connectivity),
            ("URL Processing", self.test_2_url_processing),
            ("URL Validation", self.test_3_url_validation),
            ("Conversational Memory", self.test_4_conversational_memory),
            ("Code Generation with URL", self.test_5_code_generation_with_url),
            ("Multi-URL Reasoning", self.test_6_reasoning_with_urls),
            ("Structured JSON Output", self.test_7_json_output_with_url),
            ("URL Security Analysis", self.test_8_url_security_check),
            ("Different Models", self.test_9_different_models),
            ("Streaming Response", self.test_10_streaming_response),
            ("Multilingual Support", self.test_11_multilingual_url_processing),
            ("Complex Multi-Step Task", self.test_12_complex_url_task)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"[ERROR] Test '{test_name}' crashed: {str(e)}")
                import traceback
                traceback.print_exc()
                failed += 1
        
        # Generate report
        total_time = time.time() - self.start_time
        
        print("\n" + "="*70)
        print("[SUMMARY] Comprehensive Test Results")
        print("="*70)
        print(f"Total Tests: {len(tests)}")
        print(f"[PASS] Passed: {passed}")
        print(f"[FAIL] Failed: {failed}")
        print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Average Time per Test: {(total_time/len(tests)):.2f}s")
        print("="*70)
        
        # Category breakdown
        print("\n[CATEGORY BREAKDOWN]")
        print("-" * 70)
        categories = {
            "Basic Functionality": ["Basic Connectivity", "Conversational Memory"],
            "URL Processing": ["URL Processing", "URL Validation", "Multi-URL Reasoning", "URL Security Analysis"],
            "Advanced Features": ["Code Generation with URL", "Structured JSON Output", "Different Models", "Streaming Response"],
            "Complex Tasks": ["Complex Multi-Step Task"],
            "Language Support": ["Multilingual Support"]
        }
        
        for category, test_names in categories.items():
            category_results = [r for r in self.test_results if r["test_name"] in test_names]
            if category_results:
                passed_count = sum(1 for r in category_results if r["passed"])
                total_count = len(category_results)
                print(f"{category}: {passed_count}/{total_count} passed")
        
        # Save results
        self.save_results()
        
        return passed, failed
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"glm47_enhanced_test_results_{timestamp}.json"
        
        report = {
            "api_key": self.api_key[:20] + "...",
            "test_date": datetime.now().isoformat(),
            "base_url": self.base_url,
            "test_urls": self.test_urls,
            "total_tests": len(self.test_results),
            "passed": sum(1 for r in self.test_results if r["passed"]),
            "failed": sum(1 for r in self.test_results if not r["passed"]),
            "success_rate": (sum(1 for r in self.test_results if r["passed"]) / len(self.test_results) * 100) if self.test_results else 0,
            "results": self.test_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n[SAVE] Results saved to: {filename}")
        print(f"[SAVE] Detailed logs available for analysis")


def main():
    """Main test execution"""
    # Try to load from .env file
    api_key = None
    
    if os.path.exists(".env"):
        print("[INFO] Loading API key from .env file...")
        with open(".env", 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("GLM_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    
    # Fallback to provided key or environment variable
    if not api_key:
        api_key = os.getenv("GLM_API_KEY", "85cf3935c0b843738d461fec7cb2b515.dFTF3tjsPnXLaglE")
    
    print(f"\n[INFO] Using API Key: {api_key[:20]}...")
    
    # Create tester instance
    tester = EnhancedGLM47Tester(api_key)
    
    # Run all tests
    passed, failed = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
