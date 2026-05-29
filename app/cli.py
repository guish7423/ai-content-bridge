#!/usr/bin/env python3
"""AI Content Bridge — CLI for testing."""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bridge import process, process_quick


def main():
    parser = argparse.ArgumentParser(description="AI Content Bridge CLI")
    parser.add_argument("text", nargs="?", help="Chinese text to translate")
    parser.add_argument("--file", "-f", type=Path, help="Read text from file")
    parser.add_argument("--platform", "-p", default="x", choices=["x", "linkedin", "reddit", "blog"],
                        help="Target platform (default: x)")
    parser.add_argument("--quick", "-q", action="store_true",
                        help="Quick mode - single platform, text only")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Process for all platforms")
    parser.add_argument("--json", "-j", action="store_true",
                        help="Output raw JSON")

    args = parser.parse_args()

    text = args.text
    if args.file:
        text = args.file.read_text(encoding="utf-8")
    if not text:
        text = sys.stdin.read()

    if args.quick:
        content = process_quick(text, args.platform)
        if args.json:
            print(json.dumps({"platform": args.platform, "content": content}, ensure_ascii=False, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"  📱 {args.platform.upper()}")
            print(f"{'='*60}\n")
            print(content)
        return

    platforms = ["x", "linkedin", "reddit", "blog"] if args.all else [args.platform]
    result = process(text, platforms)

    if args.json:
        print(json.dumps({
            "original": result.original_text,
            "analysis": result.analysis,
            "localized": result.localized_text,
            "platforms": result.platform_versions,
        }, ensure_ascii=False, indent=2))
        return

    # Pretty print
    print(f"\n{'='*60}")
    print(f"  📝 Original ({len(text)} chars)")
    print(f"{'='*60}\n{text}\n")

    print(f"{'='*60}")
    print(f"  🔍 Analysis")
    print(f"{'='*60}")
    for k, v in result.analysis.items():
        if isinstance(v, list):
            print(f"\n  {k}:")
            for item in v:
                print(f"    • {item}")
        else:
            print(f"\n  {k}: {v}")

    print(f"\n{'='*60}")
    print(f"  🌐 Localized")
    print(f"{'='*60}\n{result.localized_text}\n")

    for platform, data in result.platform_versions.items():
        print(f"{'='*60}")
        print(f"  📱 {platform.upper()}")
        print(f"{'='*60}\n{data['content']}\n")
        if data.get("hashtags"):
            print(f"  Hashtags: {' '.join(data['hashtags'])}\n")
        if data.get("notes"):
            print(f"  💡 {data['notes']}\n")

    u = result.usage
    print(f"{'='*60}")
    print(f"  📊 Usage: {u['calls']} calls, {u['tokens']} tokens, ${u['cost_usd']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
