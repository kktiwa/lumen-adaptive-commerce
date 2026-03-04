#!/usr/bin/env python3
"""Main entry point for iteration2 - Conversational Shopping Assistant"""

from .chat_ui import build_ui

def main():
    """Main entry point"""
    print("Starting Conversational Shopping Assistant...")
    demo = build_ui()
    demo.launch(share=True)

if __name__ == "__main__":
    main()

