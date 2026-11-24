// Type rules for vault-server: one way to get typed data in, so agents
// cannot hide a type error behind `any` or a cast.
// - No `any`, anywhere.
// - No `as` casts except in `readJson` (src/github.ts), the one place a
//   GitHub or OAuth JSON body becomes a typed value. `as const` stays allowed.
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["node_modules/**", "worker-configuration.d.ts", ".wrangler/**"] },
  {
    files: ["src/**/*.ts", "test/**/*.ts"],
    languageOptions: { parser: tseslint.parser },
    plugins: { "@typescript-eslint": tseslint.plugin },
    linterOptions: { reportUnusedDisableDirectives: "error" },
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-assertions": ["error", { assertionStyle: "never" }],
    },
  },
  {
    // The single allowed cast: readJson's `response.json() as Promise<T>`.
    files: ["src/github.ts"],
    rules: {
      "@typescript-eslint/consistent-type-assertions": "off",
      "no-restricted-syntax": [
        "error",
        {
          selector:
            "TSTypeAssertion, TSAsExpression:not([typeAnnotation.typeName.name='const']):not(VariableDeclarator[id.name='readJson'] TSAsExpression)",
          message: "No casts outside readJson in src/github.ts. Parse or narrow the value instead.",
        },
      ],
    },
  },
);
