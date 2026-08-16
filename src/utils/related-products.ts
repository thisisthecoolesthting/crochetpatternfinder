// Resolves "related products" for an article or pillar by scanning its
// markdown body for internal /products/<slug>/ links and returning the
// matching published product entries in the order they first appear.
//
// Used by the article + pillar templates to render a "Featured products"
// block and a mobile sticky CTA without authors having to maintain a
// separate `relatedProducts` frontmatter array.

import type { CollectionEntry } from 'astro:content';
import { getCollection } from 'astro:content';

const PRODUCT_LINK_RE = /\/products\/([a-z0-9][a-z0-9\-]*[a-z0-9])\b/gi;

export async function getRelatedProductsFromBody(
  body: string,
): Promise<CollectionEntry<'products'>[]> {
  if (!body) return [];

  const seen = new Set<string>();
  const orderedSlugs: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = PRODUCT_LINK_RE.exec(body)) !== null) {
    const slug = m[1].toLowerCase();
    if (!seen.has(slug)) {
      seen.add(slug);
      orderedSlugs.push(slug);
    }
  }
  if (orderedSlugs.length === 0) return [];

  const allProducts = await getCollection('products', ({ data }) => data.status === 'published');
  const bySlug = new Map(allProducts.map((p) => [p.slug, p]));

  return orderedSlugs
    .map((s) => bySlug.get(s))
    .filter((p): p is CollectionEntry<'products'> => p !== undefined);
}

// Build an Amazon affiliate URL for a product entry. Prefers the
// precomputed affiliateUrl from frontmatter if present; falls back to a
// constructed URL from the ASIN + associate tag.
export function amazonAffiliateUrl(
  product: CollectionEntry<'products'>,
  associateTag = 'retired',
): string {
  // Amazon Associates retired 2026-08 -- never return a live Amazon URL.
  return '#';
}
