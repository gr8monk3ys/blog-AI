"""Template management CLI for blog-AI."""

import argparse
import json
import logging
import sys
from pathlib import Path

from ..utils.logging import setup_logging
from ..utils.templates import (
    ContentTemplate,
    TemplateManager,
    create_default_blog_template,
    create_default_faq_template,
)

logger = logging.getLogger(__name__)


def cmd_list(args: argparse.Namespace) -> int:
    """List all templates."""
    manager = TemplateManager(templates_dir=Path(args.templates_dir))

    templates = manager.list()

    if not templates:
        print("No templates found.")
        print(f"\nTemplates directory: {manager.templates_dir}")
        print("\nCreate a new template with: blog-ai-template create")
        return 0

    print("=" * 70)
    print(f"Available Templates ({len(templates)})")
    print("=" * 70)

    for template in templates:
        print(f"\n📄 {template.name}")
        print(f"   Description: {template.description}")
        print(f"   Type: {template.content_type}")
        print(f"   Version: {template.version}")
        if template.author:
            print(f"   Author: {template.author}")
        if template.tags:
            print(f"   Tags: {', '.join(template.tags)}")

    print("\n" + "=" * 70)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    """Show template details."""
    manager = TemplateManager(templates_dir=Path(args.templates_dir))

    try:
        template = manager.load(args.name)

        print("=" * 70)
        print(f"Template: {template.metadata.name}")
        print("=" * 70)

        # Metadata
        print("\n📋 Metadata:")
        print(f"  Description: {template.metadata.description}")
        print(f"  Type: {template.metadata.content_type}")
        print(f"  Version: {template.metadata.version}")
        if template.metadata.author:
            print(f"  Author: {template.metadata.author}")
        if template.metadata.tags:
            print(f"  Tags: {', '.join(template.metadata.tags)}")

        # Prompts
        if template.prompts:
            print("\n💬 Prompts:")
            for name, prompt in template.prompts.items():
                print(f"  - {name}:")
                if prompt.system_prompt:
                    print(f"    System: {prompt.system_prompt[:100]}...")
                print(f"    User: {prompt.user_prompt_template[:100]}...")
                if prompt.placeholders:
                    print(f"    Placeholders: {', '.join(prompt.placeholders.keys())}")

        # Structure
        if template.structure:
            print("\n🏗️  Structure:")
            if template.structure.sections:
                print(f"  Sections: {template.structure.sections}")
            if template.structure.subsections_per_section:
                print(f"  Subsections per section: {template.structure.subsections_per_section}")
            if template.structure.min_words:
                print(f"  Min words: {template.structure.min_words}")
            if template.structure.max_words:
                print(f"  Max words: {template.structure.max_words}")
            print(f"  Introduction: {template.structure.include_introduction}")
            print(f"  Conclusion: {template.structure.include_conclusion}")

        # Parameters
        if template.parameters:
            print("\n⚙️  Parameters:")
            if template.parameters.temperature is not None:
                print(f"  Temperature: {template.parameters.temperature}")
            if template.parameters.max_tokens:
                print(f"  Max tokens: {template.parameters.max_tokens}")
            if template.parameters.model:
                print(f"  Model: {template.parameters.model}")
            if template.parameters.provider:
                print(f"  Provider: {template.parameters.provider}")

        # Examples
        if template.examples:
            print(f"\n📚 Examples: {len(template.examples)}")

        print("\n" + "=" * 70)
        return 0

    except FileNotFoundError:
        print(f"❌ Template '{args.name}' not found")
        print(f"\nAvailable templates: {', '.join(t.name for t in manager.list())}")
        return 1
    except Exception as e:
        print(f"❌ Error loading template: {e}")
        return 1


def cmd_init_defaults(args: argparse.Namespace) -> int:
    """Initialize default templates."""
    manager = TemplateManager(templates_dir=Path(args.templates_dir))

    templates = [
        ("default-blog", create_default_blog_template()),
        ("default-faq", create_default_faq_template()),
    ]

    created = []
    skipped = []

    for name, template in templates:
        if manager.exists(name) and not args.force:
            skipped.append(name)
            continue

        manager.save(template)
        created.append(name)

    print("=" * 70)
    print("Initialize Default Templates")
    print("=" * 70)

    if created:
        print(f"\n✓ Created {len(created)} template(s):")
        for name in created:
            print(f"  - {name}")

    if skipped:
        print(f"\n⚠️  Skipped {len(skipped)} existing template(s):")
        for name in skipped:
            print(f"  - {name}")
        print("\nUse --force to overwrite existing templates")

    print(f"\nTemplates directory: {manager.templates_dir}")
    print("\n" + "=" * 70)
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    """Delete a template."""
    manager = TemplateManager(templates_dir=Path(args.templates_dir))

    if manager.delete(args.name):
        print(f"✓ Deleted template: {args.name}")
        return 0
    else:
        print(f"❌ Template '{args.name}' not found")
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Export a template."""
    manager = TemplateManager(templates_dir=Path(args.templates_dir))

    try:
        output_path = Path(args.output)
        manager.export(args.name, output_path)
        print(f"✓ Exported template '{args.name}' to {output_path}")
        return 0
    except FileNotFoundError:
        print(f"❌ Template '{args.name}' not found")
        return 1
    except Exception as e:
        print(f"❌ Error exporting template: {e}")
        return 1


def cmd_import(args: argparse.Namespace) -> int:
    """Import a template."""
    manager = TemplateManager(templates_dir=Path(args.templates_dir))

    try:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ File not found: {input_path}")
            return 1

        template = manager.import_template(input_path, name=args.name)
        print(f"✓ Imported template: {template.metadata.name}")
        return 0
    except Exception as e:
        print(f"❌ Error importing template: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a template file."""
    try:
        input_path = Path(args.file)
        if not input_path.exists():
            print(f"❌ File not found: {input_path}")
            return 1

        with open(input_path, encoding="utf-8") as f:
            template_dict = json.load(f)

        # Try to parse as template
        template = ContentTemplate(**template_dict)

        print("=" * 70)
        print(f"✓ Template is valid: {template.metadata.name}")
        print("=" * 70)
        print(f"Type: {template.metadata.content_type}")
        print(f"Version: {template.metadata.version}")
        print(f"Prompts: {len(template.prompts)}")
        if template.structure:
            print("Structure: ✓")
        if template.parameters:
            print("Parameters: ✓")
        print("=" * 70)
        return 0

    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return 1
    except Exception as e:
        print(f"❌ Invalid template: {e}")
        return 1


def main() -> int:
    """Main CLI entry point for template management."""
    parser = argparse.ArgumentParser(
        description="Manage content generation templates for blog-AI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--templates-dir",
        type=str,
        default="templates",
        help="Templates directory",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    subparsers.add_parser("list", help="List all templates")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show template details")
    show_parser.add_argument("name", help="Template name")

    # Init defaults command
    init_parser = subparsers.add_parser("init-defaults", help="Initialize default templates")
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing templates",
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a template")
    delete_parser.add_argument("name", help="Template name")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export a template")
    export_parser.add_argument("name", help="Template name")
    export_parser.add_argument("output", help="Output file path")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import a template")
    import_parser.add_argument("input", help="Input file path")
    import_parser.add_argument(
        "--name",
        help="Override template name",
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a template file")
    validate_parser.add_argument("file", help="Template file to validate")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level)

    # Route to command
    if args.command == "list":
        return cmd_list(args)
    elif args.command == "show":
        return cmd_show(args)
    elif args.command == "init-defaults":
        return cmd_init_defaults(args)
    elif args.command == "delete":
        return cmd_delete(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "import":
        return cmd_import(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
