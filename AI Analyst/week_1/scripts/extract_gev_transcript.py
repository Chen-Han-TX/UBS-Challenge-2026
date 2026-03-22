import argparse
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import anthropic


@dataclass(frozen=True)
class ExtractedTranscript:
    source_filename: str
    extracted_at_utc: str
    company: str
    extracted: Dict[str, Any]


SYSTEM_PROMPT = """You are an equity research analyst assistant.
Extract structured signals from an earnings call transcript.

Requirements:
- Output MUST be valid JSON (no markdown, no commentary).
- Do not hallucinate numbers; if not present, use null.
- Keep snippets short (<= 200 chars) and cite exact phrases from transcript.
- If the user message includes an AUTHORITATIVE_FILE_PERIOD line, you MUST set metadata.period to that exact string (e.g. "Q1 2024"). Do not invent a different quarter/year.
- For metadata.date, prefer the earnings call date from the transcript header if clearly stated (as YYYY-MM-DD); otherwise null.

Return schema:
{
  "metadata": {
    "company": "GE Vernova",
    "period": "QX YYYY" | null,
    "date": "YYYY-MM-DD" | null
  },
  "mentions": {
    "china": {
      "count_estimate": number | null,
      "snippets": [string, ...]
    },
    "competition": {
      "count_estimate": number | null,
      "snippets": [string, ...]
    },
    "capacity": {
      "count_estimate": number | null,
      "snippets": [string, ...]
    },
    "pricing": {
      "count_estimate": number | null,
      "snippets": [string, ...]
    },
    "backlog": {
      "count_estimate": number | null,
      "snippets": [string, ...]
    }
  },
  "key_takeaways": [string, string, string],
  "risk_flags": [string, ...]
}
"""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_gev_quarter_year_from_filename(filename: str) -> Optional[str]:
    """
    Map filenames like GEV_Q1_2024.txt -> "Q1 2024".
    Returns None if the pattern does not match (caller may rely on model-only inference).
    """
    stem = Path(filename).stem
    m = re.fullmatch(r"GEV_Q([1-4])_(\d{4})", stem, flags=re.IGNORECASE)
    if not m:
        return None
    quarter = int(m.group(1))
    year = int(m.group(2))
    if quarter < 1 or quarter > 4:
        return None
    return f"Q{quarter} {year}"


def _apply_canonical_period(extracted: Dict[str, Any], canonical_period: str) -> None:
    """Force metadata.period to match the filename-derived quarter (post-processing safety net)."""
    meta = extracted.get("metadata")
    if not isinstance(meta, dict):
        extracted["metadata"] = {"company": "GE Vernova", "period": canonical_period, "date": None}
        return
    meta["period"] = canonical_period
    if meta.get("company") is None:
        meta["company"] = "GE Vernova"


def extract_transcript(
    *,
    client: anthropic.Anthropic,
    transcript_text: str,
    model: str,
    canonical_period: Optional[str],
) -> Dict[str, Any]:
    preamble_parts: List[str] = []
    if canonical_period:
        preamble_parts.append(
            f'AUTHORITATIVE_FILE_PERIOD: "{canonical_period}"\n'
            f"You MUST set JSON field metadata.period exactly to: {canonical_period}\n"
            "(This label comes from the input filename; ignore any conflicting quarter text elsewhere.)"
        )
    user_text = "\n\n".join(preamble_parts + ["---TRANSCRIPT START---", transcript_text, "---TRANSCRIPT END---"])

    message = client.messages.create(
        model=model,
        max_tokens=2048,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_text,
                    }
                ],
            }
        ],
    )

    # Anthropics SDK returns content blocks; we expect first block text to be JSON.
    text_blocks = [b for b in message.content if getattr(b, "type", None) == "text"]
    if not text_blocks:
        raise RuntimeError("No text content returned from model.")

    raw = text_blocks[0].text.strip()

    # Some models occasionally wrap JSON in markdown fences. Strip them defensively.
    if raw.startswith("```"):
        # Drop leading ``` or ```json line
        raw_lines = raw.splitlines()
        if raw_lines:
            # Remove first fence line
            raw_lines = raw_lines[1:]
        # Remove trailing fence line if present
        if raw_lines and raw_lines[-1].strip().startswith("```"):
            raw_lines = raw_lines[:-1]
        raw = "\n".join(raw_lines).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Model output was not valid JSON. Re-run with shorter input or ensure transcript is plain text."
        ) from e

    if canonical_period:
        _apply_canonical_period(data, canonical_period)
    return data


def list_available_models(client: anthropic.Anthropic) -> List[str]:
    """
    Returns model IDs available to the current API key.
    """
    # Anthropic SDK returns a paginated object; coerce to a simple list of ids.
    models = client.models.list()
    ids: List[str] = []
    for m in getattr(models, "data", []) or []:
        model_id = getattr(m, "id", None)
        if isinstance(model_id, str) and model_id.strip():
            ids.append(model_id.strip())
    return ids


def pick_default_model(available: Sequence[str]) -> str:
    """
    Prefer a Sonnet-class model for long-context extraction tasks.
    Fallback to the first available model if no obvious match is found.
    """
    lowered = [(m, m.lower()) for m in available]
    for needle in ("sonnet",):
        for original, low in lowered:
            if needle in low:
                return original
    if available:
        return available[0]
    raise RuntimeError("No models available for this API key.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured signals from one GEV earnings call transcript via Anthropic."
    )
    parser.add_argument("--input", required=True, help="Path to transcript .txt file")
    parser.add_argument("--output", required=True, help="Path to write extracted JSON")
    parser.add_argument(
        "--model",
        default="",
        help="Anthropic model name (default: auto-pick a Sonnet model available to your key)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List models available to your API key and exit.",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing ANTHROPIC_API_KEY. Set it in your shell, e.g.:\n"
            "export ANTHROPIC_API_KEY=\"...\""
        )

    with open(args.input, "r", encoding="utf-8") as f:
        transcript_text = f.read().strip()

    if not transcript_text:
        raise SystemExit("Input transcript file is empty.")

    canonical_period = parse_gev_quarter_year_from_filename(os.path.basename(args.input))
    if canonical_period:
        print(f"Using canonical period from filename: {canonical_period}")

    client = anthropic.Anthropic(api_key=api_key)
    available_models = list_available_models(client)

    if args.list_models:
        for m in available_models:
            print(m)
        return 0

    model = args.model.strip() if isinstance(args.model, str) else ""
    if not model:
        model = pick_default_model(available_models)

    extracted = extract_transcript(
        client=client,
        transcript_text=transcript_text,
        model=model,
        canonical_period=canonical_period,
    )

    payload = ExtractedTranscript(
        source_filename=os.path.basename(args.input),
        extracted_at_utc=_utc_now_iso(),
        company="GE Vernova",
        extracted=extracted,
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(asdict(payload), f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

