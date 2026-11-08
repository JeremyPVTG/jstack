// Semantic search over the vault through a Cloudflare AI Search instance (built-in storage).
// GitHub stays the source of truth; the index is a copy, synced by content hash.
import { searchable, type Files, type Semantic } from "./vault";

/** The parts of the AI Search instance binding this Worker uses. */
export type VaultIndex = {
  search(request: { query: string; ai_search_options?: Record<string, unknown> }): Promise<{ chunks: { text: string; item: { key: string } }[] }>;
  items: {
    upload(name: string, content: string): Promise<{ id: string; key: string }>;
    list(options?: { page?: number; per_page?: number }): Promise<{ result: { id: string; key: string }[]; result_info: { total_count: number } }>;
    delete(itemId: string): Promise<void>;
  };
};

const STATE_KEY = "aisearch:indexed"; // path -> sha-1 of the indexed text
const MAX_UPLOADS = 30; // per sync run, to stay inside a Worker's subrequest budget

const hash = async (text: string) => [...new Uint8Array(await crypto.subtle.digest("SHA-1", new TextEncoder().encode(text)))].map((b) => b.toString(16).padStart(2, "0")).join("");

/** Vector matches for a query, or null when the index is unavailable or slow. */
export async function semanticMatches(index: VaultIndex | undefined, query: string, limit: number): Promise<Semantic[] | null> {
  if (!index || !query.trim()) return null;
  try {
    const result = await Promise.race([
      index.search({ query, ai_search_options: { retrieval: { retrieval_type: "vector", max_num_results: Math.min(limit * 3, 50) } } }),
      new Promise<never>((_, reject) => setTimeout(() => reject(new Error("timeout")), 5000)),
    ]);
    return result.chunks.map((chunk) => ({ path: chunk.item.key, text: chunk.text }));
  } catch (error) {
    console.log(JSON.stringify({ level: "warn", route: "semantic", message: String(error).slice(0, 200) }));
    return null;
  }
}

/** Index one file right after a write, so it is searchable before the next scheduled sync. */
export async function indexFile(index: VaultIndex | undefined, kv: KVNamespace, path: string, text: string): Promise<void> {
  if (!index || !searchable(path)) return;
  try {
    await index.items.upload(path, text);
    const state = (await kv.get<Record<string, string>>(STATE_KEY, "json")) ?? {};
    state[path] = await hash(text);
    await kv.put(STATE_KEY, JSON.stringify(state));
  } catch (error) {
    console.log(JSON.stringify({ level: "warn", route: "index-file", path, message: String(error).slice(0, 200) }));
  }
}

/** Bring the index in line with the vault: upload new or changed pages, delete removed ones. */
export async function syncIndex(index: VaultIndex, kv: KVNamespace, files: Files): Promise<{ uploaded: number; deleted: number; pending: number }> {
  const state = (await kv.get<Record<string, string>>(STATE_KEY, "json")) ?? {};
  const wanted = Object.keys(files).filter(searchable).sort();
  const changed: string[] = [];
  for (const path of wanted) if (state[path] !== (await hash(files[path]))) changed.push(path);
  let uploaded = 0;
  for (const path of changed.slice(0, MAX_UPLOADS)) {
    await index.items.upload(path, files[path]);
    state[path] = await hash(files[path]);
    uploaded++;
  }
  const removed = Object.keys(state).filter((path) => files[path] === undefined);
  let deleted = 0;
  if (removed.length) {
    const ids = new Map<string, string>();
    for (let page = 1; page <= 20; page++) {
      const { result } = await index.items.list({ page, per_page: 50 });
      for (const item of result) ids.set(item.key, item.id);
      if (result.length < 50) break;
    }
    for (const path of removed) {
      const id = ids.get(path);
      if (id) await index.items.delete(id);
      delete state[path];
      deleted++;
    }
  }
  await kv.put(STATE_KEY, JSON.stringify(state));
  return { uploaded, deleted, pending: changed.length - uploaded };
}
