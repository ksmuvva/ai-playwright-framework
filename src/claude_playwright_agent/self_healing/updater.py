"""
Self-Healing Code Updater Module

Automatically updates page object files with healed selectors.
Integrates with healing analytics to suggest and apply code improvements.
"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CodeUpdater:
    """
    Update page object code with healed selectors.

    Example:
        >>> updater = CodeUpdater()
        >>> updater.apply_healing_to_page_object(
        ...     page_object_path="pages/login_page.py",
        ...     healing_results=[...]
        ... )
    """

    # Patterns to find selector usage in code
    SELECTOR_PATTERNS = {
        'click': r'self\.click\(["\']([^"\']+)["\']',
        'fill': r'self\.fill\(["\']([^"\']+)["\']',
        'type': r'self\.type\(["\']([^"\']+)["\']',
        'is_visible': r'self\.is_visible\(["\']([^"\']+)["\']',
        'wait_for': r'self\.wait_for_selector\(["\']([^"\']+)["\']',
    }

    def __init__(self, backup: bool = True):
        """
        Initialize CodeUpdater.

        Args:
            backup: Whether to create backup files before modifying
        """
        self.backup = backup
        self.modifications: List[Dict[str, Any]] = []

    def apply_healing_to_page_object(
        self,
        page_object_path: str,
        healing_results: List[Dict[str, Any]]
    ) -> bool:
        """
        Apply healing results to a page object file.

        Args:
            page_object_path: Path to page object Python file
            healing_results: List of healing result dictionaries

        Returns:
            True if file was modified, False otherwise
        """
        filepath = Path(page_object_path)

        if not filepath.exists():
            logger.error(f"Page object file not found: {filepath}")
            return False

        # Read file
        content = filepath.read_text(encoding='utf-8')
        original_content = content

        # Create backup if enabled
        if self.backup:
            backup_path = filepath.with_suffix(f'.py.bak')
            backup_path.write_text(content, encoding='utf-8')
            logger.debug(f"Created backup: {backup_path}")

        # Apply each healing result
        modifications_made = 0
        for healing in healing_results:
            if healing.get('success'):
                original_selector = healing.get('original_selector')
                healed_selector = healing.get('healed_selector')
                strategy = healing.get('strategy_used')

                if original_selector and healed_selector:
                    # Replace selector in content
                    new_content = self._replace_selector(
                        content,
                        original_selector,
                        healed_selector,
                        strategy
                    )

                    if new_content != content:
                        content = new_content
                        modifications_made += 1

                        self.modifications.append({
                            "file": str(filepath),
                            "original_selector": original_selector,
                            "healed_selector": healed_selector,
                            "strategy": strategy
                        })

                        logger.info(f"Replaced selector '{original_selector}' with '{healed_selector}'")

        # Write modified content back
        if modifications_made > 0:
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Applied {modifications_made} selector updates to {filepath}")
            return True
        else:
            logger.info(f"No selector updates needed for {filepath}")
            return False

    def _replace_selector(
        self,
        content: str,
        original_selector: str,
        healed_selector: str,
        strategy: Optional[str]
    ) -> str:
        """
        Replace selector in code content.

        Args:
            content: File content
            original_selector: Original selector to replace
            healed_selector: New selector to use
            strategy: Strategy used for healing

        Returns:
            Modified content
        """
        # Escape special regex characters in selector
        escaped_selector = re.escape(original_selector)

        # Pattern to match selector strings (both single and double quotes)
        pattern = rf'([\'"]){escaped_selector}\1'

        # Replacement with healing comment
        replacement = rf'\1{healed_selector}\1  # Auto-healed from "{original_selector}" using {strategy}'

        # Replace all occurrences
        new_content = re.sub(pattern, replacement, content)

        return new_content

    def generate_healing_report(self) -> str:
        """
        Generate a report of all modifications made.

        Returns:
            Markdown formatted report
        """
        if not self.modifications:
            return "# No Selector Modifications\n\nNo selectors were updated."

        lines = [
            "# Self-Healing Code Update Report",
            f"\nTotal modifications: {len(self.modifications)}\n",
            "## Modified Files\n"
        ]

        # Group by file
        by_file: Dict[str, List[Dict]] = {}
        for mod in self.modifications:
            filepath = mod['file']
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(mod)

        for filepath, mods in by_file.items():
            lines.append(f"### {filepath}")
            lines.append(f"Modifications: {len(mods)}\n")

            for mod in mods:
                lines.append(f"- `{mod['original_selector']}` → `{mod['healed_selector']}`")
                lines.append(f"  - Strategy: {mod['strategy']}")
            lines.append("")

        lines.append("## Recommendations")
        lines.append("\n1. Review all changes to ensure they're correct")
        lines.append("2. Run tests to verify the updated selectors work")
        lines.append("3. Consider updating test data if selectors were data-driven")
        lines.append("4. Commit changes with message: 'chore: apply self-healing selector updates'")

        return "\n".join(lines)

    def suggest_selector_improvements(
        self,
        page_object_path: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze a page object file and suggest selector improvements.

        Args:
            page_object_path: Path to page object Python file

        Returns:
            List of suggestion dictionaries
        """
        filepath = Path(page_object_path)

        if not filepath.exists():
            logger.error(f"Page object file not found: {filepath}")
            return []

        content = filepath.read_text(encoding='utf-8')
        suggestions = []

        # Check for fragile selectors
        fragile_patterns = {
            'css_only_id': r'self\.click\(["\']#([a-zA-Z]+)\["\']\)',  # #id[...]
            'xpath': r'self\.click\(["\']//[^"\']+["\']\)',  # XPath selectors
            'index_based': r'self\.click\(["\'].*>> nth=[0-9]+["\']\)',  # nth= selectors
        }

        for pattern_type, pattern in fragile_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                suggestions.append({
                    "type": "fragile_selector",
                    "pattern_type": pattern_type,
                    "count": len(matches),
                    "examples": matches[:3],
                    "recommendation": self._get_recommendation_for_pattern(pattern_type)
                })

        # Check for missing data-testid attributes
        has_data_testid = 'data-testid' in content or 'test_id' in content
        if not has_data_testid:
            suggestions.append({
                "type": "best_practice",
                "recommendation": "Consider using data-testid attributes for more stable selectors"
            })

        return suggestions

    def _get_recommendation_for_pattern(self, pattern_type: str) -> str:
        """Get recommendation for a specific pattern type."""
        recommendations = {
            'css_only_id': 'Consider using more specific attributes or data-testid',
            'xpath': 'XPath selectors are fragile. Consider CSS selectors or Playwright locators',
            'index_based': 'Index-based selectors break when UI changes. Use text-based or data-testid selectors'
        }
        return recommendations.get(pattern_type, "Review this selector for potential improvements")

    def create_selector_constants(
        self,
        page_object_path: str,
        selector_file: Optional[str] = None
    ) -> bool:
        """
        Extract magic string selectors to constants.

        Args:
            page_object_path: Path to page object file
            selector_file: Optional separate file for selectors

        Returns:
            True if successful
        """
        filepath = Path(page_object_path)

        if not filepath.exists():
            logger.error(f"Page object file not found: {filepath}")
            return False

        content = filepath.read_text(encoding='utf-8')

        # Extract all selector strings
        selectors: Dict[str, List[str]] = {}

        for method, pattern in self.SELECTOR_PATTERNS.items():
            matches = re.findall(pattern, content)
            for selector in matches:
                if selector not in selectors:
                    selectors[selector] = []
                selectors[selector].append(method)

        if not selectors:
            logger.info("No selectors found to extract")
            return False

        # Generate constant names
        constant_names = {}
        for selector in selectors.keys():
            # Generate a meaningful constant name
            name = self._generate_constant_name(selector)
            constant_names[selector] = name

        # Generate selector class code
        class_code = self._generate_selector_class(constant_names, selectors)

        if selector_file:
            # Write to separate file
            selector_path = Path(selector_file)
            selector_path.write_text(class_code, encoding='utf-8')
            logger.info(f"Created selector file: {selector_path}")
        else:
            # Add to existing file
            # This is more complex as we need to parse the AST
            logger.info("Selector extraction to existing file not yet implemented")

        return True

    def _generate_constant_name(self, selector: str) -> str:
        """Generate a constant name from selector."""
        # Remove special characters
        clean = re.sub(r'[^a-zA-Z0-9]+', '_', selector)
        # Convert to uppercase
        name = clean.upper()
        # Add prefix if doesn't start with letter
        if not name[0].isalpha():
            name = f"SELECTOR_{name}"
        return name

    def _generate_selector_class(
        self,
        constant_names: Dict[str, str],
        selectors: Dict[str, List[str]]
    ) -> str:
        """Generate a selector class code."""
        lines = [
            '"""Auto-generated selector constants."""\n',
            'class Selectors:',
            '    """Selector constants for page elements."""\n\n'
        ]

        for selector, const_name in sorted(constant_names.items()):
            methods = ', '.join(selectors[selector])
            lines.append(f'    {const_name} = "{selector}"  # Used by: {methods}')

        return '\n'.join(lines)

    def restore_backup(self, page_object_path: str) -> bool:
        """
        Restore a file from its backup.

        Args:
            page_object_path: Path to original file (without .bak extension)

        Returns:
            True if backup was restored
        """
        filepath = Path(page_object_path)
        backup_path = filepath.with_suffix('.py.bak')

        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Restore from backup
        content = backup_path.read_text(encoding='utf-8')
        filepath.write_text(content, encoding='utf-8')

        logger.info(f"Restored {filepath} from backup")

        # Remove backup
        backup_path.unlink()

        return True

    def get_modifications(self) -> List[Dict[str, Any]]:
        """
        Get list of all modifications made.

        Returns:
            List of modification dictionaries
        """
        return self.modifications.copy()

    def clear_modifications(self) -> None:
        """Clear modification history."""
        self.modifications.clear()

    def __repr__(self) -> str:
        """String representation."""
        return f"CodeUpdater(modifications={len(self.modifications)}, backup={self.backup})"
