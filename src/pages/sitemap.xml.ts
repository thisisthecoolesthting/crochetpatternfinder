// Custom sitemap generator — replaces @astrojs/sitemap which has an
// upstream bug with our content collection setup. Rebuilds on every
// Astro build, includes only published entries.

import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';

const SITE = (import.meta.env.SITE as string | undefined)?.replace(/\/$/, '') || 'https://example.com';

export const GET: APIRoute = async () => {
  const products = await getCollection('products', ({ data }) => data.status === 'published');
  const pillars  = await getCollection('pillars',  ({ data }) => data.status === 'published');
  const articles = await getCollection('articles', ({ data }) => data.status === 'published');

  const urls: Array<{ loc: string; lastmod?: string; changefreq?: string; priority?: string }> = [];

  // Static high-value pages
  urls.push({ loc: `${SITE}/`,          changefreq: 'weekly',  priority: '1.0' });
  urls.push({ loc: `${SITE}/about`,     changefreq: 'monthly', priority: '0.6' });
  urls.push({ loc: `${SITE}/disclosure`,changefreq: 'yearly',  priority: '0.3' });
  urls.push({ loc: `${SITE}/methodology`, changefreq: 'yearly', priority: '0.4' });
  urls.push({ loc: `${SITE}/products`,  changefreq: 'daily',   priority: '0.9' });
  urls.push({ loc: `${SITE}/pillars`,   changefreq: 'weekly',  priority: '0.8' });
  urls.push({ loc: `${SITE}/articles`,  changefreq: 'weekly',  priority: '0.7' });

  for (const p of products) {
    const last = p.data.lastSeen ? new Date(p.data.lastSeen).toISOString().split('T')[0] : undefined;
    urls.push({
      loc: `${SITE}/products/${p.slug}`,
      lastmod: last,
      changefreq: 'weekly',
      priority: '0.8',
    });
  }
  for (const p of pillars) {
    const last = (p.data.updatedAt || p.data.publishedAt)
      ? new Date(p.data.updatedAt || p.data.publishedAt).toISOString().split('T')[0]
      : undefined;
    urls.push({
      loc: `${SITE}/pillars/${p.slug}`,
      lastmod: last,
      changefreq: 'monthly',
      priority: '0.9',
    });
  }
  for (const a of articles) {
    const last = (a.data.updatedAt || a.data.publishedAt)
      ? new Date(a.data.updatedAt || a.data.publishedAt).toISOString().split('T')[0]
      : undefined;
    urls.push({
      loc: `${SITE}/articles/${a.slug}`,
      lastmod: last,
      changefreq: 'monthly',
      priority: '0.7',
    });
  }

  const body = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls.map((u) => {
      const parts = [
        `  <url>`,
        `    <loc>${u.loc}</loc>`,
        u.lastmod ? `    <lastmod>${u.lastmod}</lastmod>` : '',
        u.changefreq ? `    <changefreq>${u.changefreq}</changefreq>` : '',
        u.priority ? `    <priority>${u.priority}</priority>` : '',
        `  </url>`,
      ].filter(Boolean);
      return parts.join('\n');
    }),
    '</urlset>',
  ].join('\n');

  return new Response(body, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
