#!/usr/bin/env python3
"""Main entry point for iteration3 - Autonomous Agentic Commerce Application"""

from .agentic_ui import build_ui


def main():
    """Main entry point"""
    print("Starting Autonomous Agentic Shopping Application...")
    demo = build_ui()
    demo.launch(share=True)


if __name__ == "__main__":
    main()
