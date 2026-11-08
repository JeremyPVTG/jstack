// Pure vault logic: no network. Mirrors skills/j-research/scripts/vault_lint.py.

export type Files = Record<string, string>; // path -> text, paths relative to the repo root

const WINDOWS: Record<string, number> = { high: 30, medium: 90, low: 365 };
const TYPES = new Set(["topic", "entity", "comparison", "decision"]);
const WIKI_FIELDS = ["type", "reviewed", "volatility", "sources"];
const RAW_FIELDS = ["url", "captured", "kind"];
const CODE = /```[\s\S]*?```|`[^`\n]*`/g;
const LINK = /\[\[([^[\]|#]+)(?:#[^\]|]*)?(?:\|[^\]]*)?\]\]/g;

/** Text files from a gzip-decompressed tar (GitHub tarball), with the top directory stripped. */
export function untar(bytes: Uint8Array, keep: (path: string) => boolean): Files {
  const files: Files = {};
  const decoder = new TextDecoder();
  const field = (start: number, length: number) => decoder.decode(bytes.subarray(start, start + length)).replace(/\0.*$/s, "");
  let offset = 0;
  let longName: string | null = null;
  while (offset + 512 <= bytes.length) {
    const name = field(offset, 100);
    if (!name) break;
    const size = parseInt(field(offset + 124, 12).trim() || "0", 8);
    const type = String.fromCharCode(bytes[offset + 156] || 48);
    const prefix = field(offset + 345, 155);
    const body = bytes.subarray(offset + 512, offset + 512 + size);
    if (type === "x") {
      const match = decoder.decode(body).match(/\d+ path=([^\n]*)\n/);
      longName = match ? match[1] : null;
    } else if (type === "0" || type === "\0") {
      const full = longName ?? (prefix ? `${prefix}/${name}` : name);
      const path = full.split("/").slice(1).join("/");
      if (path && keep(path)) files[path] = decoder.decode(body);
      longName = null;
    } else if (type !== "g") {
      longName = null;
    }
    offset += 512 + Math.ceil(size / 512) * 512;
  }
  return files;
}

export function frontmatter(text: string): Record<string, string> | null {
  if (!text.startsWith("---\n")) return null;
  const end = text.indexOf("\n---", 4);
  if (end < 0) return null;
  const fields: Record<string, string> = {};
  for (const line of text.slice(4, end).split("\n")) {
    const match = line.match(/^([A-Za-z_]+):\s*(.*?)\s*(?:#.*)?$/);
    if (match) fields[match[1]] = match[2].replace(/^["']|["']$/g, "");
  }
  return fields;
}

/** Wikilink targets listed under a frontmatter key, e.g. supersedes: then "  - \"[[Old page]]\"" lines. */
export function listField(text: string, key: string): string[] {
  if (!text.startsWith("---\n")) return [];
  const end = text.indexOf("\n---", 4);
  const lines = text.slice(4, end < 0 ? 4 : end).split("\n");
  const start = lines.findIndex((line) => line.startsWith(`${key}:`));
  if (start < 0) return [];
  const out: string[] = [];
  for (const line of lines.slice(start + 1)) {
    if (!/^\s+-/.test(line)) break;
    const match = line.match(/\[\[([^\[\]|#]+)/);
    if (match) out.push(match[1].trim());
  }
  return out;
}

const isDate = (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value));
const days = (from: string, to: Date) => Math.floor((to.getTime() - Date.parse(from)) / 86_400_000);

/** Problems with a wiki page's frontmatter, empty when valid. */
export function wikiProblems(text: string): string[] {
  const fields = frontmatter(text);
  const missing = WIKI_FIELDS.filter((key) => !fields || !(key in fields));
  if (missing.length) return [`missing frontmatter ${missing.join(", ")}`];
  const problems: string[] = [];
  if (!TYPES.has(fields!.type)) problems.push(`type must be one of ${[...TYPES].sort().join(", ")}`);
  if (!isDate(fields!.reviewed)) problems.push("reviewed must be YYYY-MM-DD");
  if (!(fields!.volatility in WINDOWS)) problems.push("volatility must be high, medium, or low");
  return problems;
}

export function lint(files: Files, today: Date): { errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];
  const notes = Object.keys(files).filter((path) => path.endsWith(".md") && !path.split("/").some((part) => part.startsWith(".")));
  const byPath = new Map<string, string>();
  const byName = new Map<string, string>();
  for (const path of notes) {
    const rel = path.slice(0, -3);
    byPath.set(rel.toLowerCase(), rel);
    const stem = rel.split("/").pop()!.toLowerCase();
    if (!byName.has(stem)) byName.set(stem, rel);
  }
  const resolve = (target: string) => {
    const key = target.trim().replace(/\.md$/, "").toLowerCase();
    return byPath.get(key) ?? (key.includes("/") ? undefined : byName.get(key));
  };
  const inbound = new Map<string, Set<string>>();
  const outbound = new Map<string, Set<string>>();
  for (const path of notes) {
    const rel = path.slice(0, -3);
    const text = files[path];
    for (const [, target] of text.replace(CODE, "").matchAll(LINK)) {
      const found = resolve(target);
      if (!found) errors.push(`${rel}: broken link [[${target}]]`);
      else if (found !== rel) {
        inbound.set(found, (inbound.get(found) ?? new Set()).add(rel));
        outbound.set(rel, (outbound.get(rel) ?? new Set()).add(found));
      }
    }
    if (rel.startsWith("wiki/")) {
      const problems = wikiProblems(text);
      for (const problem of problems) errors.push(`${rel}: ${problem}`);
      const fields = frontmatter(text);
      if (!problems.length && fields && days(fields.reviewed, today) > WINDOWS[fields.volatility]) {
        warnings.push(`${rel}: stale, reviewed ${fields.reviewed} (${fields.volatility} volatility)`);
      }
    } else if (rel.startsWith("raw/")) {
      const fields = frontmatter(text);
      const missing = RAW_FIELDS.filter((key) => !fields?.[key]);
      if (missing.length) errors.push(`${rel}: missing frontmatter ${missing.join(", ")}`);
    }
  }
  for (const path of notes.filter((p) => p.startsWith("wiki/"))) {
    const rel = path.slice(0, -3);
    for (const [key, severe] of [["supersedes", true], ["contradicts", false]] as const) {
      for (const target of listField(files[path], key)) {
        const other = resolve(target);
        if (!other || other === rel) continue;
        if (!outbound.get(other)?.has(rel)) (severe ? errors : warnings).push(`${other}: ${key === "supersedes" ? `superseded by [[${rel.split("/").pop()}]]; link to it` : `contradicted by [[${rel.split("/").pop()}]]; link to it under Contradictions`}`);
      }
    }
  }
  for (const rel of [...byPath.values()].filter((r) => r.startsWith("wiki/")).sort()) {
    const from = inbound.get(rel) ?? new Set();
    if (!from.has("index")) errors.push(`${rel}: not listed in index.md`);
    if (![...from].some((source) => source !== "index")) warnings.push(`${rel}: orphan, no other page links to it`);
  }
  return { errors, warnings };
}

const tokens = (text: string) => text.toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];

export type Hit = { path: string; title: string; type: string; reviewed: string; stale?: true; superseded_by?: string[]; match?: "keyword" | "semantic" | "both"; snippet: string; score: number };
type Info = Pick<Hit, "title" | "type" | "reviewed" | "stale" | "superseded_by">;

/** Wiki page title -> titles of the pages that supersede it, lower-cased keys. */
function successorsOf(files: Files): Map<string, string[]> {
  const successors = new Map<string, string[]>();
  for (const [path, text] of Object.entries(files)) {
    if (!path.startsWith("wiki/")) continue;
    for (const target of listField(text, "supersedes")) {
      const key = target.toLowerCase();
      successors.set(key, [...(successors.get(key) ?? []), path.slice(5, -3)]);
    }
  }
  return successors;
}

function info(path: string, text: string, successors: Map<string, string[]>, today: Date): Info {
  const title = text.match(/^# (.+)$/m)?.[1] ?? path.split("/").pop()!.replace(/\.md$/, "");
  const fields = frontmatter(text) ?? {};
  const wiki = path.startsWith("wiki/");
  const superseded = wiki ? successors.get(path.slice(5, -3).toLowerCase()) : undefined;
  const stale = wiki && isDate(fields.reviewed ?? "") && fields.volatility in WINDOWS && days(fields.reviewed, today) > WINDOWS[fields.volatility];
  return { title, type: fields.type ?? (path.startsWith("raw/") ? "source" : ""), reviewed: fields.reviewed ?? fields.captured ?? "", ...(stale ? { stale: true as const } : {}), ...(superseded ? { superseded_by: superseded } : {}) };
}

/** Pages that search covers: Markdown under wiki/ and raw/. */
export const searchable = (path: string) => path.endsWith(".md") && (path.startsWith("wiki/") || path.startsWith("raw/"));

/** BM25 over the vault's Markdown, title words weighted, wiki pages ranked above raw captures, superseded pages demoted. Hits flag stale and superseded pages. */
export function search(files: Files, query: string, limit = 8, today = new Date()): Hit[] {
  const terms = [...new Set(tokens(query))];
  if (!terms.length) return [];
  const docs = Object.entries(files)
    .filter(([path]) => searchable(path))
    .map(([path, text]) => {
      const title = text.match(/^# (.+)$/m)?.[1] ?? path.split("/").pop()!.replace(/\.md$/, "");
      const words = [...tokens(title), ...tokens(title), ...tokens(title), ...tokens(text)];
      const counts = new Map<string, number>();
      for (const word of words) counts.set(word, (counts.get(word) ?? 0) + 1);
      return { path, text, counts, length: words.length };
    });
  const average = docs.reduce((sum, doc) => sum + doc.length, 0) / Math.max(docs.length, 1);
  const df = new Map(terms.map((term) => [term, docs.filter((doc) => doc.counts.has(term)).length]));
  const successors = successorsOf(files);
  const k1 = 1.2;
  const b = 0.75;
  return docs
    .map((doc) => {
      let score = 0;
      for (const term of terms) {
        const tf = doc.counts.get(term) ?? 0;
        if (!tf) continue;
        const idf = Math.log(1 + (docs.length - df.get(term)! + 0.5) / (df.get(term)! + 0.5));
        score += (idf * tf * (k1 + 1)) / (tf + k1 * (1 - b + (b * doc.length) / average));
      }
      const meta = info(doc.path, doc.text, successors, today);
      if (doc.path.startsWith("wiki/")) score *= 1.5;
      if (meta.superseded_by) score *= 0.5;
      const body = doc.text.replace(/^---\n[\s\S]*?\n---\n/, "");
      const at = terms.map((term) => body.toLowerCase().indexOf(term)).filter((i) => i >= 0).sort((x, y) => x - y)[0] ?? 0;
      const snippet = body.slice(Math.max(0, at - 80), at + 220).replace(/\s+/g, " ").trim();
      return { path: doc.path, ...meta, snippet, score: Math.round(score * 100) / 100 };
    })
    .filter((hit) => hit.score > 0)
    .sort((x, y) => y.score - x.score)
    .slice(0, limit);
}

/** A semantic match from the vector index: a vault path and the matching chunk. */
export type Semantic = { path: string; text: string };

/**
 * Merge keyword hits with semantic matches by reciprocal rank fusion (k = 60), keeping
 * the keyword ranking's preferences: wiki pages x1.5, superseded pages x0.5. Semantic
 * matches for paths no longer in the vault are dropped. Scores are fused ranks, not BM25.
 */
export function fuse(files: Files, keyword: Hit[], semantic: Semantic[], limit = 8, today = new Date()): Hit[] {
  const successors = successorsOf(files);
  const merged = new Map<string, Hit & { fused: number }>();
  keyword.forEach((hit, rank) => merged.set(hit.path, { ...hit, match: "keyword", fused: 1 / (61 + rank) }));
  const seen = new Set<string>();
  let rank = 0;
  for (const match of semantic) {
    if (seen.has(match.path) || files[match.path] === undefined || !searchable(match.path)) continue;
    seen.add(match.path);
    const add = 1 / (61 + rank++);
    const existing = merged.get(match.path);
    if (existing) {
      existing.fused += add;
      existing.match = "both";
    } else {
      const snippet = match.text.replace(/^---\n[\s\S]*?\n---\n/, "").replace(/\s+/g, " ").trim().slice(0, 300);
      merged.set(match.path, { path: match.path, ...info(match.path, files[match.path], successors, today), match: "semantic", snippet, score: 0, fused: add });
    }
  }
  return [...merged.values()]
    .map(({ fused, ...hit }) => {
      let score = fused;
      if (hit.path.startsWith("wiki/")) score *= 1.5;
      if (hit.superseded_by) score *= 0.5;
      return { ...hit, score: Math.round(score * 10_000) / 10_000 };
    })
    .sort((x, y) => y.score - x.score)
    .slice(0, limit);
}

/** Where agents may write with write_page: wiki pages and the index. Raw captures and the log have their own tools. */
export function writablePath(path: string): boolean {
  return path === "index.md" || /^wiki\/[^/\\]+\.md$/.test(path);
}

export function slug(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60);
}

export type Capture = { slug: string; url: string; title: string; author?: string; published?: string; kind: string; version?: string; body: string };
const KINDS = new Set(["docs", "code", "paper", "forum", "video", "social", "article", "dataset"]);

export function capturePath(capture: Capture, today: string): string {
  return `raw/${today.slice(0, 7)}/${today} ${slug(capture.slug)}.md`;
}

export function captureText(capture: Capture, today: string): string {
  if (!KINDS.has(capture.kind)) throw new Error(`kind must be one of ${[...KINDS].join(", ")}`);
  if (!slug(capture.slug)) throw new Error("slug needs letters or digits");
  const clean = (value?: string) => (value ?? "").replace(/[\r\n]+/g, " ").trim();
  return [
    "---",
    `url: ${clean(capture.url)}`,
    `title: "${clean(capture.title).replace(/"/g, "'")}"`,
    `author: ${clean(capture.author)}`,
    `published: ${clean(capture.published) || "unknown"}`,
    `captured: ${today}`,
    `kind: ${capture.kind}`,
    `version: ${clean(capture.version)}`,
    "---",
    "",
    capture.body.trim(),
    "",
  ].join("\n");
}

export function logLine(kind: string, summary: string, pages: string[], today: string, spend?: string): string {
  if (!["research", "ingest", "lint"].includes(kind)) throw new Error("kind must be research, ingest, or lint");
  const text = summary.replace(/[\r\n]+/g, " ").trim();
  const links = pages.map((page) => `[[${page.replace(/[[\]]/g, "")}]]`).join(", ");
  const cost = (spend ?? "").replace(/[^\w$.~ -]/g, "").trim().slice(0, 24);
  return `## [${today}] ${kind} | ${text}${links ? ` | pages: ${links}` : ""}${cost ? ` | spend: ${cost}` : ""}`;
}

export type Skill = { name: string; description: string; files: string[] };

export function skills(files: Files): Skill[] {
  return Object.keys(files)
    .filter((path) => /^skills\/[^/]+\/SKILL\.md$/.test(path))
    .sort()
    .map((path) => {
      const dir = path.slice(0, -"SKILL.md".length);
      const fields = frontmatter(files[path]) ?? {};
      return { name: fields.name ?? dir.split("/")[1], description: fields.description ?? "", files: Object.keys(files).filter((p) => p.startsWith(dir)).map((p) => p.slice(dir.length)).sort() };
    });
}
