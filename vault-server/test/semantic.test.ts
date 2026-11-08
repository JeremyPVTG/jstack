import { describe, expect, it } from "vitest";
import { semanticMatches, syncIndex, type VaultIndex } from "../src/semantic";
import { fuse, search, type Files } from "../src/vault";

const page = (title: string, body = "", extra = "") =>
  `---\ntype: topic\nreviewed: 2026-11-01\nvolatility: medium\nsources:\n  - "[[raw/2026-11/2026-11-01 s]]"\n${extra}---\n\n# ${title}\n\n${body}\n`;
const today = new Date("2026-11-07");

describe("fuse", () => {
  const files: Files = {
    "wiki/Runner costs.md": page("Runner costs", "CI runners on boat are cheaper."),
    "wiki/Build machines.md": page("Build machines", "Where continuous integration jobs execute."),
    "raw/2026-11/2026-11-01 s.md": "---\nurl: https://x\ncaptured: 2026-11-01\nkind: docs\n---\nCI runners pricing.\n",
  };

  it("adds pages that only match by meaning, and marks how each hit matched", () => {
    const keyword = search(files, "ci runners", 50, today);
    const hits = fuse(files, keyword, [{ path: "wiki/Build machines.md", text: "Where continuous integration jobs execute." }, { path: "wiki/Runner costs.md", text: "x" }], 8, today);
    expect(hits.map((h) => [h.path, h.match])).toEqual([
      ["wiki/Runner costs.md", "both"],
      ["wiki/Build machines.md", "semantic"],
      ["raw/2026-11/2026-11-01 s.md", "keyword"],
    ]);
    expect(hits[1].title).toBe("Build machines");
    expect(hits[1].snippet).toContain("continuous integration");
  });

  it("drops semantic matches for files no longer in the vault", () => {
    expect(fuse(files, [], [{ path: "wiki/Deleted.md", text: "gone" }], 8, today)).toEqual([]);
  });

  it("keeps stale and superseded flags on semantic-only hits", () => {
    const withNew = { ...files, "wiki/New.md": page("New", "", 'supersedes:\n  - "[[Build machines]]"\n') };
    const [hit] = fuse(withNew, [], [{ path: "wiki/Build machines.md", text: "t" }], 8, new Date("2027-06-01"));
    expect(hit.superseded_by).toEqual(["New"]);
    expect(hit.stale).toBe(true);
  });
});

function fakeIndex() {
  const items = new Map<string, string>();
  const calls: string[] = [];
  const index: VaultIndex = {
    search: async () => ({ chunks: [{ text: "chunk", item: { key: "wiki/A.md" } }] }),
    items: {
      upload: async (name, content) => (calls.push(`up ${name}`), items.set(name, content), { id: `id-${name}`, key: name }),
      list: async () => ({ result: [...items.keys()].map((key) => ({ id: `id-${key}`, key })), result_info: { total_count: items.size } }),
      delete: async (id) => (calls.push(`del ${id}`), void items.delete(id.slice(3))),
    },
  };
  return { index, items, calls };
}

function fakeKv(): KVNamespace {
  const store = new Map<string, string>();
  return {
    get: async (key: string, type?: string) => (store.has(key) ? (type === "json" ? JSON.parse(store.get(key)!) : store.get(key)) : null),
    put: async (key: string, value: string) => void store.set(key, value),
  } as unknown as KVNamespace;
}

describe("syncIndex", () => {
  it("uploads new and changed pages only, and deletes removed ones", async () => {
    const { index, calls } = fakeIndex();
    const kv = fakeKv();
    const files: Files = { "wiki/A.md": "a", "raw/x/B.md": "b", "index.md": "i", "wiki/notes.txt": "n" };
    expect(await syncIndex(index, kv, files)).toEqual({ uploaded: 2, deleted: 0, pending: 0 });
    expect(await syncIndex(index, kv, files)).toEqual({ uploaded: 0, deleted: 0, pending: 0 });
    calls.length = 0;
    expect(await syncIndex(index, kv, { "wiki/A.md": "a2" })).toEqual({ uploaded: 1, deleted: 1, pending: 0 });
    expect(calls).toEqual(["up wiki/A.md", "del id-raw/x/B.md"]);
  });

  it("caps uploads per run and reports what is left", async () => {
    const { index } = fakeIndex();
    const files: Files = Object.fromEntries(Array.from({ length: 35 }, (_, i) => [`wiki/P${i}.md`, `p${i}`]));
    const kv = fakeKv();
    expect(await syncIndex(index, kv, files)).toEqual({ uploaded: 30, deleted: 0, pending: 5 });
    expect(await syncIndex(index, kv, files)).toEqual({ uploaded: 5, deleted: 0, pending: 0 });
  });
});

describe("semanticMatches", () => {
  it("maps chunks to paths, and returns null without an index or on failure", async () => {
    expect(await semanticMatches(fakeIndex().index, "q", 8)).toEqual([{ path: "wiki/A.md", text: "chunk" }]);
    expect(await semanticMatches(undefined, "q", 8)).toBeNull();
    const broken = { ...fakeIndex().index, search: async () => { throw new Error("down"); } };
    expect(await semanticMatches(broken, "q", 8)).toBeNull();
  });
});
