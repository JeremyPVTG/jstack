import { ESLint } from "eslint";
import { describe, expect, it } from "vitest";

// The lint rules in eslint.config.mjs fire where they should and nowhere else.
// Runs from vault-server/, as `npm test` does.
const eslint = new ESLint();

async function rules(code: string, filePath: string): Promise<(string | null)[]> {
  const [result] = await eslint.lintText(code, { filePath });
  return result.messages.map((message) => message.ruleId);
}

describe("vault-server lint", () => {
  it("bans explicit any", async () => {
    expect(await rules("export const a: any = 1;\n", "src/tools.ts")).toContain("@typescript-eslint/no-explicit-any");
    expect(await rules("export const a = (x: any[]) => x;\n", "test/x.test.ts")).toContain("@typescript-eslint/no-explicit-any");
  });

  it("bans casts in src and test", async () => {
    const cast = "export const n = JSON.parse('1') as number;\n";
    expect(await rules(cast, "src/tools.ts")).toContain("@typescript-eslint/consistent-type-assertions");
    expect(await rules(cast, "test/semantic.test.ts")).toContain("@typescript-eslint/consistent-type-assertions");
    expect(await rules("export const n = <number>JSON.parse('1');\n", "src/vault.ts")).toContain("@typescript-eslint/consistent-type-assertions");
  });

  it("allows as const", async () => {
    expect(await rules("export const a = ['x', 'y'] as const;\n", "src/vault.ts")).toEqual([]);
  });

  it("allows a cast only inside readJson in src/github.ts", async () => {
    const readJson = "export const readJson = <T>(response: Response): Promise<T> => response.json() as Promise<T>;\n";
    expect(await rules(readJson, "src/github.ts")).toEqual([]);
    const other = `${readJson}export const sha = (body: unknown) => (body as { sha: string }).sha;\n`;
    expect(await rules(other, "src/github.ts")).toEqual(["no-restricted-syntax"]);
    expect(await rules(readJson, "src/tools.ts")).toContain("@typescript-eslint/consistent-type-assertions");
  });

  it("passes on the current code", async () => {
    const results = await eslint.lintFiles(["src", "test"]);
    expect(results.flatMap((result) => result.messages.map((m) => `${result.filePath}:${m.line} ${m.ruleId}`))).toEqual([]);
  });
});
