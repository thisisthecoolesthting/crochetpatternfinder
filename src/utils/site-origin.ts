/**
 * Base site URL from astro.config.mjs `site` (e.g. https://example.com).
 * No trailing slash.
 */
export function siteOrigin(): string {
  const s = import.meta.env.SITE;
  if (typeof s !== 'string' || !s) {
    return '';
  }
  return s.replace(/\/$/, '');
}
