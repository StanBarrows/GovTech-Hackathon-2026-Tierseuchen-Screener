"""
Extract structured labels from disease / PAFF reports using a configurable
SystemPrompt schema. Two input modes, auto-detected from the -i path:

  * file mode      : -i points to a .jsonl file (one record per line, must
                     have a 'fulltext' field). Output is a single .jsonl file.
  * directory mode : -i points to a directory of .json files (one record per
                     file). Output is a directory with one .json file per
                     input, same filenames. The entire JSON content is used
                     as 'fulltext' for the LLM (see record_to_text()).

Errors land in a '_error' field instead of crashing the run.
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


def parse(text: str, system: str) -> dict:
    """Run the extraction prompt on one text and return parsed JSON."""
    prompt = f'# Text to parse\n"""\n{text.strip()}\n"""'
    raw = chat(
        prompt,
        system=system,
        temperature=0,
        # response_format={"type": "json_object"},  # uncomment if your server supports it
    ).strip()
    # defensive: strip code fences if the model adds them anyway
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    return json.loads(raw.strip())


def record_to_text(record) -> str:
    """Turn one loaded JSON record into the 'fulltext' passed to the LLM.

    Default: serialize the whole record as indented JSON text — this works
    when there is no single text field and you want the LLM to see everything.

    If your PAFF JSONs DO have a known text field, replace the body with e.g.
        return record.get("text") or record.get("content") or json.dumps(record, ensure_ascii=False)

    If you want all string leaves concatenated, see _flatten_strings() below.
    """
    if isinstance(record, str):
        return record
    return json.dumps(record, ensure_ascii=False, indent=2)


def _flatten_strings(obj) -> list:
    """Recursively collect all string leaves from a nested JSON structure.
    Useful if you want to swap record_to_text() to text-only mode."""
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(_flatten_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_flatten_strings(v))
    return out


# --------------------------------------------------------------------------
# Mode 1: JSONL file -> JSONL file (one record per line)
# --------------------------------------------------------------------------


def extract_file(
    system: str,
    empty_labels: dict,
    in_path: Path,
    out_path: Path,
    resume: bool = False,
    progress_every: int = 10,
) -> None:
    in_path, out_path = Path(in_path), Path(out_path)

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

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                out = {"_raw": line.rstrip(), **empty_labels,
                       "_error": f"jsonl parse: {e}"}
                fout.write(json.dumps(out, ensure_ascii=False) + "\n")
                fout.flush()
                continue

            text = record.get("fulltext")
            if not text:
                labels = {**empty_labels, "_error": "missing fulltext"}
            else:
                try:
                    labels = parse(text, system)
                except Exception as e:
                    labels = {**empty_labels,
                              "_error": f"extraction: {type(e).__name__}: {e}"}

            fout.write(json.dumps({**record, **labels}, ensure_ascii=False) + "\n")
            fout.flush()

            if progress_every and (i + 1) % progress_every == 0:
                print(f"processed {i + 1}")

    print("done")


# --------------------------------------------------------------------------
# Mode 2: directory of JSON files -> directory of JSON files
# --------------------------------------------------------------------------


def extract_dir(
    system: str,
    empty_labels: dict,
    in_dir: Path,
    out_dir: Path,
    resume: bool = False,
    progress_every: int = 10,
) -> None:
    in_dir, out_dir = Path(in_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.glob("*.json"))
    total = len(files)
    print(f"found {total} json files in {in_dir}")

    skipped = 0
    for i, in_file in enumerate(files):
        out_file = out_dir / in_file.name

        # resume: if the output already exists, skip
        if resume and out_file.exists():
            skipped += 1
            continue

        # 1) load input JSON
        try:
            record = json.loads(in_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            merged = {"_source": in_file.name, **empty_labels,
                      "_error": f"json parse: {e}"}
            out_file.write_text(
                json.dumps(merged, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            continue

        # 2) turn it into the text the LLM sees
        text = record_to_text(record)
        if not text or not text.strip():
            labels = {**empty_labels, "_error": "empty record"}
        else:
            try:
                labels = parse(text, system)
            except Exception as e:
                labels = {**empty_labels,
                          "_error": f"extraction: {type(e).__name__}: {e}"}

        # 3) write merged record (original JSON preserved + labels merged in)
        merged = record if isinstance(record, dict) else {"_record": record}
        merged = {**merged, **labels, "_source": in_file.name}
        out_file.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if progress_every and (i + 1) % progress_every == 0:
            print(f"processed {i + 1}/{total}")

    if skipped:
        print(f"skipped {skipped} already-processed files")
    print("done")


# --------------------------------------------------------------------------
# Fallback shapes for known schemas
# --------------------------------------------------------------------------
# These are written when extraction fails or the input is empty. Keys MUST
# match the field names in the corresponding SystemPrompt. Add a new entry
# here whenever you introduce another schema.

EMPTY_LABELS_BY_SCHEMA = {
    "paff": {
        "Relevanz":   {"label": None, "evidence": None, "rationale": None},
        "Severity":   {"label": None, "evidence": None, "rationale": None},
        "Reichweite": {"label": None, "evidence": None, "rationale": None},
        "Prävention": {
            "bekämpfung":  {"measures": [], "evidence": None},
            "surveilance": {"measures": [], "evidence": None},
        },
    },
    "disease": {
        "Disease": None,
        "DiseaseSubtype": None,
        "InEurope": None,
        "consequence": {"politisch": None, "sozial": None, "wirtschaftlich": None},
    },
}


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Extract structured labels from disease / PAFF reports "
                    "using a configurable SystemPrompt schema. Auto-detects "
                    "whether -i is a JSONL file or a directory of JSON files."
    )
    p.add_argument("-s", "--schema", default="SystemPrompt.md",
                   help="Path to the SystemPrompt markdown file. "
                        "Default: %(default)s")
    p.add_argument("-e", "--empty-labels", default="paff",
                   help="Fallback shape on extraction failure. Either a key "
                        "from EMPTY_LABELS_BY_SCHEMA ('paff', 'disease') or a "
                        "path to a JSON file. Default: %(default)s")
    p.add_argument("-i", "--input", required=True,
                   help="Either a .jsonl file (each line must have 'fulltext') "
                        "OR a directory of .json files (whole content used as "
                        "fulltext).")
    p.add_argument("-o", "--output", required=True,
                   help="Either a .jsonl file (for JSONL input) or a directory "
                        "(for directory input). Parent dirs are created.")
    p.add_argument("--no-resume", action="store_true",
                   help="Overwrite existing output instead of resuming.")
    p.add_argument("--progress-every", type=int, default=10,
                   help="Print progress every N records (0 disables). "
                        "Default: %(default)s")
    args = p.parse_args()

    SYSTEM = Path(args.schema).read_text(encoding="utf-8")

    # Resolve EMPTY_LABELS: built-in key or JSON file path
    if args.empty_labels in EMPTY_LABELS_BY_SCHEMA:
        EMPTY_LABELS = EMPTY_LABELS_BY_SCHEMA[args.empty_labels]
    else:
        EMPTY_LABELS = json.loads(
            Path(args.empty_labels).read_text(encoding="utf-8")
        )

    in_path = Path(args.input)
    out_path = Path(args.output)

    if in_path.is_dir():
        # directory mode
        out_path.mkdir(parents=True, exist_ok=True)
        extract_dir(
            system=SYSTEM,
            empty_labels=EMPTY_LABELS,
            in_dir=in_path,
            out_dir=out_path,
            resume=not args.no_resume,
            progress_every=args.progress_every,
        )
    else:
        # file mode (jsonl)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        extract_file(
            system=SYSTEM,
            empty_labels=EMPTY_LABELS,
            in_path=in_path,
            out_path=out_path,
            resume=not args.no_resume,
            progress_every=args.progress_every,
        )