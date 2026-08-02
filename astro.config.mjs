import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

const ASSOCIATE_TAG = process.env.PUBLIC_ASSOCIATE_TAG || 'crochetpatternfinder-20';

function rehypeAugmentProductLinks() {
  const productHrefRe = /^\/products\/([a-z0-9]+)-/i;

  function walk(node) {
    if (!node || !Array.isArray(node.children)) return;
    const out = [];
    for (const child of node.children) {
      if (
        child &&
        child.type === 'element' &&
        child.tagName === 'a' &&
        child.properties &&
        typeof child.properties.href === 'string'
      ) {
        const m = child.properties.href.match(productHrefRe);
        if (m) {
          const asin = m[1].toUpperCase();
          const amazonHref =
            'https://www.amazon.com/dp/' + asin + '?tag=' + ASSOCIATE_TAG + '&linkCode=ll1';

          out.push({
            type: 'element',
            tagName: 'span',
            properties: { className: ['product-link-pair'] },
            children: [
              child,
              {
                type: 'element',
                tagName: 'a',
                properties: {
                  href: amazonHref,
                  rel: 'nofollow sponsored noopener',
                  target: '_blank',
                  className: ['amazon-cta-inline'],
                },
                children: [{ type: 'text', value: 'Check on Amazon →' }],
              },
            ],
          });
          continue;
        }
      }
      walk(child);
      out.push(child);
    }
    node.children = out;
  }

  return (tree) => walk(tree);
}

// https://astro.build/config
export default defineConfig({
  site: 'https://crochetpatternfinder.org',
  trailingSlash: 'never',
  integrations: [tailwind()],
  build: { format: 'directory' },
  markdown: {
    rehypePlugins: [rehypeAugmentProductLinks],
    shikiConfig: { theme: 'github-light' },
  },
});
