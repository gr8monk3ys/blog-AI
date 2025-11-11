#!/usr/bin/env python3
"""Performance benchmark script for blog-AI.

Benchmarks key operations to track performance over time.
Run: python scripts/benchmark.py
"""

import time
from pathlib import Path
from typing import Callable

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.blog import BlogMetadata, BlogPost, BlogSection
from src.models.book import Book, Chapter
from src.models.common import Topic
from src.services.formatters.mdx import MDXFormatter
from src.services.formatters.docx import DOCXFormatter


def benchmark(func: Callable, name: str, iterations: int = 100) -> float:
    """Benchmark a function and return average time in ms."""
    times = []

    # Warmup
    func()

    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"\n{name}:")
    print(f"  Average: {avg_time:.3f}ms")
    print(f"  Min: {min_time:.3f}ms")
    print(f"  Max: {max_time:.3f}ms")

    return avg_time


def create_sample_blog() -> BlogPost:
    """Create a sample blog post for benchmarking."""
    return BlogPost(
        metadata=BlogMetadata(
            title="Performance Benchmarking in Python",
            description="Learn how to benchmark Python code effectively",
            tags=["python", "performance", "benchmarking"],
            topic="Performance Testing",
            author="Benchmark Bot",
            read_time_minutes=5,
        ),
        sections=[
            BlogSection(
                heading="Introduction to Benchmarking",
                content="Learn about benchmarking best practices...",
                topics=[
                    Topic(
                        title="Why benchmark?",
                        content="Benchmarking helps identify performance bottlenecks...",
                        word_count=10,
                    ),
                    Topic(
                        title="Benchmarking best practices",
                        content="Always warm up your code before measuring...",
                        word_count=10,
                    ),
                ],
            ),
            BlogSection(
                heading="Tools and Techniques",
                content="Explore various benchmarking tools...",
                topics=[
                    Topic(
                        title="Using timeit module",
                        content="Python's timeit module is perfect for micro-benchmarks...",
                        word_count=10,
                    ),
                    Topic(
                        title="Profiling with cProfile",
                        content="For more detailed analysis, use cProfile...",
                        word_count=10,
                    ),
                ],
            ),
        ],
        word_count=100,
    )


def create_sample_book() -> Book:
    """Create a sample book for benchmarking."""
    return Book(
        title="Python Performance Guide",
        subtitle="Benchmarking Edition",
        author="Benchmark Bot",
        topic="Performance Testing",
        chapters=[
            Chapter(
                number=i + 1,
                title=f"Chapter {i + 1}: Performance Topic",
                topics=[
                    Topic(
                        title=f"Topic {j + 1}",
                        content="This is sample content. " * 100,
                        word_count=100,
                    )
                    for j in range(3)
                ],
                word_count=300,
            )
            for i in range(5)
        ],
        word_count=1500,
    )


def main():
    """Run all benchmarks."""
    print("=" * 70)
    print("🚀 blog-AI Performance Benchmarks")
    print("=" * 70)

    results = {}

    # Benchmark 1: Model creation
    print("\n📊 Benchmarking Model Creation...")
    results["blog_creation"] = benchmark(
        lambda: BlogPost(
            metadata=BlogMetadata(
                title="Test",
                description="Test description",
                tags=["test"],
                topic="Testing",
                author="Test",
                read_time_minutes=5,
            ),
            sections=[
                BlogSection(
                    heading="Section",
                    content="Test content",
                    topics=[
                        Topic(
                            title="Topic",
                            content="Content",
                            word_count=1,
                        )
                    ],
                )
            ],
            word_count=10,
        ),
        "BlogPost Model Creation",
        iterations=1000,
    )

    results["book_creation"] = benchmark(
        lambda: Book(
            title="Test Book",
            subtitle="Test",
            author="Test",
            topic="Testing",
            chapters=[
                Chapter(
                    number=1,
                    title="Chapter 1",
                    topics=[
                        Topic(
                            title="Topic",
                            content="Content",
                            word_count=1,
                        )
                    ],
                    word_count=1,
                )
            ],
            word_count=1,
        ),
        "Book Model Creation",
        iterations=1000,
    )

    # Benchmark 2: MDX Formatting
    print("\n📊 Benchmarking MDX Formatting...")
    blog = create_sample_blog()
    mdx_formatter = MDXFormatter()
    results["mdx_formatting"] = benchmark(
        lambda: mdx_formatter.format(blog),
        "MDX Format (Blog Post)",
        iterations=100,
    )

    # Benchmark 3: DOCX Formatting
    print("\n📊 Benchmarking DOCX Formatting...")
    book = create_sample_book()
    docx_formatter = DOCXFormatter()
    results["docx_formatting"] = benchmark(
        lambda: docx_formatter.format(book),
        "DOCX Format (Book)",
        iterations=50,
    )

    # Benchmark 4: Model Validation
    print("\n📊 Benchmarking Model Validation...")
    results["validation"] = benchmark(
        lambda: BlogMetadata(
            title="Test Title",
            description="A" * 160,  # Max length
            tags=["tag1", "tag2", "tag3"],
            topic="Testing",
            author="Test Author",
            read_time_minutes=5,
        ),
        "BlogMetadata Validation",
        iterations=1000,
    )

    # Summary
    print("\n" + "=" * 70)
    print("📈 Benchmark Summary")
    print("=" * 70)

    for name, time_ms in sorted(results.items(), key=lambda x: x[1]):
        print(f"{name:30} {time_ms:8.3f}ms")

    # Performance targets
    print("\n" + "=" * 70)
    print("🎯 Performance Targets")
    print("=" * 70)
    print("✓ Model creation: <1ms (fast object instantiation)")
    print("✓ MDX formatting: <50ms (lightweight text processing)")
    print("✓ DOCX formatting: <200ms (includes binary document creation)")
    print("✓ Validation: <1ms (Pydantic is highly optimized)")

    # Check if targets are met
    print("\n" + "=" * 70)
    print("✅ Results:")
    print("=" * 70)

    checks = [
        (results["blog_creation"] < 1.0, "Blog creation"),
        (results["book_creation"] < 1.0, "Book creation"),
        (results["mdx_formatting"] < 50.0, "MDX formatting"),
        (results["docx_formatting"] < 200.0, "DOCX formatting"),
        (results["validation"] < 1.0, "Validation"),
    ]

    all_passed = True
    for passed, name in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All performance targets met!")
    else:
        print("⚠️  Some performance targets not met. Consider optimization.")
    print("=" * 70)


if __name__ == "__main__":
    main()
