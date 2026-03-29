"""
pipeline.py — Orchestrate the full resume tailoring workflow.

For each job:
  1. Tailor the base resume via LLM (Gemini or Anthropic)
  2. Generate a .docx (and attempt PDF) file
  3. Send via Gmail (skipped in dry-run mode)

Each job is wrapped in its own try/except — one failure never stops the rest.
"""

from pathlib import Path

from docx import Document as DocxDocument

from src.parser import load_jobs
from src.tailor import tailor_resume
from src.doc_generator import generate_document
from src.emailer import send_resume_email


def _read_resume_text(docx_path: str) -> str:
    """Extract plain text from the base resume .docx."""
    doc = DocxDocument(docx_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def run_pipeline(
    xlsx_path: str,
    json_path: str,
    resume_docx_path: str,
    output_dir: str,
    llm_api_key: str,
    llm_provider: str,
    gmail_user: str,
    gmail_app_password: str,
    email_recipient: str,
    dry_run: bool = False,
) -> None:
    """
    Run the full pipeline: parse → tailor → generate → email.

    Args:
        dry_run: If True, skip email sending (validates everything else end-to-end)
    """
    print("=" * 60)
    print("Resume Tailoring Agent — Starting Pipeline")
    print(f"LLM Provider : {llm_provider.upper()}")
    if dry_run:
        print("Mode         : DRY RUN (email sending skipped)")
    print("=" * 60)

    # Load and merge job data
    print("\nLoading job data...")
    jobs = load_jobs(xlsx_path, json_path)
    print(f"Found {len(jobs)} jobs to process.\n")

    # Read base resume once
    print("Reading base resume...")
    base_resume_text = _read_resume_text(resume_docx_path)
    print(f"Base resume loaded ({len(base_resume_text)} chars).\n")

    successes = []
    failures = []

    for job in jobs:
        print(f"[Job {job['id']}/5] {job['title']} at {job['company']}")
        print("-" * 50)

        try:
            # Step 1: Tailor resume via LLM
            print(f"  Tailoring resume with {llm_provider.capitalize()}...")
            tailored_text = tailor_resume(base_resume_text, job, llm_api_key, llm_provider)
            print(f"  Tailoring complete ({len(tailored_text)} chars).")

            # Step 2: Generate document
            print("  Generating document...")
            file_path = generate_document(tailored_text, job, output_dir)

            # Step 3: Send email (or skip in dry-run)
            if dry_run:
                print(f"  [DRY RUN] Would send email to {email_recipient} with {Path(file_path).name}")
            else:
                print("  Sending email...")
                send_resume_email(
                    file_path,
                    job,
                    gmail_user,
                    gmail_app_password,
                    email_recipient,
                )

            successes.append(job["title"])
            print("  Done.\n")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            failures.append({"title": job["title"], "error": error_msg})
            print(f"  FAILED — {error_msg}\n")

    # Final summary
    print("=" * 60)
    print("Pipeline Complete")
    print("=" * 60)
    print(f"Succeeded: {len(successes)}/{len(jobs)}")
    for title in successes:
        print(f"  ✓ {title}")

    if failures:
        print(f"\nFailed: {len(failures)}/{len(jobs)}")
        for f in failures:
            print(f"  ✗ {f['title']} — {f['error']}")
    print()
