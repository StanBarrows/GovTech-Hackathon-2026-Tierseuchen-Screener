"""
Extract structured labels (Disease, DiseaseSubtype, InEurope, consequence)
from each line of disease_reports.jsonl and write disease_reports_embeddings.jsonl.

One input line -> one output line. Original record is preserved, extracted
fields are merged in. Errors land in a `_error` field instead of crashing the run.
"""

import json
from pathlib import Path

from openai import OpenAI
import requests
import httpx


# --------------------------------------------------------------------------
# Client setup
# --------------------------------------------------------------------------

with open("TS-Scanner.json") as f:
    env = json.load(f)

with open("llm.codebar.net.json") as f:
    codebar = json.load(f)

access = {v["name"]: v["value"] for v in env["variables"] if v.get("enabled", True)}


class ScrubTransport(httpx.HTTPTransport):
    def handle_request(self, request):
        request.headers["user-agent"] = "Mozilla/5.0"
        for name in [h for h in request.headers if h.lower().startswith("x-stainless")]:
            del request.headers[name]
        return super().handle_request(request)


client = OpenAI(
    base_url=access["url"],
    api_key=access["token"],
    http_client=httpx.Client(transport=ScrubTransport()),
)

models = client.models.list()
print([m.id for m in models.data])


def chat(prompt, model="qwen.3.5:9b", system=None, stream=False, **kwargs):
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if stream:
        text = ""
        for chunk in client.chat.completions.create(
            model=model, messages=messages, stream=True, **kwargs
        ):
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            text += delta
        print()
        return text

    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content


# --------------------------------------------------------------------------
# Extraction pipeline
# --------------------------------------------------------------------------

SYSTEM = Path("SystemPrompt.md").read_text(encoding="utf-8")

EMPTY_LABELS = {
    "Disease": None,
    "DiseaseSubtype": None,
    "InEurope": None,
    "consequence": {"politisch": None, "sozial": None, "wirtschaftlich": None},
}


def parse(text: str) -> dict:
    """Run the extraction prompt on one text and return parsed JSON."""
    prompt = f'# Text to parse\n"""\n{text.strip()}\n"""'
    raw = chat(
        prompt,
        system=SYSTEM,
        temperature=0,
        # response_format={"type": "json_object"},  # uncomment if your server supports it
    ).strip()
    # defensive: strip code fences if the model adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    return json.loads(raw.strip())


def extract_file(
    in_path: str = "disease_reports.jsonl",
    out_path: str = "disease_reports_embeddings.jsonl",
    resume: bool = False,
    progress_every: int = 10,
) -> None:
    in_path, out_path = Path(in_path), Path(out_path)

    # Resume by counting existing output lines (1-to-1 with input lines)
    already = 0
    if resume and out_path.exists():
        with out_path.open(encoding="utf-8") as f:
            already = sum(1 for _ in f)
        if already:
            print(f"resuming after {already} already-processed lines")

    mode = "a" if already else "w"
    with in_path.open(encoding="utf-8") as fin, \
         out_path.open(mode, encoding="utf-8") as fout:

        for i, line in enumerate(fin):
            if i < already:
                continue

            # 1) parse input JSONL
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                out = {"_raw": line.rstrip(), **EMPTY_LABELS,
                       "_error": f"jsonl parse: {e}"}
                fout.write(json.dumps(out, ensure_ascii=False) + "\n")
                fout.flush()
                continue

            # 2) extract labels
            text = record.get("fulltext")
            if not text:
                labels = {**EMPTY_LABELS, "_error": "missing fulltext"}
            else:
                try:
                    labels = parse(text)
                except Exception as e:
                    labels = {**EMPTY_LABELS,
                              "_error": f"extraction: {type(e).__name__}: {e}"}

            # 3) write merged record (original fields kept + labels added)
            fout.write(json.dumps({**record, **labels}, ensure_ascii=False) + "\n")
            fout.flush()

            if progress_every and (i + 1) % progress_every == 0:
                print(f"processed {i + 1}")

    print("done")


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Extract Disease / DiseaseSubtype / InEurope / consequence "
                    "from a JSONL of disease reports."
    )
    p.add_argument("-i", "--input", default="disease_reports.jsonl",
                   help="Path to the input JSONL (each line must have a "
                        "'fulltext' field). Default: %(default)s")
    p.add_argument("-o", "--output", default="disease_reports_embeddings.jsonl",
                   help="Path to the output JSONL. Parent directories are "
                        "created if missing. Default: %(default)s")
    p.add_argument("--no-resume", action="store_true",
                   help="Overwrite the output file instead of resuming from "
                        "where a previous run left off.")
    p.add_argument("--progress-every", type=int, default=10,
                   help="Print progress every N lines (0 disables). "
                        "Default: %(default)s")
    args = p.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    extract_file(
        in_path=args.input,
        out_path=str(out_path),
        resume=not args.no_resume,
        progress_every=args.progress_every,
    )