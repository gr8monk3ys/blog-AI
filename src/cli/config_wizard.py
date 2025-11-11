"""Configuration wizard for blog-AI setup."""

import os
import sys
from pathlib import Path
from typing import Any

try:
    import questionary
    from questionary import Style

    QUESTIONARY_AVAILABLE = True
except ImportError:
    QUESTIONARY_AVAILABLE = False


def check_questionary() -> None:
    """Check if questionary is installed and provide installation instructions."""
    if not QUESTIONARY_AVAILABLE:
        print("❌ Error: questionary is required for the configuration wizard")
        print("\nInstall it with:")
        print("  uv sync --all-extras")
        print("  or")
        print("  pip install questionary")
        sys.exit(1)


# Custom style for the wizard
WIZARD_STYLE = Style(
    [
        ("qmark", "fg:#673ab7 bold"),  # Question mark
        ("question", "bold"),  # Question text
        ("answer", "fg:#f44336 bold"),  # User's answer
        ("pointer", "fg:#673ab7 bold"),  # Pointer for selections
        ("highlighted", "fg:#673ab7 bold"),  # Highlighted choice
        ("selected", "fg:#cc5454"),  # Selected choice
        ("separator", "fg:#cc5454"),  # Separator
        ("instruction", ""),  # Instruction text
        ("text", ""),  # Plain text
        ("disabled", "fg:#858585 italic"),  # Disabled options
    ]
)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path.cwd()


def check_existing_config() -> dict[str, Any]:
    """Check for existing configuration."""
    root = get_project_root()
    env_file = root / ".env"
    toml_file = root / ".blog-ai.toml"

    existing: dict[str, Any] = {"env_exists": env_file.exists(), "toml_exists": toml_file.exists()}

    if existing["env_exists"]:
        # Try to read existing values
        existing["env_values"] = {}
        try:
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        existing["env_values"][key.strip()] = value.strip()
        except Exception:
            pass

    return existing


def create_env_file(config: dict[str, Any]) -> None:
    """Create .env file with configuration."""
    root = get_project_root()
    env_file = root / ".env"

    # Read template
    template_file = root / ".env.example"
    if template_file.exists():
        with open(template_file) as f:
            template = f.read()
    else:
        template = """# blog-AI Configuration
# Copy this file to .env and fill in your values

# === Required Settings ===

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# === Optional Settings ===

# Anthropic Configuration (optional)
# ANTHROPIC_API_KEY=your-anthropic-api-key-here

# LLM Settings
# LLM_TEMPERATURE=0.7
# LLM_MAX_TOKENS=4000

# Output Settings
# OUTPUT_DIR=content

# Logging
# LOG_LEVEL=INFO
"""

    # Replace placeholders with actual values
    env_content = template
    for key, value in config.items():
        if value:
            # Find the line with this key and replace it
            lines = env_content.split("\n")
            new_lines = []
            for line in lines:
                if line.strip().startswith(f"{key}=") or line.strip().startswith(f"# {key}="):
                    # Uncomment and set value
                    new_lines.append(f"{key}={value}")
                else:
                    new_lines.append(line)
            env_content = "\n".join(new_lines)

    # Write to .env
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"\n✓ Configuration saved to {env_file}")


