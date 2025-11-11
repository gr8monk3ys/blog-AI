"""API server CLI for blog-AI."""

import argparse
import sys


def main() -> int:
    """Main entry point for API server."""
    parser = argparse.ArgumentParser(
        description="Run the blog-AI REST API server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Logging level",
    )

    args = parser.parse_args()

    try:
        import uvicorn

        print("=" * 70)
        print("blog-AI REST API Server")
        print("=" * 70)
        print(f"Starting server at http://{args.host}:{args.port}")
        print(f"API documentation: http://{args.host}:{args.port}/docs")
        print(f"Alternative docs: http://{args.host}:{args.port}/redoc")
        print("=" * 70)
        print("\nPress CTRL+C to stop the server\n")

        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=args.workers if not args.reload else 1,
            log_level=args.log_level,
        )

        return 0

    except ImportError:
        print("❌ Error: uvicorn is required to run the API server")
        print("\nInstall it with:")
        print("  uv sync --all-extras")
        print("  or")
        print("  pip install uvicorn")
        return 1
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
