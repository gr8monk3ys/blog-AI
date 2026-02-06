const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');

const BLOG_DIR = path.join(__dirname, '..', 'frontend', 'content', 'blog');

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
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;

  if (!url || !key) {
    console.error('Missing NEXT_PUBLIC_SUPABASE_URL or SUPABASE_SERVICE_KEY');
    process.exit(1);
  }

  const supabase = createClient(url, key);
  const posts = loadPosts();

  if (posts.length === 0) {
    console.log('No blog posts found to seed.');
    return;
  }

  const { error } = await supabase.from('blog_posts').upsert(posts, {
    onConflict: 'slug',
  });

  if (error) {
    console.error('Failed to seed blog posts:', error.message);
    process.exit(1);
  }

  console.log(`Seeded ${posts.length} blog posts.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
