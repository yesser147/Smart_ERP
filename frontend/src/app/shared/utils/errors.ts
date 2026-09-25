/** Backend (Spring: { message }) or AI engine (FastAPI: { detail }) error -> readable sentence. */
export function errorMessage(err: any, fallback = 'Something went wrong.'): string {
  if (err?.status === 0) return 'The server cannot be reached. Check that it is running.';
  const body = err?.error;
  if (typeof body?.message === 'string') return body.message;
  if (typeof body?.detail === 'string') return body.detail;
  if (Array.isArray(body?.detail)) {
    // FastAPI validation errors: [{ loc, msg }]
    return body.detail.map((d: any) => d?.msg).filter(Boolean).join(' ') || fallback;
  }
  return fallback;
}
