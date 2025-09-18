#!/usr/bin/env python3
"""
Ansible Configuration Validation Script for Koji-Boxed

This script validates the YAML configuration files in ansible-configs/
to ensure they conform to the expected schema and cross-references are valid.
"""

import sys
import os
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass


@dataclass
class ValidationError:
    """Represents a validation error with context"""
    file: str
    line: Optional[int]
    message: str
    severity: str = "error"  # error, warning


class ConfigValidator:
    """Validates Koji ansible configuration files"""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def add_error(self, file: str, message: str, line: int = None):
        """Add a validation error"""
        self.errors.append(ValidationError(file, line, message, "error"))

    def add_warning(self, file: str, message: str, line: int = None):
        """Add a validation warning"""
        self.warnings.append(ValidationError(file, line, message, "warning"))

    def validate_yaml_syntax(self, file_path: Path) -> Optional[Any]:
        """Validate YAML syntax and return parsed content"""
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)
            return content
        except yaml.YAMLError as e:
            line = getattr(e, 'problem_mark', None)
            line_num = line.line + 1 if line else None
            self.add_error(file_path.name, f"YAML syntax error: {e}", line_num)
            return None
        except Exception as e:
            self.add_error(file_path.name, f"Failed to read file: {e}")
            return None

    def validate_users(self, users_data: List[Dict]) -> Set[str]:
        """Validate users configuration and return set of user names"""
        user_names = set()
        valid_permissions = {
            'admin', 'tag', 'target', 'host', 'dist-repo', 'maven-import',
            'repo', 'build', 'livecd', 'appliance', 'image', 'win-admin',
            'win-import', 'sign', 'appliance-admin'
        }
        valid_states = {'present', 'absent'}

        for i, user in enumerate(users_data):
            if not isinstance(user, dict):
                self.add_error('users.yml', f"User entry {i+1} must be a dictionary")
                continue

            # Required fields
            if 'name' not in user:
                self.add_error('users.yml', f"User entry {i+1} missing required 'name' field")
                continue

            name = user['name']
            if not isinstance(name, str) or not name.strip():
                self.add_error('users.yml', f"User entry {i+1} 'name' must be a non-empty string")
                continue

            user_names.add(name)

            # Principal validation
            if 'principal' in user:
                principal = user['principal']
                if not isinstance(principal, str) or '@' not in principal:
                    self.add_error('users.yml', f"User '{name}' principal must be in format 'user@REALM'")

            # Permissions validation
            if 'permissions' in user:
                permissions = user['permissions']
                if not isinstance(permissions, list):
                    self.add_error('users.yml', f"User '{name}' permissions must be a list")
                else:
                    for perm in permissions:
                        if perm not in valid_permissions:
                            self.add_warning('users.yml', f"User '{name}' has unknown permission '{perm}'. Valid permissions: {', '.join(sorted(valid_permissions))}")

            # State validation
            state = user.get('state', 'present')
            if state not in valid_states:
                self.add_error('users.yml', f"User '{name}' state must be one of: {', '.join(valid_states)}")

        return user_names

    def validate_hosts(self, hosts_data: List[Dict]) -> Set[str]:
        """Validate hosts configuration and return set of host names"""
        host_names = set()
        valid_arches = {
            'x86_64', 'i686', 'noarch', 'aarch64', 'ppc64le', 's390x',
            'armv7hl', 'ppc64', 'sparc64', 'alpha', 'ia64'
        }
        valid_states = {'present', 'absent'}

        for i, host in enumerate(hosts_data):
            if not isinstance(host, dict):
                self.add_error('hosts.yml', f"Host entry {i+1} must be a dictionary")
                continue

            # Required fields
            if 'name' not in host:
                self.add_error('hosts.yml', f"Host entry {i+1} missing required 'name' field")
                continue

            name = host['name']
            if not isinstance(name, str) or not name.strip():
                self.add_error('hosts.yml', f"Host entry {i+1} 'name' must be a non-empty string")
                continue

            host_names.add(name)

            # Architecture validation
            if 'arches' in host:
                arches = host['arches']
                if not isinstance(arches, list):
                    self.add_error('hosts.yml', f"Host '{name}' arches must be a list")
                else:
                    for arch in arches:
                        if arch not in valid_arches:
                            self.add_warning('hosts.yml', f"Host '{name}' has unknown architecture '{arch}'. Common arches: {', '.join(sorted(valid_arches))}")

            # Capacity validation
            if 'capacity' in host:
                capacity = host['capacity']
                if not isinstance(capacity, (int, float)) or capacity <= 0:
                    self.add_error('hosts.yml', f"Host '{name}' capacity must be a positive number")

            # Enabled validation
            if 'enabled' in host:
                enabled = host['enabled']
                if not isinstance(enabled, bool):
                    self.add_error('hosts.yml', f"Host '{name}' enabled must be true or false")

            # State validation
            state = host.get('state', 'present')
            if state not in valid_states:
                self.add_error('hosts.yml', f"Host '{name}' state must be one of: {', '.join(valid_states)}")

        return host_names

    def validate_tags(self, tags_data: List[Dict]) -> Set[str]:
        """Validate tags configuration and return set of tag names"""
        tag_names = set()
        valid_states = {'present', 'absent'}

        for i, tag in enumerate(tags_data):
            if not isinstance(tag, dict):
                self.add_error('tags.yml', f"Tag entry {i+1} must be a dictionary")
                continue

            # Required fields
            if 'name' not in tag:
                self.add_error('tags.yml', f"Tag entry {i+1} missing required 'name' field")
                continue

            name = tag['name']
            if not isinstance(name, str) or not name.strip():
                self.add_error('tags.yml', f"Tag entry {i+1} 'name' must be a non-empty string")
                continue

            tag_names.add(name)

            # Parent validation (will be cross-referenced later)
            if 'parent' in tag and tag['parent'] is not None:
                parent = tag['parent']
                if not isinstance(parent, str):
                    self.add_error('tags.yml', f"Tag '{name}' parent must be a string or null")

            # Boolean field validation
            for field in ['locked', 'maven_support']:
                if field in tag and not isinstance(tag[field], bool):
                    self.add_error('tags.yml', f"Tag '{name}' {field} must be true or false")

            # State validation
            state = tag.get('state', 'present')
            if state not in valid_states:
                self.add_error('tags.yml', f"Tag '{name}' state must be one of: {', '.join(valid_states)}")

        return tag_names

    def validate_targets(self, targets_data: List[Dict], tag_names: Set[str]):
        """Validate targets configuration"""
        target_names = set()
        valid_states = {'present', 'absent'}

        for i, target in enumerate(targets_data):
            if not isinstance(target, dict):
                self.add_error('targets.yml', f"Target entry {i+1} must be a dictionary")
                continue

            # Required fields
            required_fields = ['name', 'build_tag', 'dest_tag']
            for field in required_fields:
                if field not in target:
                    self.add_error('targets.yml', f"Target entry {i+1} missing required '{field}' field")
                    continue

            name = target.get('name')
            if not isinstance(name, str) or not name.strip():
                self.add_error('targets.yml', f"Target entry {i+1} 'name' must be a non-empty string")
                continue

            if name in target_names:
                self.add_error('targets.yml', f"Duplicate target name '{name}'")
            target_names.add(name)

            # Cross-reference validation with tags
            build_tag = target.get('build_tag')
            dest_tag = target.get('dest_tag')

            if build_tag and build_tag not in tag_names:
                self.add_error('targets.yml', f"Target '{name}' references unknown build_tag '{build_tag}'")

            if dest_tag and dest_tag not in tag_names:
                self.add_error('targets.yml', f"Target '{name}' references unknown dest_tag '{dest_tag}'")

            # State validation
            state = target.get('state', 'present')
            if state not in valid_states:
                self.add_error('targets.yml', f"Target '{name}' state must be one of: {', '.join(valid_states)}")

    def validate_cross_references(self, tags_data: List[Dict], tag_names: Set[str]):
        """Validate cross-references within tags (parent relationships)"""
        for tag in tags_data:
            name = tag.get('name')
            parent = tag.get('parent')

            if parent and parent not in tag_names:
                self.add_error('tags.yml', f"Tag '{name}' references unknown parent '{parent}'")

    def validate_all(self) -> bool:
        """Validate all configuration files"""
        config_files = {
            'users.yml': self.config_dir / 'users.yml',
            'hosts.yml': self.config_dir / 'hosts.yml',
            'tags.yml': self.config_dir / 'tags.yml',
            'targets.yml': self.config_dir / 'targets.yml'
        }

        # Check if config directory exists
        if not self.config_dir.exists():
            self.add_error('', f"Configuration directory '{self.config_dir}' does not exist")
            return False

        # Parse all files
        parsed_data = {}
        for name, path in config_files.items():
            if not path.exists():
                self.add_warning(name, f"Configuration file '{path}' does not exist, skipping")
                parsed_data[name] = []
            else:
                data = self.validate_yaml_syntax(path)
                if data is None:
                    parsed_data[name] = []
                elif not isinstance(data, list):
                    self.add_error(name, "Configuration file must contain a list of items")
                    parsed_data[name] = []
                else:
                    parsed_data[name] = data

        # Validate individual file schemas
        user_names = self.validate_users(parsed_data.get('users.yml', []))
        host_names = self.validate_hosts(parsed_data.get('hosts.yml', []))
        tag_names = self.validate_tags(parsed_data.get('tags.yml', []))

        # Validate cross-references
        self.validate_cross_references(parsed_data.get('tags.yml', []), tag_names)
        self.validate_targets(parsed_data.get('targets.yml', []), tag_names)

        return len(self.errors) == 0

    def print_results(self, verbose: bool = False):
        """Print validation results"""
        if self.errors:
            print(f"❌ Found {len(self.errors)} error(s):")
            for error in self.errors:
                line_info = f":{error.line}" if error.line else ""
                print(f"  {error.file}{line_info}: {error.message}")
            print()

        if self.warnings:
            print(f"⚠️  Found {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                line_info = f":{warning.line}" if warning.line else ""
                print(f"  {warning.file}{line_info}: {warning.message}")
            print()

        if not self.errors and not self.warnings:
            print("✅ All configuration files are valid!")
        elif not self.errors:
            print("✅ Configuration is valid (with warnings)")
        else:
            print("❌ Configuration validation failed")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Koji ansible configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Validate ansible-configs/ directory
  %(prog)s --config-dir /path/to/configs      # Validate custom directory
  %(prog)s --verbose                          # Show detailed output
        """
    )

    parser.add_argument(
        '--config-dir',
        type=Path,
        default=Path('ansible-configs'),
        help='Path to ansible configuration directory (default: ansible-configs)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show verbose output'
    )

    args = parser.parse_args()

    # Validate configuration
    validator = ConfigValidator(args.config_dir)
    is_valid = validator.validate_all()
    validator.print_results(args.verbose)

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
