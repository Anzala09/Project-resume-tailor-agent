"""
main.py — Entry point for the AI Resume Tailoring Agent.

Loads credentials from .env and kicks off the pipeline.

Usage:
    python main.py              # Full run: tailor + generate + email
    python main.py --dry-run    # Validate pipeline without sending emails

LLM Provider (auto-detected from .env):
    GEMINI_API_KEY set      → Uses Google Gemini 1.5 Flash (FREE)
    ANTHROPIC_API_KEY set   → Uses Anthropic Claude Sonnet (paid)
"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from src.pipeline import run_pipeline

load_dotenv()

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"


def _detect_llm_provider() -> tuple[str, str]:
    """
    Auto-detect which LLM provider to use based on available API keys.

    Returns:
        (provider_name, api_key) — e.g. ("gemini", "AIza...")

    Raises:
        SystemExit if no valid key is found.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if gemini_key:
        return "gemini", gemini_key
    if anthropic_key:
        return "anthropic", anthropic_key

    print("Error: No LLM API key found.")
    print()
    print("Set one of the following in your .env file:")
    print("  GEMINI_API_KEY     — FREE. Get it at https://aistudio.google.com/app/apikey")
    print("  ANTHROPIC_API_KEY  — Paid. Get it at https://console.anthropic.com/")
    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Resume Tailoring Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full pipeline (parse, tailor, generate docs) but skip sending emails.",
    )
    args = parser.parse_args()

    # Auto-detect LLM provider
    llm_provider, llm_api_key = _detect_llm_provider()

    # Validate email credentials (required unless dry-run)
    email_vars = ["GMAIL_USER", "GMAIL_APP_PASSWORD", "EMAIL_RECIPIENT"]
    missing_email = [k for k in email_vars if not os.getenv(k)]

    if missing_email and not args.dry_run:
        print(f"Error: Missing email credentials: {', '.join(missing_email)}")
        print("Set these in your .env file, or use --dry-run to skip email sending.")
        raise SystemExit(1)

    run_pipeline(
        xlsx_path=str(INPUT_DIR / "option2_job_links.xlsx"),
        json_path=str(INPUT_DIR / "option2_jobs.json"),
        resume_docx_path=str(INPUT_DIR / "candidate_resume.docx"),
        output_dir=str(OUTPUT_DIR),
        llm_api_key=llm_api_key,
        llm_provider=llm_provider,
        gmail_user=os.getenv("GMAIL_USER", ""),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", ""),
        email_recipient=os.getenv("EMAIL_RECIPIENT", ""),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
