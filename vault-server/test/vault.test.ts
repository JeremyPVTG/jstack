import { describe, expect, it } from "vitest";
import { localDate } from "../src/tools";
import { captureText, capturePath, droppedIndexEntries, guideText, INDEX_SECTIONS, indexEntryProblems, lint, listField, logLine, readablePath, search, skills, untar, upsertIndex, wikiProblems, writablePath, type Files } from "../src/vault";

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

describe("index entries", () => {
  // Shaped like the live index: intro, newest-first sections, groups split by blank lines, a summary with a wikilink, no Entities section.
  const INDEX = [
    "# Index",
    "",
    "Every wiki page with a one-line summary. Agents read this first.",
    "",
    "## Topics",
    "",
    "- [[Newest topic]]: newest (2026-11-20).",
    "- [[Cattle gait analysis]]: gait scoring from video (2026-11-18).",
    "",
    "- [[Older topic]]: builds on [[Cattle gait analysis]] (2026-11-01).",
    "",
    "## Decisions",
    "",
    "- [[Vault server scope]]: what jvault does (2026-11-10).",
    "",
    "## Comparisons",
    "",
    "- [[A vs B]]: compared (2026-11-02).",
    "",
  ].join("\n");
  const entry = (title: string, summary = `about ${title} (2026-11-24).`) => ({ title, summary });
  const linesOf = (text: string) => text.split("\n");
  /** The "## " heading an index line sits under. */
  const sectionOf = (text: string, line: string) => {
    const lines = linesOf(text);
    return lines.slice(0, lines.indexOf(line)).filter((l) => l.startsWith("## ")).pop();
  };

  it("adds a new entry first under its section and changes nothing else", () => {
    const { text, change } = upsertIndex(INDEX, entry("Fresh page"), "Topics");
    expect(change).toBe("added");
    const lines = linesOf(text);
    expect(lines.slice(4, 8)).toEqual(["## Topics", "", "- [[Fresh page]]: about Fresh page (2026-11-24).", "- [[Newest topic]]: newest (2026-11-20)."]);
    expect(lines.filter((l) => l !== "- [[Fresh page]]: about Fresh page (2026-11-24).")).toEqual(linesOf(INDEX));
  });

  it("replaces an existing entry in place, even when it sits under another section", () => {
    const { text, change } = upsertIndex(INDEX, entry("Vault server scope", "new summary (2026-11-24)."), "Topics");
    expect(change).toBe("replaced");
    const before = linesOf(INDEX);
    const after = linesOf(text);
    expect(after.length).toBe(before.length);
    expect(after.filter((l, i) => l !== before[i])).toEqual(["- [[Vault server scope]]: new summary (2026-11-24)."]);
    expect(after.indexOf("- [[Vault server scope]]: new summary (2026-11-24).")).toBe(before.indexOf("- [[Vault server scope]]: what jvault does (2026-11-10)."));
  });

  it("is idempotent: the same entry twice writes once", () => {
    const first = upsertIndex(INDEX, entry("Fresh page"), "Decisions");
    const second = upsertIndex(first.text, entry("Fresh page"), "Decisions");
    expect(second).toEqual({ text: first.text, change: "unchanged" });
    expect(upsertIndex(INDEX, entry("A vs B", "compared (2026-11-02)."), "Comparisons")).toEqual({ text: INDEX, change: "unchanged" });
  });

  it("routes each page type to its section", () => {
    const template = "# Index\n\n## Topics\n\n## Decisions\n\n## Comparisons\n\n## Entities\n";
    for (const [type, heading] of [["topic", "## Topics"], ["decision", "## Decisions"], ["comparison", "## Comparisons"], ["entity", "## Entities"]] as const) {
      const { text } = upsertIndex(template, entry("Page"), INDEX_SECTIONS[type]);
      expect(sectionOf(text, "- [[Page]]: about Page (2026-11-24)."), type).toBe(heading);
    }
  });

  it("appends a missing section at the end", () => {
    const { text, change } = upsertIndex(INDEX, entry("Cloudflare"), "Entities");
    expect(change).toBe("added");
    expect(text).toBe(`${INDEX}\n## Entities\n\n- [[Cloudflare]]: about Cloudflare (2026-11-24).\n`);
    expect(upsertIndex("# Index", entry("X"), "Topics").text).toBe("# Index\n\n## Topics\n\n- [[X]]: about X (2026-11-24).\n");
  });

  it("keeps the file's last newline, or its absence, when the section heading is the last line", () => {
    expect(upsertIndex("# Index\n\n## Topics\n", entry("X"), "Topics").text).toBe("# Index\n\n## Topics\n- [[X]]: about X (2026-11-24).\n");
    expect(upsertIndex("# Index\n\n## Topics", entry("X"), "Topics").text).toBe("# Index\n\n## Topics\n- [[X]]: about X (2026-11-24).");
    expect(upsertIndex("## Topics\n\n", entry("X"), "Topics").text).toBe("## Topics\n\n- [[X]]: about X (2026-11-24).\n");
  });

  it("does not match a title that is a prefix of another title", () => {
    const { text, change } = upsertIndex(INDEX, entry("Cattle gait"), "Topics");
    expect(change).toBe("added");
    expect(text).toContain("- [[Cattle gait analysis]]: gait scoring from video (2026-11-18).");
    expect(text).toContain("- [[Cattle gait]]: about Cattle gait (2026-11-24).");
  });

  it("matches an aliased entry by its title", () => {
    const { text, change } = upsertIndex("## Topics\n\n- [[Page|shown]]: old\n", entry("Page", "new"), "Topics");
    expect(change).toBe("replaced");
    expect(text).toBe("## Topics\n\n- [[Page]]: new\n");
  });

  it("changes exactly one line for every add and replace on a realistic index", () => {
    const titles = ["Newest topic", "Cattle gait analysis", "Older topic", "Vault server scope", "A vs B", "New one", "Cattle"];
    for (const title of titles) {
      for (const section of Object.values(INDEX_SECTIONS)) {
        const { text, change } = upsertIndex(INDEX, entry(title), section);
        const before = linesOf(INDEX);
        const after = linesOf(text);
        if (change === "replaced") {
          expect(after.filter((l, i) => l !== before[i]), `${title} ${section}`).toEqual([`- [[${title}]]: about ${title} (2026-11-24).`]);
        } else if (section === "Entities") {
          expect(text.startsWith(INDEX), `${title} ${section}`).toBe(true);
        } else {
          const line = `- [[${title}]]: about ${title} (2026-11-24).`;
          expect(after.length, `${title} ${section}`).toBe(before.length + 1);
          expect(after.filter((l) => l !== line), `${title} ${section}`).toEqual(before);
        }
      }
    }
  });

  it("accepts a one-line summary with wikilinks and refuses bad entries", () => {
    expect(indexEntryProblems(entry("Page", "builds on [[Other page]] and [[Third|alias]] (2026-11-24)."))).toEqual([]);
    expect(indexEntryProblems(entry("Page", "x".repeat(280)))).toEqual([]);
    expect(indexEntryProblems(entry("Page", "x".repeat(281)))).toEqual(["summary is 281 characters; keep it to 280"]);
    expect(indexEntryProblems(entry("Page", "first line\nsecond line"))).toEqual(["summary must be one line"]);
    expect(indexEntryProblems(entry("Page", ""))).toEqual(["summary is empty"]);
    expect(indexEntryProblems(entry("", "ok"))).toEqual(["title is empty"]);
    for (const title of ["A]]: injected", "A|alias", "A#heading", "[[A", "A\nB", "../AGENTS", "sub/page", "a\\b"]) expect(indexEntryProblems(entry(title, "ok")), title).toHaveLength(1);
  });

  it("finds pages a rewrite of index.md would drop, ignoring entries for deleted pages", () => {
    const pages = new Set(["Newest topic", "Cattle gait analysis", "Older topic", "Vault server scope"]); // no page for "A vs B"
    const rewritten = "# Index\n\n## Topics\n\n- [[newest topic]]: renamed case\n\nSee [[Cattle gait analysis]] in prose.\n";
    expect(droppedIndexEntries(INDEX, rewritten, pages)).toEqual(["Older topic", "Vault server scope"]);
    expect(droppedIndexEntries(INDEX, INDEX, pages)).toEqual([]);
    expect(droppedIndexEntries(INDEX, upsertIndex(INDEX, entry("Older topic", "shorter"), "Topics").text, pages)).toEqual([]);
  });
});

