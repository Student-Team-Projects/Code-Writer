#!/usr/bin/env python3
"""
Config profile manager — list, view, and switch between configuration profiles.

Usage:
    python config_manager.py list              # List all available profiles
    python config_manager.py view <profile>    # View a specific profile
    python config_manager.py switch <profile>  # Switch to a profile
    python config_manager.py current           # Show the active profile
"""

import os
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
PROFILES_DIR = CONFIG_DIR / "profiles"


def load_json(path):
    """Load and parse a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    """Save data to a JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def list_profiles():
    """List all available profiles."""
    if not PROFILES_DIR.exists():
        print("❌ Profiles directory not found:", PROFILES_DIR)
        return

    profiles = sorted([f[:-5] for f in os.listdir(PROFILES_DIR) if f.endswith(".json")])
    
    if not profiles:
        print("❌ No profiles found in:", PROFILES_DIR)
        return

    active_profile = get_active_profile()
    print("📋 Available profiles:")
    for profile in profiles:
        marker = " ✓" if profile == active_profile else ""
        profile_file = PROFILES_DIR / f"{profile}.json"
        profile_data = load_json(profile_file)
        name = profile_data.get("name", profile)
        description = profile_data.get("description", "")
        print(f"  {marker} {profile:15} → {name}")
        if description:
            print(f"    {description}")


def view_profile(profile_name):
    """View the contents of a specific profile."""
    profile_file = PROFILES_DIR / f"{profile_name}.json"
    
    if not profile_file.exists():
        print(f"❌ Profile '{profile_name}' not found")
        list_profiles()
        return

    data = load_json(profile_file)
    print(f"📄 Profile: {profile_name}")
    print(json.dumps(data, indent=2))


def switch_profile(profile_name):
    """Switch to a different profile."""
    profile_file = PROFILES_DIR / f"{profile_name}.json"
    
    if not profile_file.exists():
        print(f"❌ Profile '{profile_name}' not found")
        list_profiles()
        return

    settings = load_json(SETTINGS_FILE)
    settings["active_profile"] = profile_name
    save_json(SETTINGS_FILE, settings)

    profile_data = load_json(profile_file)
    print(f"✅ Switched to profile: {profile_name}")
    print(f"   Name: {profile_data.get('name', 'N/A')}")
    print(f"   Description: {profile_data.get('description', 'N/A')}")
    print(f"   Provider: {profile_data.get('model', {}).get('provider', 'N/A')}")


def get_active_profile():
    """Get the currently active profile."""
    if not SETTINGS_FILE.exists():
        return None
    settings = load_json(SETTINGS_FILE)
    return settings.get("active_profile", "default")


def show_current():
    """Show the currently active profile."""
    active = get_active_profile()
    if not active:
        print("❌ No active profile configured")
        return

    profile_file = PROFILES_DIR / f"{active}.json"
    if not profile_file.exists():
        print(f"❌ Active profile '{active}' not found")
        return

    data = load_json(profile_file)
    print(f"🎯 Active profile: {active}")
    print(f"   Name: {data.get('name', 'N/A')}")
    print(f"   Description: {data.get('description', 'N/A')}")
    print(f"   Model provider: {data.get('model', {}).get('provider', 'N/A')}")
    print(f"   Model: {data.get('model', {}).get('model', 'N/A')}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "list":
        list_profiles()
    elif command == "view":
        if len(sys.argv) < 3:
            print("Usage: python config_manager.py view <profile>")
            list_profiles()
            return
        view_profile(sys.argv[2])
    elif command == "switch":
        if len(sys.argv) < 3:
            print("Usage: python config_manager.py switch <profile>")
            list_profiles()
            return
        switch_profile(sys.argv[2])
    elif command == "current":
        show_current()
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
