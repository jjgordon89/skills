#!/usr/bin/env node
/**
 * Register as a mentor on the OpenClaw Mentor relay.
 * Usage: node register.js --name "Jean" --description "..." --specialties "memory,heartbeats"
 */

const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(`--${name}`);
  return idx >= 0 && idx + 1 < args.length ? args[idx + 1] : null;
}

const RELAY_URL = process.env.MENTOR_RELAY_URL || 'https://mentor.telegraphic.app';
const name = getArg('name');
const slug = getArg('slug') || '';
const description = getArg('description') || '';
const specialtiesStr = getArg('specialties') || '';
const github = getArg('github') || '';
const owner = getArg('owner') || '';

if (!name) {
  console.error('Usage: node register.js --name "Name" [--slug "my-slug"] [--description "..."] [--specialties "a,b,c"] [--github "username"] [--owner "github-user"]');
  process.exit(1);
}

const specialties = specialtiesStr ? specialtiesStr.split(',').map(s => s.trim()) : [];

async function main() {
  const res = await fetch(`${RELAY_URL}/api/mentor/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, slug: slug || undefined, description, specialties, github_username: github, owner: owner || undefined }),
  });

  const data = await res.json();

  if (!res.ok) {
    console.error('Registration failed:', data.error);
    process.exit(1);
  }

  console.log('✅ Registered successfully!');
  console.log(`   Mentor ID: ${data.mentor_id}`);
  console.log(`   Slug: ${data.slug}`);
  console.log(`   Profile: ${RELAY_URL}/mentors/${data.slug}`);
  console.log(`   Status: ${data.status} (needs approval)`);
  console.log(`   Token: ${data.token}`);
  if (data.claim_url) {
    console.log(`   Claim URL: ${data.claim_url}`);
    console.log('');
    console.log('Send this claim URL to your human to bind this mentor to their GitHub account.');
  }
  console.log('');
  console.log('Add to your .env:');
  console.log(`   MENTOR_RELAY_TOKEN=${data.token}`);
}

main().catch(err => { console.error(err); process.exit(1); });
