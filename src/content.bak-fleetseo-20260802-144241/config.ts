// Astro content collections. Defaults use spawn-time tokens; spawn_site replaces
// crochetpatternfinder-author to match the niche default author.
import { defineCollection, z } from 'astro:content';

const authors = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    role: z.string(),
    credentials: z.string().optional().default(''),
    photoUrl: z.string(),
    shortBio: z.string(),
    joinedAt: z.coerce.date().optional(),
    location: z.string().optional().default(''),
    socials: z
      .object({
        linkedin: z.string().url().optional(),
        instagram: z.string().url().optional(),
        email: z.string().email().optional(),
      })
      .optional(),
  }),
});

const products = defineCollection({
  type: 'content',
  schema: z.object({
    asin: z.string(),
    title: z.string(),
    seoTitle: z.string().optional().default(''),
    metaDescription: z.string().optional().default(''),
    cardTitle: z.string().optional().default(''),
    cardPick: z.string().optional().default(''),
    category: z.string(),
    price: z.number().nullable().optional(),
    rating: z.number().nullable().optional(),
    reviewCount: z.number().nullable().optional(),
    bsr: z.number().nullable().optional(),
    commissionPerSale: z.number().optional().default(0),
    score: z.number().optional().default(0),
    imageUrl: z.string().optional().default(''),
    affiliateUrl: z.string(),
    isPrime: z.boolean().optional().default(false),
    status: z.enum(['draft', 'in_review', 'published']).default('draft'),
    firstSeen: z.string().optional().default(''),
    lastSeen: z.string().optional().default(''),
    tags: z.array(z.string()).optional().default([]),
    author: z.string().optional().default('crochetpatternfinder-author'),
    reviewedAt: z.coerce.date().optional(),
  }),
});

const pillars = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    metaDescription: z.string(),
    publishedAt: z.coerce.date(),
    updatedAt: z.coerce.date().optional(),
    heroImage: z.string().optional(),
    excerpt: z.string(),
    targetKeyword: z.string(),
    relatedProducts: z.array(z.string()).optional().default([]),
    status: z.enum(['draft', 'in_review', 'published']).default('draft'),
    tags: z.array(z.string()).optional().default([]),
    author: z.string().optional().default('crochetpatternfinder-author'),
    reviewedAt: z.coerce.date().optional(),
  }),
});

const articles = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    metaDescription: z.string(),
    publishedAt: z.coerce.date(),
    updatedAt: z.coerce.date().optional(),
    heroImage: z.string().optional(),
    excerpt: z.string(),
    pillarSlug: z.string().optional(),
    relatedProducts: z.array(z.string()).optional().default([]),
    status: z.enum(['draft', 'in_review', 'published']).default('draft'),
    tags: z.array(z.string()).optional().default([]),
    keyTakeaways: z.array(z.string()).optional().default([]),
    author: z.string().optional().default('crochetpatternfinder-author'),
    reviewedAt: z.coerce.date().optional(),
  }),
});

export const collections = {
  authors,
  products,
  pillars,
  articles,
};
