import { describe, expect, it } from "vitest";
import { localDate } from "../src/tools";
import { captureText, capturePath, lint, listField, logLine, readablePath, search, skills, untar, wikiProblems, writablePath, type Files } from "../src/vault";

const page = (title: string, body = "", type = "topic", reviewed = "2026-11-01", volatility = "medium") =>
  `---\ntype: ${type}\nreviewed: ${reviewed}\nvolatility: ${volatility}\nsources:\n  - "[[raw/2026-11/2026-11-01 source]]"\n---\n\n# ${title}\n\n${body}\n`;
const raw = "---\nurl: https://example.com\ncaptured: 2026-11-01\nkind: docs\n---\nExtract.\n";
const base = (): Files => ({ "AGENTS.md": "Rules with `[[example]]` links in code.\n```\n[[Also not]]\n```\n", "log.md": "# Log\n", "raw/2026-11/2026-11-01 source.md": raw });
const today = new Date("2026-11-07");

function tar(entries: Record<string, string>): Uint8Array {
  const blocks: Uint8Array[] = [];
  const enc = new TextEncoder();
  for (const [name, text] of Object.entries(entries)) {
    const header = new Uint8Array(512);
    const body = enc.encode(text);
    const put = (offset: number, value: string) => header.set(enc.encode(value), offset);
    if (name.length > 100) {
      const record = ` path=${name}\n`;
      const pax = enc.encode(`${record.length + String(record.length + 2).length}${record}`);
      const paxHeader = new Uint8Array(512);
      paxHeader.set(enc.encode("pax"), 0);
      paxHeader.set(enc.encode(pax.length.toString(8).padStart(11, "0")), 124);
      paxHeader[156] = "x".charCodeAt(0);
      blocks.push(paxHeader, pad(pax));
      put(0, name.slice(-90));
    } else put(0, name);
    put(124, body.length.toString(8).padStart(11, "0"));
    header[156] = "0".charCodeAt(0);
    blocks.push(header, pad(body));
  }
  blocks.push(new Uint8Array(1024));
  const out = new Uint8Array(blocks.reduce((n, b) => n + b.length, 0));
  let offset = 0;
  for (const block of blocks) (out.set(block, offset), (offset += block.length));
  return out;
}
const pad = (bytes: Uint8Array) => {
  const out = new Uint8Array(Math.ceil(bytes.length / 512) * 512);
  out.set(bytes);
  return out;
};

describe("untar", () => {
  it("strips the top directory, keeps matching files, and reads pax long names", () => {
    const long = `top-abc/wiki/${"A very long page title that goes on ".repeat(4)}.md`;
    const files = untar(tar({ "top-abc/index.md": "# Index", "top-abc/image.png": "x", [long]: "long" }), (p) => p.endsWith(".md"));
    expect(files["index.md"]).toBe("# Index");
    expect(files["image.png"]).toBeUndefined();
    expect(files[long.split("/").slice(1).join("/")]).toBe("long");
  });
});

describe("lint", () => {
  it("passes a clean vault", () => {
    const files = { ...base(), "index.md": "- [[A]]\n- [[B]]\n", "wiki/A.md": page("A", "See [[B]]."), "wiki/B.md": page("B", "See [[A]].", "entity") };
    expect(lint(files, today)).toEqual({ errors: [], warnings: [] });
  });

  it("reports the same errors as vault_lint.py", () => {
    const files = { ...base(), "index.md": "- [[A]]\n- [[Gone]]\n", "wiki/A.md": page("A", "See [[Missing page]].", "opinion"), "wiki/B.md": "# B\nNo frontmatter. [[A]]\n", "raw/2026-11/bad.md": "---\nurl: x\n---\n" };
    const { errors } = lint(files, today);
    for (const expected of ["broken link [[Missing page]]", "broken link [[Gone]]", "type must be one of", "wiki/B: missing frontmatter", "wiki/B: not listed in index.md", "raw/2026-11/bad: missing frontmatter captured, kind"]) {
      expect(errors.some((e) => e.includes(expected)), expected).toBe(true);
    }
  });

  it("warns on stale and orphan pages", () => {
    const files = { ...base(), "index.md": "- [[A]]\n", "wiki/A.md": page("A", "", "topic", "2026-07-01", "high") };
    const { errors, warnings } = lint(files, today);
    expect(errors).toEqual([]);
    expect(warnings.join("\n")).toMatch(/wiki\/A: stale/);
    expect(warnings.join("\n")).toMatch(/wiki\/A: orphan/);
  });
});

