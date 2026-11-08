import { AuthorizationError, CimdFetchError, getOAuthApi, OAuthProvider, type AuthRequest, type ConsentDescription, type OAuthProviderOptions } from "@cloudflare/workers-oauth-provider";
import { createMcpHandler } from "@modelcontextprotocol/server";
import { syncIndex } from "./semantic";
import { vaultServer, vaultSnapshot, type VaultEnv } from "./tools";

/**
 * jvault: a personal remote MCP server for a research vault and agent skills.
 * One Worker is both the OAuth authorization server and the protected
 * resource at /mcp. A client is allowed on a consent page, then the person
 * signs in with GitHub; only ALLOWED_GITHUB_ID can complete a grant.
 */
type Env = VaultEnv & {
  RATE_LIMITER: RateLimit;
  ALLOWED_GITHUB_ID: string;
  GITHUB_CLIENT_ID: string;
  GITHUB_CLIENT_SECRET: string;
};
type Props = { githubId: string; login: string };

const MCP_PATH = "/mcp";
const SCOPES = ["vault.read", "vault.write"];

function options(origin: string): OAuthProviderOptions<Env> {
  return {
    apiRoute: MCP_PATH,
    apiHandler: { fetch: (request: Request, env: Env, ctx: ExecutionContext & { props?: Props }) => serveMcp(request, env, ctx, origin) },
    defaultHandler: { fetch: async () => new Response("Not found", { status: 404 }) },
    authorizeEndpoint: "/authorize",
    tokenEndpoint: "/oauth/token",
    clientRegistrationEndpoint: "/oauth/register",
    clientIdMetadataDocumentEnabled: true,
    accessTokenTTL: 60 * 60,
    refreshTokenTTL: 30 * 24 * 60 * 60,
    scopesSupported: SCOPES,
    requiredScopes: ["vault.read"],
    resourceMetadata: { resource: `${origin}${MCP_PATH}`, resource_name: "Jeremy's vault" },
    onError: ({ code, internal }) => console.log(JSON.stringify({ level: "warn", route: "oauth", code, reason: internal?.reason ?? null })),
  } as OAuthProviderOptions<Env>;
}

async function serveMcp(request: Request, env: Env, ctx: ExecutionContext & { props?: Props }, origin: string): Promise<Response> {
  if (ctx.props?.githubId !== env.ALLOWED_GITHUB_ID) return json(403, { error: "access_denied", error_description: "This connection is not for the vault owner." });
  const browserOrigin = request.headers.get("origin");
  if (browserOrigin && browserOrigin !== origin) return json(403, { error: "access_denied", error_description: "Requests from other sites are refused." });
  if (!(await env.RATE_LIMITER.limit({ key: `mcp:${ctx.props.githubId}` })).success) return json(429, { error: "too_many_requests" }, { "retry-after": "60" });
  return createMcpHandler(() => vaultServer(env), { onerror: (error) => console.log(JSON.stringify({ level: "warn", route: "mcp", message: error.message.slice(0, 200) })) }).fetch(request);
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const oauth = () => getOAuthApi(options(url.origin), { ...env });
    try {
      if (url.pathname === "/authorize") return request.method === "POST" ? await decide(request, url, env, oauth()) : await consent(request, oauth());
      if (url.pathname === "/callback") return await callback(request, url, env, oauth());
    } catch (error) {
      return authorizeFailure(error);
    }
    if (url.pathname === "/oauth/register" && !(await env.RATE_LIMITER.limit({ key: "register" })).success) return json(429, { error: "too_many_requests" }, { "retry-after": "60" });
    if (url.pathname === "/") return page(200, "Jeremy's vault", "A personal MCP server. Add https://" + url.host + MCP_PATH + " as a connector in your AI tool.");
    return new OAuthProvider(options(url.origin)).fetch(request, { ...env }, ctx);
  },

  /** Keeps the AI Search index in step with the vault, whichever machine or agent wrote to GitHub. */
  async scheduled(_controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    if (!env.VAULT_SEARCH) return;
    ctx.waitUntil(
      vaultSnapshot(env)
        .then(({ sha, files }) => syncIndex(env.VAULT_SEARCH!, env.OAUTH_KV, files).then((result) => console.log(JSON.stringify({ level: "info", route: "index-sync", vault: sha.slice(0, 7), ...result }))))
        .catch((error) => console.log(JSON.stringify({ level: "warn", route: "index-sync", message: String(error).slice(0, 200) }))),
    );
  },
};

type OAuthApi = ReturnType<typeof getOAuthApi>;

async function consent(request: Request, oauth: OAuthApi): Promise<Response> {
  const authRequest = await oauth.parseAuthRequest(request);
  const details = await oauth.describeConsent(authRequest);
  const transaction = await oauth.beginConsent(authRequest);
  return html(200, consentPage(details, transaction.handle), transaction.headers, formTarget(authRequest.redirectUri));
}

async function decide(request: Request, url: URL, env: Env, oauth: OAuthApi): Promise<Response> {
  const from = request.headers.get("origin");
  if (from && from !== url.origin) return page(403, "Refused", "This form must be sent from this site.");
  const form = await request.formData();
  const handle = String(form.get("handle") ?? "");
  if (form.get("decision") !== "allow") {
    const denied = await oauth.denyConsent(request, handle);
    denied.headers.set("location", denied.redirectTo);
    return new Response(null, { status: 302, headers: denied.headers });
  }
  const approved = await oauth.approveConsent(request, handle, { scope: SCOPES });
  const upstream = await oauth.beginUpstream(approved.request, { headers: approved.headers });
  return redirectToGitHub(url, env.GITHUB_CLIENT_ID, upstream.state, upstream.headers);
}

