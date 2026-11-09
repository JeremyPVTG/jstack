import { readablePath, untar, type Files } from "./vault";

export type Repo = { slug: string; branch: string; token: string };

const API = "https://api.github.com";

export class GitHubError extends Error {
  constructor(readonly status: number, message: string) {
    super(message);
  }
}

async function gh(repo: Repo, path: string, init: RequestInit = {}): Promise<Response> {
  const response = await fetch(`${API}/repos/${repo.slug}${path}`, {
    ...init,
    headers: {
      authorization: `Bearer ${repo.token}`,
      accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28",
      "user-agent": "jvault",
      ...(init.headers ?? {}),
    },
  });
  return response;
}

async function ok(response: Response, what: string): Promise<Response> {
  if (response.ok) return response;
  throw new GitHubError(response.status, `${what}: GitHub ${response.status} ${(await response.text()).slice(0, 200)}`);
}

const toBase64 = (text: string) => {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
};
const fromBase64 = (data: string) => new TextDecoder().decode(Uint8Array.from(atob(data.replace(/\n/g, "")), (c) => c.charCodeAt(0)));

export async function headSha(repo: Repo): Promise<string> {
  const response = await ok(await gh(repo, `/git/ref/heads/${repo.branch}`), "read branch");
  return ((await response.json()) as { object: { sha: string } }).object.sha;
}

/** All matching text files at a commit, from one tarball download. */
export async function snapshotAt(repo: Repo, sha: string, keep: (path: string) => boolean): Promise<Files> {
  const response = await ok(await gh(repo, `/tarball/${sha}`), "download snapshot");
  const tar = await new Response(response.body!.pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
  return untar(new Uint8Array(tar), keep);
}

export async function readFile(repo: Repo, path: string): Promise<{ text: string; sha: string } | null> {
  const response = await gh(repo, `/contents/${encodePath(path)}?ref=${repo.branch}`);
  if (response.status === 404) return null;
  const body = (await (await ok(response, `read ${path}`)).json()) as { content?: string; sha: string; type: string };
  if (body.type !== "file" || body.content === undefined) throw new GitHubError(400, `${path} is not a file`);
  return { text: fromBase64(body.content), sha: body.sha };
}

/** Create (no sha) or replace (sha of the version read). GitHub refuses a stale sha with 409. */
export async function writeFile(repo: Repo, path: string, text: string, message: string, sha?: string): Promise<{ sha: string; commit: string }> {
  const response = await gh(repo, `/contents/${encodePath(path)}`, {
    method: "PUT",
    body: JSON.stringify({ message, content: toBase64(text), branch: repo.branch, ...(sha ? { sha } : {}) }),
  });
  if (response.status === 409 || response.status === 422) {
    throw new GitHubError(409, sha ? `${path} changed since you read it. Read it again, reapply your edit, and retry.` : `${path} already exists. Read it first and pass its sha to replace it.`);
  }
  const body = (await (await ok(response, `write ${path}`)).json()) as { content: { sha: string }; commit: { sha: string } };
  return { sha: body.content.sha, commit: body.commit.sha };
}

/** Refuses a path that is not inside the repo: an empty, "." or ".." segment would move the request to another API route or repository. */
const encodePath = (path: string) => {
  if (!readablePath(path)) throw new GitHubError(400, "Give a path inside the vault, e.g. 'wiki/Page title.md'.");
  return path.split("/").map(encodeURIComponent).join("/");
};