def run_wizard() -> None:
    """Run the configuration wizard."""
    check_questionary()

    print("=" * 70)
    print("blog-AI Configuration Wizard")
    print("=" * 70)
    print("\nWelcome! This wizard will help you set up blog-AI.\n")

    # Check existing configuration
    existing = check_existing_config()

    if existing["env_exists"]:
        overwrite = questionary.confirm(
            "A .env file already exists. Do you want to overwrite it?",
            default=False,
            style=WIZARD_STYLE,
        ).ask()

        if not overwrite:
            print("\n✓ Keeping existing configuration")
            sys.exit(0)

    config: dict[str, Any] = {}

    # Step 1: API Provider Selection
    print("\n" + "=" * 70)
    print("Step 1: API Provider")
    print("=" * 70)

    providers = questionary.checkbox(
        "Which LLM providers do you want to use?",
        choices=[
            questionary.Choice("OpenAI (GPT-4, GPT-3.5)", value="openai", checked=True),
            questionary.Choice("Anthropic Claude", value="anthropic"),
        ],
        style=WIZARD_STYLE,
    ).ask()

    if not providers:
        print("\n❌ Error: You must select at least one provider")
        sys.exit(1)

    # Step 2: API Keys
    print("\n" + "=" * 70)
    print("Step 2: API Keys")
    print("=" * 70)
    print("\nNote: Your API keys will be stored securely in .env file")
    print("The .env file is gitignored and will not be committed to version control\n")

    if "openai" in providers:
        # Check if key exists
        existing_key = existing.get("env_values", {}).get("OPENAI_API_KEY", "")
        if existing_key and existing_key != "your-openai-api-key-here":
            use_existing = questionary.confirm(
                f"Use existing OpenAI API key ({existing_key[:10]}...)? ",
                default=True,
                style=WIZARD_STYLE,
            ).ask()
            if use_existing:
                config["OPENAI_API_KEY"] = existing_key
            else:
                config["OPENAI_API_KEY"] = questionary.password(
                    "Enter your OpenAI API key:", style=WIZARD_STYLE
                ).ask()
        else:
            config["OPENAI_API_KEY"] = questionary.password(
                "Enter your OpenAI API key:", style=WIZARD_STYLE
            ).ask()

    if "anthropic" in providers:
        existing_key = existing.get("env_values", {}).get("ANTHROPIC_API_KEY", "")
        if existing_key and existing_key != "your-anthropic-api-key-here":
            use_existing = questionary.confirm(
                f"Use existing Anthropic API key ({existing_key[:10]}...)? ",
                default=True,
                style=WIZARD_STYLE,
            ).ask()
            if use_existing:
                config["ANTHROPIC_API_KEY"] = existing_key
            else:
                config["ANTHROPIC_API_KEY"] = questionary.password(
                    "Enter your Anthropic API key:", style=WIZARD_STYLE
                ).ask()
        else:
            config["ANTHROPIC_API_KEY"] = questionary.password(
                "Enter your Anthropic API key:", style=WIZARD_STYLE
            ).ask()

    # Step 3: Default Settings
    print("\n" + "=" * 70)
    print("Step 3: Default Settings")
    print("=" * 70)

    configure_defaults = questionary.confirm(
        "Would you like to configure default settings? (You can skip this)",
        default=False,
        style=WIZARD_STYLE,
    ).ask()

    if configure_defaults:
        # Temperature
        config["LLM_TEMPERATURE"] = questionary.text(
            "LLM temperature (0.0-2.0, default: 0.7):",
            default="0.7",
            style=WIZARD_STYLE,
        ).ask()

        # Max tokens
        config["LLM_MAX_TOKENS"] = questionary.text(
            "Max tokens per request (default: 4000):",
            default="4000",
            style=WIZARD_STYLE,
        ).ask()

        # Output directory
        config["OUTPUT_DIR"] = questionary.text(
            "Output directory for generated content:",
            default="content",
            style=WIZARD_STYLE,
        ).ask()

        # Log level
        config["LOG_LEVEL"] = questionary.select(
            "Logging level:",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            default="INFO",
            style=WIZARD_STYLE,
        ).ask()

    # Step 4: Validation
    print("\n" + "=" * 70)
    print("Step 4: Validation")
    print("=" * 70)

    validate = questionary.confirm(
        "Would you like to validate your API keys?",
        default=True,
        style=WIZARD_STYLE,
    ).ask()

    if validate:
        print("\nValidating API keys...")
        # Set environment variables temporarily for validation
        if "OPENAI_API_KEY" in config:
            os.environ["OPENAI_API_KEY"] = config["OPENAI_API_KEY"]
        if "ANTHROPIC_API_KEY" in config:
            os.environ["ANTHROPIC_API_KEY"] = config["ANTHROPIC_API_KEY"]

        # Try to validate
        validation_passed = True

        if "openai" in providers and "OPENAI_API_KEY" in config:
            try:
                from ..services.llm.openai import OpenAIProvider

                provider = OpenAIProvider()
                # Try a minimal generation
                result = provider.generate("Say 'test' only", max_tokens=10)
                if result:
                    print("✓ OpenAI API key is valid")
                else:
                    print("❌ OpenAI API key validation failed")
                    validation_passed = False
            except Exception as e:
                print(f"❌ OpenAI validation error: {e}")
                validation_passed = False

        if "anthropic" in providers and "ANTHROPIC_API_KEY" in config:
            try:
                from ..services.llm.anthropic import AnthropicProvider

                provider = AnthropicProvider()
                result = provider.generate("Say 'test' only", max_tokens=10)
                if result:
                    print("✓ Anthropic API key is valid")
                else:
                    print("❌ Anthropic API key validation failed")
                    validation_passed = False
            except Exception as e:
                print(f"❌ Anthropic validation error: {e}")
                validation_passed = False

        if not validation_passed:
            continue_anyway = questionary.confirm(
                "\nSome validations failed. Continue anyway?",
                default=False,
                style=WIZARD_STYLE,
            ).ask()
            if not continue_anyway:
                print("\n❌ Configuration cancelled")
                sys.exit(1)

    # Step 5: Save Configuration
    print("\n" + "=" * 70)
    print("Step 5: Save Configuration")
    print("=" * 70)

    confirm = questionary.confirm(
        "Save this configuration?",
        default=True,
        style=WIZARD_STYLE,
    ).ask()

    if confirm:
        create_env_file(config)

        # Create output directory if specified
        if "OUTPUT_DIR" in config:
            output_dir = Path(config["OUTPUT_DIR"])
            output_dir.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created output directory: {output_dir}")

        print("\n" + "=" * 70)
        print("✓ Configuration Complete!")
        print("=" * 70)
        print("\nYou're all set! Try generating your first blog post:")
        print("\n  blog-ai-blog 'Your Topic Here'")
        print("\nOr generate a book:")
        print("\n  blog-ai-book 'Your Book Topic'")
        print("\nFor more options, see:")
        print("\n  blog-ai-blog --help")
        print("\n" + "=" * 70)
    else:
        print("\n❌ Configuration cancelled")
        sys.exit(1)


def main() -> int:
    """Main entry point for the configuration wizard."""
    try:
        run_wizard()
        return 0
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