function redirectToGitHub(url: URL, clientId: string, state: string, headers: Headers): Response {
  const github = new URL("https://github.com/login/oauth/authorize");
  github.searchParams.set("client_id", clientId);
  github.searchParams.set("redirect_uri", `${url.origin}/callback`);
  github.searchParams.set("state", state);
  github.searchParams.set("allow_signup", "false");
  headers.set("location", github.toString());
  return new Response(null, { status: 302, headers });
}

async function callback(request: Request, url: URL, env: Env, oauth: OAuthApi): Promise<Response> {
  const resumed = await oauth.finishUpstream<unknown>(request);
  const code = url.searchParams.get("code");
  if (!code) return page(400, "Sign-in cancelled", "GitHub did not return a sign-in. Start connecting again from your AI tool.");
  const token = (await (
    await fetch("https://github.com/login/oauth/access_token", {
      method: "POST",
      headers: { accept: "application/json", "content-type": "application/json" },
      body: JSON.stringify({ client_id: env.GITHUB_CLIENT_ID, client_secret: env.GITHUB_CLIENT_SECRET, code, redirect_uri: `${url.origin}/callback` }),
    })
  ).json()) as { access_token?: string };
  if (!token.access_token) return page(400, "Sign-in failed", "GitHub did not issue a token. Start connecting again from your AI tool.");
  const user = (await (await fetch("https://api.github.com/user", { headers: { authorization: `Bearer ${token.access_token}`, "user-agent": "jvault", accept: "application/vnd.github+json" } })).json()) as { id?: number; login?: string };
  if (String(user.id) !== env.ALLOWED_GITHUB_ID) return page(403, "Not allowed", "This vault belongs to someone else.");
  const client = await oauth.lookupClient(resumed.request.clientId);
  const { redirectTo } = await oauth.completeAuthorization({
    request: resumed.request as AuthRequest,
    userId: String(user.id),
    metadata: { clientName: client?.clientName?.trim() || resumed.request.clientId, grantedAt: new Date().toISOString() },
    scope: SCOPES,
    props: { githubId: String(user.id), login: user.login ?? "" } satisfies Props,
  });
  resumed.headers.set("location", redirectTo);
  return new Response(null, { status: 302, headers: resumed.headers });
}

function authorizeFailure(error: unknown): Response {
  if (error instanceof AuthorizationError && error.redirectTo) return Response.redirect(error.redirectTo, 302);
  if (error instanceof AuthorizationError) return page(400, "This request cannot continue", `${error.description} Start connecting again from your AI tool.`);
  if (error instanceof CimdFetchError) return page(400, "This app could not be verified", "Start connecting again from your AI tool.");
  throw error;
}

const escape = (value: string) => value.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`);

function consentPage(details: ConsentDescription, handle: string): string {
  const name = escape(details.clientName);
  const verified = details.clientDomain ? `Published by <strong>${escape(details.clientDomain)}</strong>.` : "This app registered itself, so its name is unverified.";
  const loopback = details.redirectIsLoopback ? `<p class="warn">This sends access to an app on your computer. Continue only if you just started connecting from it.</p>` : "";
  return shell(
    `Allow ${name} to use your vault?`,
    `<h1>Allow ${name} to use your vault?</h1>
<p>${verified} Access goes to <strong>${escape(details.redirectHost)}</strong>.</p>
${loopback}
<p>It can read and search your research vault and skills, add captured sources and log entries, and create or edit wiki pages. You sign in with GitHub next; only the vault owner's account is accepted.</p>
<form method="post">
<input type="hidden" name="handle" value="${escape(handle)}">
<div class="actions"><button class="primary" name="decision" value="allow">Allow</button><button name="decision" value="cancel">Cancel</button></div>
</form>`,
  );
}

function shell(title: string, body: string): string {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="referrer" content="same-origin"><title>${title}</title>
<style>:root{color-scheme:light dark}body{margin:0;font:400 15px/1.55 system-ui,-apple-system,sans-serif;background:Canvas;color:CanvasText}main{max-width:520px;margin:48px auto;padding:24px;border:1px solid color-mix(in srgb,CanvasText 15%,transparent);border-radius:12px}h1{font-size:20px;font-weight:600;margin:0 0 8px}.warn{color:#b45309}.actions{display:flex;gap:8px;margin-top:20px}button{font:inherit;font-weight:500;padding:8px 16px;border-radius:8px;border:1px solid color-mix(in srgb,CanvasText 25%,transparent);background:transparent;color:inherit;min-height:44px;cursor:pointer}button.primary{background:CanvasText;color:Canvas}@media (max-width:560px){main{margin:16px;padding:16px}}</style>
</head><body><main>${body}</main></body></html>`;
}

function page(status: number, title: string, message: string): Response {
  return html(status, shell(escape(title), `<h1>${escape(title)}</h1><p>${escape(message)}</p>`));
}

function formTarget(redirectUri: string): string {
  const target = new URL(redirectUri);
  return target.origin === "null" ? target.protocol : target.origin;
}

function html(status: number, body: string, headers: Headers = new Headers(), formTo: string | null = null): Response {
  headers.set("content-type", "text/html; charset=utf-8");
  headers.set("content-security-policy", `default-src 'none'; style-src 'unsafe-inline'; form-action 'self' https://github.com${formTo ? ` ${formTo}` : ""}; frame-ancestors 'none'; base-uri 'none'`);
  headers.set("x-frame-options", "DENY");
  return new Response(body, { status, headers });
}

function json(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...headers } });
}