describe("typed links", () => {
  const typed = (title: string, key: string, target: string, body = "") =>
    `---\ntype: topic\nreviewed: 2026-11-01\nvolatility: medium\nsources:\n  - "[[raw/2026-11/2026-11-01 source]]"\n${key}:\n  - "[[${target}]]"\n---\n\n# ${title}\n\n${body}\n`;

  it("reads list fields from frontmatter", () => {
    expect(listField(typed("New", "supersedes", "Old"), "supersedes")).toEqual(["Old"]);
    expect(listField(typed("New", "supersedes", "Old"), "contradicts")).toEqual([]);
  });

  it("requires a superseded page to link its successor and warns on unacknowledged contradictions", () => {
    const files = { ...base(), "index.md": "- [[Old]]\n- [[New]]\n- [[Other]]\n", "wiki/Old.md": page("Old"), "wiki/New.md": typed("New", "supersedes", "Old"), "wiki/Other.md": typed("Other", "contradicts", "Old") };
    const { errors, warnings } = lint(files, today);
    expect(errors).toContain("wiki/Old: superseded by [[New]]; link to it");
    expect(warnings.join("\n")).toMatch(/wiki\/Old: contradicted by \[\[Other\]\]/);
    const fixed = { ...files, "wiki/Old.md": page("Old", "Replaced by [[New]]. Disputed in [[Other]].") };
    expect(lint(fixed, today).errors).toEqual([]);
  });

  it("flags stale and superseded hits and ranks them down", () => {
    const files = { ...base(), "wiki/Old CI.md": page("Old CI", "ci runners cost", "topic", "2026-01-01", "high"), "wiki/New CI.md": typed("New CI", "supersedes", "Old CI", "ci runners cost") };
    const hits = search(files, "ci runners", 8, today);
    expect(hits[0].path).toBe("wiki/New CI.md");
    const old = hits.find((h) => h.path === "wiki/Old CI.md")!;
    expect(old.stale).toBe(true);
    expect(old.superseded_by).toEqual(["New CI"]);
  });
});

describe("search", () => {
  it("ranks the page about the query first and prefers wiki pages", () => {
    const files = { ...base(), "wiki/LLM wiki maintenance.md": page("LLM wiki maintenance", "Lint with a script; stale pages mislead."), "wiki/Other.md": page("Other", "Something about cattle gait.") };
    const hits = search(files, "wiki lint stale");
    expect(hits[0].path).toBe("wiki/LLM wiki maintenance.md");
    expect(hits[0].snippet).toMatch(/Lint|lint/);
    expect(search(files, "zzz")).toEqual([]);
  });
});

describe("writes", () => {
  it("only allows wiki pages and the index through write_page", () => {
    expect(writablePath("wiki/A page.md")).toBe(true);
    expect(writablePath("index.md")).toBe(true);
    for (const path of ["raw/2026-11/x.md", "log.md", "AGENTS.md", "wiki/sub/x.md", "wiki/../AGENTS.md"]) expect(writablePath(path), path).toBe(false);
  });

  it("lets read fetch only paths inside the vault", () => {
    for (const path of ["index.md", "wiki/A page.md", "raw/2026-11/2026-11-01 source.md", ".gitattributes"]) expect(readablePath(path), path).toBe(true);
    for (const path of ["", "../other-repo/contents/README.md", "wiki/../../x", "../../../user", "/index.md", "wiki//A.md", "./index.md", "wiki\\..\\x"]) expect(readablePath(path), path).toBe(false);
  });

  it("validates wiki frontmatter", () => {
    expect(wikiProblems(page("A"))).toEqual([]);
    expect(wikiProblems("# no frontmatter")[0]).toMatch(/missing frontmatter/);
    expect(wikiProblems(page("A", "", "topic", "soon", "extreme")).length).toBe(2);
  });

  it("builds raw captures that pass lint", () => {
    const capture = { slug: "Some Doc!", url: "https://x.dev", title: 'A "quoted" title', kind: "docs", body: "Quote." };
    const path = capturePath(capture, "2026-11-07");
    expect(path).toBe("raw/2026-11/2026-11-07 some-doc.md");
    const files = { ...base(), "index.md": "", [path]: captureText(capture, "2026-11-07") };
    expect(lint(files, today).errors).toEqual([]);
    expect(() => captureText({ ...capture, kind: "blog" }, "2026-11-07")).toThrow(/kind/);
  });

  it("formats greppable log lines", () => {
    expect(logLine("research", "Question\nmore", ["A", "B]]"], "2026-11-07")).toBe("## [2026-11-07] research | Question more | pages: [[A]], [[B]]");
    expect(logLine("research", "Q", ["A"], "2026-11-07", "~$0.12 <b>")).toBe("## [2026-11-07] research | Q | pages: [[A]] | spend: ~$0.12 b");
    expect(() => logLine("delete", "", [], "2026-11-07")).toThrow();
  });
});

describe("skills", () => {
  it("lists skills with frontmatter and files", () => {
    const files = { "skills/j-research/SKILL.md": "---\nname: j-research\ndescription: Research things.\n---\n", "skills/j-research/references/sources.md": "x", "README.md": "x" };
    expect(skills(files)).toEqual([{ name: "j-research", description: "Research things.", files: ["SKILL.md", "references/sources.md"] }]);
  });
});

describe("localDate", () => {
  it("uses the owner's time zone, not UTC", () => {
    const evening = new Date("2026-11-08T04:30:00Z"); // 20:30 on Nov 7 in Los Angeles
    expect(localDate("America/Los_Angeles", evening)).toBe("2026-11-07");
    expect(localDate("UTC", evening)).toBe("2026-11-08");
  });
});

describe("scopeProblems", () => {
  it("accepts a page in j-scope's shape and flags missing sections and Out signals", async () => {
    const { scopeProblems } = await import("../src/vault");
    const full = "# X scope\n\n## Goal and proof\nG\n\n## In\n- A\n\n## Out\n- B: waits. Comes back if users ask.\n\n## Risks accepted\n- R\n";
    expect(scopeProblems(full)).toEqual([]);
    const problems = scopeProblems("# X scope\n\n## Goal and proof\nG\n\n## Out\n- B: waits.\n");
    expect(problems.some((p) => p.includes('"In"'))).toBe(true);
    expect(problems.some((p) => p.includes('"Risks accepted"'))).toBe(true);
    expect(problems.some((p) => p.includes("no signal"))).toBe(true);
  });
});