describe("index lint", () => {
  const files = (index: string) => ({ ...base(), "index.md": index, "wiki/A.md": page("A", "See [[B]]."), "wiki/B.md": page("B", "See [[A]].") });

  it("warns once for all entries over 280 characters, naming the longest", () => {
    const index = `- [[A]]: ${"a".repeat(300)}\n- [[B]]: ${"b".repeat(320)}\n- [[A vs C]]: ${"c".repeat(280)}\n`;
    expect(lint({ ...files(index), "wiki/A vs C.md": page("A vs C", "[[A]]"), "wiki/B.md": page("B", "See [[A]] and [[A vs C]].") }, today).warnings).toEqual(["index.md: 2 entries over 280 characters (longest: B, 320)"]);
    expect(lint(files("- [[A]]: short\n- [[B]]: short\n"), today).warnings).toEqual([]);
  });

  it("points unlisted pages at add_to_index", () => {
    expect(lint(files("- [[A]]: short\n"), today).errors).toEqual(["wiki/B: not listed in index.md (fix: add_to_index)"]);
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

describe("guideText", () => {
  const index = "# Index\n\n## Topics\n\n- [[One page]]: first summary (2026-11-01).\n- [[Two page]]: second summary (2026-11-02).\n\n## Decisions\n\n- [[Three page]]: third summary (2026-11-03).\n";

  it("returns the rules and the page count, not the index lines", () => {
    const text = guideText("# Rules\n\nKeep raw sources unchanged.\n", index);
    expect(text).toContain("Keep raw sources unchanged.");
    expect(text).toContain("index.md lists 3 wiki pages");
    expect(text).not.toContain("first summary");
  });

  it("says when the vault has no rules or index", () => {
    const text = guideText(undefined, undefined);
    expect(text).toContain("(no AGENTS.md)");
    expect(text).toContain("index.md lists 0 wiki pages");
  });
});
