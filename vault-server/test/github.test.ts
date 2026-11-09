import { afterEach, describe, expect, it, vi } from "vitest";
import { readFile, writeFile, type Repo } from "../src/github";

const repo: Repo = { slug: "owner/vault", branch: "main", token: "t" };

describe("contents paths", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("refuses a path that would leave the repo, without calling GitHub", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    for (const path of ["../other-repo/contents/README.md", "wiki/../../x", "../../../user", "/index.md", ""]) {
      await expect(readFile(repo, path), path).rejects.toThrow("inside the vault");
      await expect(writeFile(repo, path, "text", "message"), path).rejects.toThrow("inside the vault");
    }
    expect(fetch).not.toHaveBeenCalled();
  });

  it("reads an ordinary path from the vault repo", async () => {
    const fetch = vi.fn(async (_url: string) => new Response("{}", { status: 404 }));
    vi.stubGlobal("fetch", fetch);
    expect(await readFile(repo, "wiki/A page.md")).toBeNull();
    expect(fetch.mock.calls[0][0]).toBe("https://api.github.com/repos/owner/vault/contents/wiki/A%20page.md?ref=main");
  });
});
