# AI Resume Tailoring Agent

An autonomous Python agent that reads 5 job postings, tailors a candidate's resume for each role using Claude (Anthropic), saves the output as Word documents, and emails each one individually via Gmail.

**Demo Video:** [link goes here]

---

## Option Choice

**Option 2 — AI Resume Tailoring Agent**

I chose Option 2 because it involves the most interesting engineering challenge: designing an LLM prompt that produces *substantively different* outputs per role, not just minor rewording. The pipeline also exercises clean modular design — parsing, AI generation, document creation, and email delivery are each isolated concerns that compose cleanly.

---

## Project Structure

```
resume-tailor-agent/
├── input/
│   ├── option2_job_links.xlsx   # Job metadata (title, company, URL)
│   ├── option2_jobs.json        # Detailed job descriptions (joined on id/#)
│   └── candidate_resume.docx   # Base resume for Alex J. Morgan
├── output/                      # Generated tailored resumes (gitignored)
├── src/
│   ├── parser.py                # Merge xlsx + json on id/#
│   ├── tailor.py                # Claude prompt + API call
│   ├── doc_generator.py         # Build styled .docx, attempt PDF
│   ├── emailer.py               # Gmail SMTP with attachment
│   └── pipeline.py              # Orchestrator with per-job error isolation
├── main.py                      # Entry point
├── .env.example                 # Credential template
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd Project-resume-tailor-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv or
# python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure credentials

```bash
cp .env.example .env
```
**Then open and edit it:**                                                                                      
                                                            
open -e .env
  
Edit `.env` and fill in:

| Variable | Where to get it |
|----------|----------------|
| `GROQ_API_KEY` | (https://console.groq.com/keys) |
| `GMAIL_USER` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) (requires 2FA) |
| `EMAIL_RECIPIENT` | Where to send the resumes (can be yourself for testing) |

> **Note on Gmail App Password:** Go to Google Account → Security → 2-Step Verification → App passwords. Create one named "Resume Agent". Copy the 16-character password into `.env`.

### 5. Run the agent

```bash
python main.py
```

The agent will:
1. Parse and join `option2_job_links.xlsx` + `option2_jobs.json`
2. Tailor the resume for each of the 5 roles via Claude
3. Save each tailored resume to `output/`
4. Email each resume to `EMAIL_RECIPIENT`

---

## Approach & Key Design Decisions

### Modular Architecture
Each concern lives in its own module (`parser`, `tailor`, `doc_generator`, `emailer`) with `pipeline.py` orchestrating them. This makes each piece independently testable and easy to swap (e.g., replace Gmail with SendGrid by only touching `emailer.py`).

### Prompt Engineering for Differentiation
The core challenge of Option 2 is producing *meaningfully different* resumes — not just swapping keywords. The Claude system prompt enforces:
- **Reorder sections** based on role type (ML work first for ML roles, infra projects first for DevOps)
- **Mirror exact language** from the job description
- **Rewrite the professional summary** from scratch per role
- **De-emphasize irrelevant skills** rather than listing everything

This produces resumes where a Backend role leads with API/microservices work and omits ML frameworks from the skills header, while the ML role leads with research and model training projects.

### Per-Job Error Isolation
Each job is processed in its own `try/except`. A Claude API timeout, a file write error, or a failed email send for job #3 does not stop jobs #4 and #5 from completing. The pipeline prints a summary of successes and failures at the end.

### PDF Generation (Optional)
The agent attempts PDF conversion via `docx2pdf` after generating each `.docx`. This requires Microsoft Word on macOS or LibreOffice on Linux. If unavailable, the pipeline falls back gracefully to `.docx`-only output with a warning — it never raises an error over this.

### Environment Variables from Day One
All credentials are loaded via `python-dotenv` at startup. The agent validates all required variables before starting and exits with a clear error message if any are missing.

---

## Assumptions

1. **`option2_jobs.json` format:** The assignment references this file but it was not provided. I created it with realistic, role-differentiated job descriptions for all 5 Nexus Systems roles, following the JSON schema shown in the assignment.
2. **Recipient email:** All 5 emails go to `EMAIL_RECIPIENT`. In a real scenario this would be the hiring manager's address per job.
3. **Candidate name stays the same:** The tailoring modifies emphasis, ordering, and language — but does not change the candidate's name, employer history, or factual details.
4. **Single Claude model:** `claude-3-5-sonnet-20241022` is used for all 5 calls. A production system might use a cheaper model for drafts and a premium one for final output.

---

## What I Would Improve Given More Time

- **Async pipeline:** Run all 5 Claude API calls concurrently with `asyncio` + `anthropic.AsyncAnthropic` to cut total runtime from ~60s to ~15s.
- **Structured Claude output:** Use Claude's tool-use / JSON mode to get structured section data back, then apply consistent formatting rather than parsing plain text heuristically.
- **Diff viewer:** Auto-generate a side-by-side diff between the base resume and each tailored version for quality review before sending.
- **Retry with exponential backoff:** Wrap Claude and SMTP calls in a retry decorator for transient network failures.
- **Email templating:** Use an HTML email template (via `jinja2`) for a more professional email body with formatted job details.

---

## Demo Video

[Add YouTube/Loom/Google Drive link here]
