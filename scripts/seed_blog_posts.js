const fs = require('fs');
const path = require('path');
const { neon } = require('@neondatabase/serverless');

const BLOG_DIR = path.join(__dirname, '..', 'content', 'blog');

const parseFrontmatter = (raw) => {
  const boundary = '---';
  if (!raw.startsWith(boundary)) {
    return { data: {}, body: raw };
  }

  const endIndex = raw.indexOf(`${boundary}\n`, boundary.length);
  if (endIndex === -1) {
    return { data: {}, body: raw };
  }

  const frontmatterBlock = raw.slice(boundary.length, endIndex).trim();
  const body = raw.slice(endIndex + boundary.length + 1).trim();
  const data = {};

  frontmatterBlock.split('\n').forEach((line) => {
    const [key, ...rest] = line.split(':');
    if (!key || rest.length === 0) return;
    data[key.trim()] = rest.join(':').trim();
  });

  return { data, body };
};

const parseTags = (value) => {
  if (!value) return [];
  const trimmed = value.trim();
  if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
    return trimmed
      .slice(1, -1)
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean);
  }
  return trimmed
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean);
};

const buildExcerpt = (body, length = 180) => {
  const text = body.replace(/[#>*_`]/g, '').replace(/\n+/g, ' ').trim();
  if (text.length <= length) return text;
  return `${text.slice(0, length).trim()}…`;
};

const loadPosts = () => {
  if (!fs.existsSync(BLOG_DIR)) return [];
  const files = fs.readdirSync(BLOG_DIR).filter((file) => file.endsWith('.md') || file.endsWith('.mdx'));

  return files.map((file) => {
    const raw = fs.readFileSync(path.join(BLOG_DIR, file), 'utf8');
    const { data, body } = parseFrontmatter(raw);
    const slug = data.slug || file.replace(/\.(md|mdx)$/, '');

    return {
      title: data.title || slug.replace(/-/g, ' '),
      slug,
      excerpt: data.excerpt || buildExcerpt(body),
      body,
      tags: parseTags(data.tags),
      status: 'published',
      published_at: data.date ? new Date(data.date).toISOString() : new Date().toISOString(),
    };
  });
};

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('Missing DATABASE_URL');
    process.exit(1);
  }

  const sql = neon(url);
  const posts = loadPosts();

  if (posts.length === 0) {
    console.log('No blog posts found to seed.');
    return;
  }

  for (const post of posts) {
    await sql.query(
      `
        INSERT INTO blog_posts (
          title,
          slug,
          excerpt,
          body,
          tags,
          status,
          published_at,
          updated_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7, NOW())
        ON CONFLICT (slug) DO UPDATE SET
          title = EXCLUDED.title,
          excerpt = EXCLUDED.excerpt,
          body = EXCLUDED.body,
          tags = EXCLUDED.tags,
          status = EXCLUDED.status,
          published_at = EXCLUDED.published_at,
          updated_at = NOW()
      `,
      [
        post.title,
        post.slug,
        post.excerpt || null,
        post.body,
        Array.isArray(post.tags) ? post.tags : [],
        post.status || 'published',
        post.published_at || null,
      ]
    );
  }

  console.log(`Seeded ${posts.length} blog posts.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
