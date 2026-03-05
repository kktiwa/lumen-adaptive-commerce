#!/usr/bin/env python3
"""
LLM Output Eval Framework
=========================
Evaluates AI-generated personalized product descriptions across 9 sections
using OpenAI as an LLM-as-judge scorer.

Requirements:
    pip install openai rich python-dotenv

Usage:
    python llm_eval_framework.py
    python llm_eval_framework.py --api-key sk-proj-...   # or set OPENAI_API_KEY env var
    python llm_eval_framework.py --input sample.json    # load from JSON file
    python llm_eval_framework.py --output report.json   # save results to JSON
"""

import os
import sys
import json
import re
import time
import argparse
import concurrent.futures
from dataclasses import dataclass, field, asdict
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; use OPENAI_API_KEY env var directly

try:
    from openai import OpenAI
except ImportError:
    print("❌  Missing dependency: pip install openai rich")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.text import Text
    from rich.columns import Columns
    from rich.rule import Rule
    from rich import box
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.layout import Layout
    from rich.align import Align
except ImportError:
    print("❌  Missing dependency: pip install openai rich")
    sys.exit(1)

console = Console()

# ─────────────────────────────────────────────
# SECTION DEFINITIONS
# ─────────────────────────────────────────────

SECTIONS = [
    {
        "key": "header",
        "label": "Header",
        "icon": "H1",
        "description": "Main headline of the product description",
        "criteria": ["persona_alignment", "value_proposition", "specificity", "memorability"],
        "rubric": (
            "Score the Header on these criteria (1-5 each, score out of 5):\n"
            "1. persona_alignment: Does it speak directly to a specific user segment or persona?\n"
            "2. value_proposition: Is the core product benefit immediately clear?\n"
            "3. specificity: Avoids vague/generic language — feels tailored not templated?\n"
            "4. memorability: Would this header stop someone while scrolling?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object — no markdown fences, no explanation:\n"
            '{"scores":{"persona_alignment":<score>,"value_proposition":<score>,"specificity":<score>,"memorability":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "subheader",
        "label": "Subheader",
        "icon": "H2",
        "description": "Secondary headline supporting the header",
        "criteria": ["complementarity", "secondary_benefit", "natural_flow", "conciseness"],
        "rubric": (
            "Score the Subheader on these criteria (1-5 each, score out of 5):\n"
            "1. complementarity: Does it expand on the header without repeating it?\n"
            "2. secondary_benefit: Does it introduce a new angle or benefit?\n"
            "3. natural_flow: Does it read naturally after the header?\n"
            "4. conciseness: Is it appropriately brief and scannable?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"complementarity":<score>,"secondary_benefit":<score>,"natural_flow":<score>,"conciseness":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "tagline",
        "label": "Tagline",
        "icon": "™",
        "description": "Short, memorable brand statement",
        "criteria": ["brevity", "emotional_resonance", "brand_voice", "memorability"],
        "rubric": (
            "Score the Tagline on these criteria (1-5 each, score out of 5):\n"
            "1. brevity: Is it under 10 words and punchy?\n"
            "2. emotional_resonance: Does it evoke a feeling or aspiration?\n"
            "3. brand_voice: Does the tone feel consistent and intentional?\n"
            "4. memorability: Is it catchy and distinctive — not generic?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"brevity":<score>,"emotional_resonance":<score>,"brand_voice":<score>,"memorability":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "summary",
        "label": "Summary",
        "icon": "¶",
        "description": "Main product description paragraph",
        "criteria": ["faithfulness", "feature_coverage", "persona_relevance", "readability"],
        "rubric": (
            "Score the Summary on these criteria (1-5 each, score out of 5):\n"
            "1. faithfulness: Are all claims grounded in plausible product facts (no hallucinated specs)?\n"
            "2. feature_coverage: Does it cover key product benefits comprehensively?\n"
            "3. persona_relevance: Is the language and focus tuned to the target user?\n"
            "4. readability: Is it well-structured, engaging, and free of filler?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"faithfulness":<score>,"feature_coverage":<score>,"persona_relevance":<score>,"readability":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "visual_cues",
        "label": "Visual Cues",
        "icon": "◈",
        "description": "Design and aesthetic descriptors",
        "criteria": ["specificity", "actionability", "brand_coherence", "originality"],
        "rubric": (
            "Score the Visual Cues on these criteria (1-5 each, score out of 5):\n"
            "1. specificity: Are descriptors concrete (e.g. 'warm amber tones') not vague ('nice colors')?\n"
            "2. actionability: Could a designer directly implement these cues?\n"
            "3. brand_coherence: Do cues align with the product's tone and persona?\n"
            "4. originality: Do they feel distinctive rather than templated?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"specificity":<score>,"actionability":<score>,"brand_coherence":<score>,"originality":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "cta",
        "label": "CTA",
        "icon": "→",
        "description": "Call-to-action button text",
        "criteria": ["action_verb_strength", "urgency_personalization", "funnel_alignment", "clarity"],
        "rubric": (
            "Score the CTA on these criteria (1-5 each, score out of 5):\n"
            "1. action_verb_strength: Does it start with a strong, clear verb?\n"
            "2. urgency_personalization: Does it create motivation or feel personalized?\n"
            "3. funnel_alignment: Does it match the appropriate stage (awareness vs. purchase)?\n"
            "4. clarity: Is the next step unmistakable to the user?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"action_verb_strength":<score>,"urgency_personalization":<score>,"funnel_alignment":<score>,"clarity":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "metatags",
        "label": "Metatags",
        "icon": "</>",
        "description": "SEO meta title and description",
        "criteria": ["length_compliance", "keyword_relevance", "no_keyword_stuffing", "click_worthiness"],
        "rubric": (
            "Score the Metatags on these criteria (1-5 each, score out of 5):\n"
            "1. length_compliance: Title ≤60 chars, Description ≤160 chars?\n"
            "2. keyword_relevance: Are primary keywords naturally included?\n"
            "3. no_keyword_stuffing: Does it read naturally, not robotically?\n"
            "4. click_worthiness: Would this appear compelling in a search result?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"length_compliance":<score>,"keyword_relevance":<score>,"no_keyword_stuffing":<score>,"click_worthiness":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "social_proof",
        "label": "Social Proof",
        "icon": "★",
        "description": "Reviews, ratings, or testimonial copy",
        "criteria": ["specificity", "authenticity", "relevance", "tone_consistency"],
        "rubric": (
            "Score the Social Proof on these criteria (1-5 each, score out of 5):\n"
            "1. specificity: Does it include concrete numbers, ratings, or names (not vague praise)?\n"
            "2. authenticity: Does it feel credible and verifiable — not manufactured?\n"
            "3. relevance: Is it tailored to the target persona's concerns?\n"
            "4. tone_consistency: Does it match the voice of the surrounding copy?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"specificity":<score>,"authenticity":<score>,"relevance":<score>,"tone_consistency":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
    {
        "key": "hyperlink_label",
        "label": "Hyperlink Label",
        "icon": "⇗",
        "description": "Anchor text for embedded links",
        "criteria": ["descriptiveness", "accessibility", "contextual_fit", "conciseness"],
        "rubric": (
            "Score the Hyperlink Label on these criteria (1-5 each, score out of 5):\n"
            "1. descriptiveness: Does the label describe the destination clearly?\n"
            "2. accessibility: Avoids generic labels like 'click here' or 'learn more'?\n"
            "3. contextual_fit: Does it integrate naturally into surrounding copy?\n"
            "4. conciseness: Is it brief without losing meaning?\n\n"
            "Overall = average of the 4 criterion scores.\n\n"
            "Return ONLY a JSON object:\n"
            '{"scores":{"descriptiveness":<score>,"accessibility":<score>,"contextual_fit":<score>,"conciseness":<score>},'
            '"overall":<average of 4 scores>,"strengths":"...","weaknesses":"...","suggestion":"..."}'
        ),
    },
]

SAMPLE_INPUTS = {
    "header": "The Smartwatch Built for Serious Athletes",
    "subheader": "Track performance, recovery, and sleep — all from your wrist.",
    "tagline": "Push further. Recover smarter.",
    "summary": (
        "Designed for endurance athletes, the ProWatch X combines advanced biometric sensors "
        "with AI-powered coaching to help you train smarter. Monitor heart rate variability, "
        "VO2 max estimates, and sleep quality in real time. Built with a titanium case and "
        "sapphire glass, it survives everything your training throws at it."
    ),
    "visual_cues": (
        "Bold matte black chassis with electric blue accents. Clean geometric sans-serif typography. "
        "High-contrast data visualizations on an AMOLED display. Rugged but refined aesthetic."
    ),
    "cta": "Start Your Free 30-Day Trial",
    "metatags": (
        "Title: ProWatch X | Smartwatch for Serious Athletes (47 chars)\n"
        "Description: Train smarter with ProWatch X — biometric tracking, AI coaching, "
        "and titanium durability for endurance athletes. (128 chars)"
    ),
    "social_proof": "Rated 4.8★ by 3,200+ verified athletes across 40 countries. #1 in Triathlete Magazine's 2024 Gear Awards.",
    "hyperlink_label": "Compare all ProWatch models and pricing",
}


# ─────────────────────────────────────────────
# SCORE HELPERS
# ─────────────────────────────────────────────

def score_color(score: float) -> str:
    if score >= 4:
        return "bold green"
    if score >= 3:
        return "bold yellow"
    return "bold red"


def score_bar(score: float, width: int = 20) -> str:
    score = min(max(score, 0), 5)  # clamp to 1-5 scale
    filled = round((score / 5) * width)
    empty = width - filled
    if score >= 4:
        bar_char = "█"
    elif score >= 3:
        bar_char = "▓"
    else:
        bar_char = "░"
    return f"[{score_color(score)}]{bar_char * filled}[/][dim]{'─' * empty}[/]"


def score_label(score: float) -> str:
    if score >= 4:
        return "[bold green]● STRONG[/]"
    if score >= 3:
        return "[bold yellow]● MODERATE[/]"
    return "[bold red]● WEAK[/]"


# ─────────────────────────────────────────────
# EVAL LOGIC
# ─────────────────────────────────────────────

@dataclass
class EvalResult:
    section_key: str
    section_label: str
    scores: dict = field(default_factory=dict)
    overall: float = 0.0
    strengths: str = ""
    weaknesses: str = ""
    suggestion: str = ""
    error: Optional[str] = None


def eval_section(
    client: OpenAI, section: dict, text: str, model: str = "gpt-5-mini"
) -> EvalResult:
    result = EvalResult(section_key=section["key"], section_label=section["label"])
    raw = ""
    try:
        response = client.chat.completions.create(
            model=model,
            max_completion_tokens=1000,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a strict LLM output evaluator for personalized product descriptions. "
                        "Always respond with valid JSON only — no markdown, no explanation, no code fences."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f'Evaluate this "{section["label"]}" section of a personalized product description:\n\n'
                        f'"{text}"\n\n{section["rubric"]}'
                    ),
                },
            ],
        )
        content = response.choices[0].message.content
        if content is None or not content.strip():
            result.error = "API returned empty content"
            return result
        raw = content.strip().replace("```json", "").replace("```", "").strip()
        if not raw:
            result.error = "API returned empty content (after stripping markdown)"
            return result
        # Extract first complete JSON object (handles "Extra data" when LLM returns multiple objects)
        first_brace = raw.find("{")
        if first_brace >= 0:
            depth, end = 0, first_brace
            for i, c in enumerate(raw[first_brace:], first_brace):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            raw = raw[first_brace : end + 1]
        parsed = json.loads(raw)
        result.scores = parsed.get("scores", {})
        result.overall = float(parsed.get("overall", 0))
        result.strengths = parsed.get("strengths", "")
        result.weaknesses = parsed.get("weaknesses", "")
        result.suggestion = parsed.get("suggestion", "")
    except json.JSONDecodeError as e:
        preview = (raw[:200] + "..." if len(raw) > 200 else raw) if raw else "(no content)"
        result.error = f"JSON parse error: {e} | Raw preview: {preview!r}"
    except Exception as e:
        if "openai" in type(e).__module__:
            result.error = f"API error: {e}"
        else:
            result.error = f"Unexpected error: {e}"
    return result


# ─────────────────────────────────────────────
# PROGRAMMATIC API (for workflow integration)
# ─────────────────────────────────────────────

# Key mapping: prompt/LLM labels -> eval section keys
KEY_ALIASES = {
    "Header": "header",
    "Subheader": "subheader",
    "Tagline": "tagline",
    "Summary": "summary",
    "Visual cues": "visual_cues",
    "CTA": "cta",
    "Metatags": "metatags",
    "Social proof": "social_proof",
    "Hyperlink label": "hyperlink_label",
}


def normalize_section_inputs(parsed: dict) -> dict:
    """Map LLM output keys (mixed case/labels) to eval section keys."""
    valid_keys = {s["key"] for s in SECTIONS}
    out = {}
    for k, v in parsed.items():
        if not v:
            continue
        text = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
        key = (
            KEY_ALIASES.get(k)
            or (k.lower().replace(" ", "_") if isinstance(k, str) else str(k))
        )
        if key in valid_keys:
            out[key] = text
    return out


def evaluate_sections(
    inputs: dict,
    api_key: Optional[str] = None,
    model: str = "gpt-5-mini",
    parallel: bool = True,
) -> dict:
    """
    Programmatic evaluation of section inputs. Returns a serializable report dict.

    Args:
        inputs: Dict mapping section keys to text (e.g. {"header": "...", "summary": "..."}).
                Keys can be normalized via normalize_section_inputs() from parsed LLM JSON.
        api_key: OpenAI API key (or set OPENAI_API_KEY env var).
        model: Model for LLM-as-judge.
        parallel: Whether to evaluate sections in parallel.

    Returns:
        Dict with keys: timestamp, sections_evaluated, overall_average, results (list of EvalResult as dicts).
    """
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key required for evaluation")
    client = OpenAI(api_key=api_key)
    section_map = {s["key"]: s for s in SECTIONS}
    filled = {k: v for k, v in inputs.items() if v and str(v).strip()}
    filled = {k: v for k, v in filled.items() if k in section_map}
    if not filled:
        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sections_evaluated": 0,
            "overall_average": 0.0,
            "results": [],
        }
    results: list[EvalResult] = []
    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:

            def eval_one(item):
                key, text = item
                return eval_section(client, section_map[key], str(text), model=model)

            results = list(executor.map(eval_one, filled.items()))
    else:
        for key, text in filled.items():
            results.append(
                eval_section(client, section_map[key], str(text), model=model)
            )
    scored = [r for r in results if not r.error]
    avg = sum(r.overall for r in scored) / len(scored) if scored else 0.0
    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sections_evaluated": len(results),
        "overall_average": round(avg, 2),
        "results": [asdict(r) for r in results],
    }


# ─────────────────────────────────────────────
# INPUT COLLECTION
# ─────────────────────────────────────────────

def collect_inputs(prefill: Optional[dict] = None) -> dict:
    inputs = {}
    console.print()
    console.rule("[bold cyan]📝  ENTER LLM OUTPUT — Section by Section[/]")
    console.print(
        "\n[dim]Paste the LLM-generated text for each section. "
        "Press [bold]Enter twice[/] to confirm each field. "
        "Leave blank to skip.\n[/]"
    )

    for section in SECTIONS:
        pfd = prefill or {}
        pre = pfd.get(section["key"]) or pfd.get(section["key"].upper()) or pfd.get(section["label"])
        if pre is None:
            pre = ""
        pre_str = pre if isinstance(pre, str) else json.dumps(pre, ensure_ascii=False)
        console.print(f"[bold white]{section['icon']}  {section['label']}[/] [dim]— {section['description']}[/]")
        if pre_str:
            preview = pre_str[:80] + ("..." if len(pre_str) > 80 else "")
            console.print(f"  [dim italic]{preview}[/]")
            use_pre = Prompt.ask("  Use pre-loaded value?", choices=["y", "n"], default="y")
            if use_pre == "y":
                inputs[section["key"]] = pre_str
                console.print()
                continue

        lines = []
        console.print("  [dim]Type content (empty line to finish):[/]")
        while True:
            try:
                line = input("  > ")
            except EOFError:
                break
            if line == "":
                break
            lines.append(line)

        value = "\n".join(lines).strip()
        if value:
            inputs[section["key"]] = value
        console.print()

    return inputs


# ─────────────────────────────────────────────
# DISPLAY RESULTS
# ─────────────────────────────────────────────

def print_section_result(result: EvalResult, section: dict):
    if result.error:
        console.print(Panel(
            f"[red]Error evaluating {result.section_label}:[/]\n{result.error}",
            border_style="red", padding=(0, 1)
        ))
        return

    # Header row
    title = Text()
    title.append(f"  {section['icon']}  ", style="bold cyan")
    title.append(result.section_label, style="bold white")
    title.append("   ")
    title.append(score_label(result.overall))
    title.append(f"   [{score_color(result.overall)}]{result.overall}/5[/]   ")
    title.append(score_bar(result.overall))

    # Sub-scores table
    sub_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    sub_table.add_column("Criterion", style="dim", no_wrap=True)
    sub_table.add_column("Bar")
    sub_table.add_column("Score", justify="right")

    for crit, val in result.scores.items():
        sub_table.add_row(
            crit.replace("_", " ").title(),
            score_bar(val, width=14),
            f"[{score_color(val)}]{val}[/]"
        )

    # Feedback panels
    s_panel = Panel(result.strengths or "—", title="[green]✓ Strengths[/]", border_style="green", padding=(0, 1))
    w_panel = Panel(result.weaknesses or "—", title="[red]✗ Weaknesses[/]", border_style="red", padding=(0, 1))
    sug_panel = Panel(result.suggestion or "—", title="[cyan]💡 Suggestion[/]", border_style="cyan", padding=(0, 1))

    body = f"{sub_table}\n"
    console.print(Panel(
        body,
        title=title,
        border_style="bright_black",
        padding=(0, 1),
    ))
    console.print(Columns([s_panel, w_panel], equal=True, expand=True))
    console.print(sug_panel)
    console.print()


def print_summary(results: list[EvalResult]):
    console.rule("[bold cyan]📊  OVERALL EVALUATION SUMMARY[/]")
    console.print()

    scored = [r for r in results if not r.error]
    if not scored:
        console.print("[red]No sections were successfully evaluated.[/]")
        return

    avg = sum(r.overall for r in scored) / len(scored)

    # Summary table
    table = Table(title="Section Scores", box=box.ROUNDED, border_style="bright_black", padding=(0, 1))
    table.add_column("Section", style="bold white", no_wrap=True)
    table.add_column("Score", justify="center")
    table.add_column("Bar", no_wrap=True)
    table.add_column("Rating")

    for result in sorted(results, key=lambda r: r.overall, reverse=True):
        if result.error:
            table.add_row(result.section_label, "[red]ERR[/]", "—", "[red]Error[/]")
        else:
            table.add_row(
                result.section_label,
                f"[{score_color(result.overall)}]{result.overall}/5[/]",
                score_bar(result.overall),
                score_label(result.overall),
            )

    console.print(table)
    console.print()

    avg_text = Text(justify="center")
    avg_text.append("\n  OVERALL SCORE  ", style="bold dim")
    avg_text.append(f"  {avg:.1f} / 5  ", style=f"bold {score_color(avg)} on default")
    avg_text.append(f"  {score_label(avg)}  ")
    avg_text.append(f"\n  {len(scored)} of {len(SECTIONS)} sections evaluated  \n", style="dim")

    console.print(Panel(avg_text, border_style=score_color(avg).replace("bold ", ""), expand=False))
    console.print()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="LLM Eval Framework — Score AI-generated product description sections"
    )
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--input", "-i", help="Path to JSON file with pre-filled section inputs")
    parser.add_argument("--output", "-o", help="Path to save results as JSON")
    parser.add_argument("--sample", "-s", action="store_true", help="Use built-in sample inputs")
    parser.add_argument("--parallel", "-p", action="store_true", help="Evaluate all sections in parallel")
    args = parser.parse_args()

    # Banner
    console.print()
    console.print(Panel(
        Align.center(
            "[bold cyan]LLM OUTPUT EVAL ENGINE[/]\n"
            "[dim]Personalization · Product Descriptions · Section Scorer[/]\n"
            "[dim]Powered by OpenAI (LLM-as-Judge)[/]"
        ),
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()

    # API key
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        console.print("[yellow]No API key found. Set OPENAI_API_KEY or use --api-key[/]")
        api_key = Prompt.ask("  Enter your OpenAI API key", password=True)

    client = OpenAI(api_key=api_key)

    # Load inputs
    prefill = None
    if args.sample:
        prefill = SAMPLE_INPUTS
        console.print("[dim]Using built-in sample inputs.[/]\n")
    elif args.input:
        try:
            with open(args.input, encoding="utf-8") as f:
                prefill = json.load(f)
            console.print(f"[dim]Loaded inputs from {args.input}[/]\n")
        except Exception as e:
            console.print(f"[red]Could not load input file: {e}[/]")
            sys.exit(1)

    inputs = collect_inputs(prefill)
    filled = {k: v for k, v in inputs.items() if v.strip()}

    if not filled:
        console.print("[red]No sections provided. Exiting.[/]")
        sys.exit(0)

    console.print(f"\n[cyan]Evaluating {len(filled)} section(s)...[/]\n")

    results = []
    section_map = {s["key"]: s for s in SECTIONS}

    if args.parallel:
        # Parallel evaluation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Evaluating sections...", total=len(filled))

            def eval_and_advance(key_text):
                key, text = key_text
                result = eval_section(client, section_map[key], text)
                progress.advance(task)
                return result

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = list(executor.map(eval_and_advance, filled.items()))
                results = futures
    else:
        # Sequential evaluation with live display
        for key, text in filled.items():
            section = section_map[key]
            console.print(f"[dim]Evaluating [bold]{section['label']}[/]...[/]")
            result = eval_section(client, section, text)
            results.append(result)

    # Display results
    console.print()
    console.rule("[bold white]SECTION RESULTS[/]")
    console.print()

    for result in results:
        section = section_map[result.section_key]
        print_section_result(result, section)

    print_summary(results)

    # Save output
    if args.output:
        output_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "sections_evaluated": len(results),
            "overall_average": round(
                sum(r.overall for r in results if not r.error) / max(1, len([r for r in results if not r.error])), 2
            ),
            "results": [asdict(r) for r in results],
        }
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            console.print(f"[green]✓ Results saved to {args.output}[/]\n")
        except Exception as e:
            console.print(f"[red]Could not save results: {e}[/]\n")


if __name__ == "__main__":
    main()
