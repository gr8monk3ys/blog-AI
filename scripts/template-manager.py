#!/usr/bin/env python3
"""Template management utility for blog-AI.

List, view, and manage prompt templates.
Run: python scripts/template-manager.py
"""

import sys
from pathlib import Path


def find_templates() -> dict[str, list[Path]]:
    """Find all available templates."""
    templates_dir = Path("templates/prompts")

    if not templates_dir.exists():
        return {}

    templates = {
        "blog": [],
        "book": [],
        "other": [],
    }

    for template_file in templates_dir.glob("*.txt"):
        name = template_file.stem
        if name.startswith("blog_"):
            templates["blog"].append(template_file)
        elif name.startswith("book_"):
            templates["book"].append(template_file)
        else:
            templates["other"].append(template_file)

    return templates


def list_templates():
    """List all available templates."""
    print("=" * 70)
    print("📋 Available Prompt Templates")
    print("=" * 70)

    templates = find_templates()

    if not any(templates.values()):
        print("\n❌ No templates found in templates/prompts/")
        print("\nCreate templates by adding .txt files to templates/prompts/")
        return

    if templates["blog"]:
        print("\n📝 Blog Templates:")
        for template in sorted(templates["blog"]):
            name = template.stem.replace("blog_", "")
            print(f"  - {name:20} ({template.name})")

    if templates["book"]:
        print("\n📚 Book Templates:")
        for template in sorted(templates["book"]):
            name = template.stem.replace("book_", "")
            print(f"  - {name:20} ({template.name})")

    if templates["other"]:
        print("\n📄 Other Templates:")
        for template in sorted(templates["other"]):
            print(f"  - {template.stem:20} ({template.name})")

    print(f"\nTotal templates: {sum(len(v) for v in templates.values())}")


def view_template(template_name: str):
    """View a specific template."""
    templates_dir = Path("templates/prompts")
    template_file = templates_dir / f"{template_name}.txt"

    if not template_file.exists():
        # Try with blog_ or book_ prefix
        for prefix in ["blog_", "book_", ""]:
            alt_file = templates_dir / f"{prefix}{template_name}.txt"
            if alt_file.exists():
                template_file = alt_file
                break

    if not template_file.exists():
        print(f"❌ Template not found: {template_name}")
        print("\nUse 'python scripts/template-manager.py list' to see available templates")
        return

    print("=" * 70)
    print(f"📄 Template: {template_file.name}")
    print("=" * 70)

    with open(template_file, encoding="utf-8") as f:
        content = f.read()

    print(content)

    print("\n" + "=" * 70)
    print(f"Template location: {template_file}")


def show_template_variables(template_name: str):
    """Show variables used in a template."""
    templates_dir = Path("templates/prompts")
    template_file = templates_dir / f"{template_name}.txt"

    if not template_file.exists():
        for prefix in ["blog_", "book_", ""]:
            alt_file = templates_dir / f"{prefix}{template_name}.txt"
            if alt_file.exists():
                template_file = alt_file
                break

    if not template_file.exists():
        print(f"❌ Template not found: {template_name}")
        return

    with open(template_file, encoding="utf-8") as f:
        content = f.read()

    import re

    variables = set(re.findall(r"\{(\w+)\}", content))

    print("=" * 70)
    print(f"📋 Variables in {template_file.name}")
    print("=" * 70)

    if variables:
        for var in sorted(variables):
            print(f"  - {{{var}}}")
    else:
        print("  No variables found")

    print(f"\nTotal variables: {len(variables)}")


def create_template():
    """Interactive template creation."""
    print("=" * 70)
    print("✨ Create New Template")
    print("=" * 70)

    name = input("\nTemplate name (e.g., blog_tutorial): ").strip()
    if not name:
        print("❌ Template name cannot be empty")
        return

    if not name.endswith(".txt"):
        name += ".txt"

    templates_dir = Path("templates/prompts")
    templates_dir.mkdir(parents=True, exist_ok=True)

    template_file = templates_dir / name

    if template_file.exists():
        overwrite = input(f"⚠️  Template {name} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != "y":
            print("Cancelled")
            return

    print("\nEnter template content (press Ctrl+D or Ctrl+Z when done):")
    print("Tip: Use {variable_name} for placeholders")
    print("-" * 70)

    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass

    content = "\n".join(lines)

    with open(template_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n✅ Created template: {template_file}")


def interactive_mode():
    """Interactive template management."""
    print("=" * 70)
    print("🎨 Template Manager")
    print("=" * 70)

    print("\nWhat would you like to do?")
    print("1. List all templates")
    print("2. View template")
    print("3. Show template variables")
    print("4. Create new template")
    print("5. Exit")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        list_templates()
    elif choice == "2":
        template = input("Enter template name: ").strip()
        view_template(template)
    elif choice == "3":
        template = input("Enter template name: ").strip()
        show_template_variables(template)
    elif choice == "4":
        create_template()
    elif choice == "5":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice")


def main():
    """Main entry point."""
    if not Path("templates/prompts").exists():
        Path("templates/prompts").mkdir(parents=True, exist_ok=True)
        print("✅ Created templates/prompts directory")

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "list":
            list_templates()
        elif command == "view" and len(sys.argv) > 2:
            view_template(sys.argv[2])
        elif command == "vars" and len(sys.argv) > 2:
            show_template_variables(sys.argv[2])
        elif command == "create":
            create_template()
        else:
            print("Usage:")
            print("  python scripts/template-manager.py list")
            print("  python scripts/template-manager.py view <template>")
            print("  python scripts/template-manager.py vars <template>")
            print("  python scripts/template-manager.py create")
            sys.exit(1)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
