import { readFile, writeFile, mkdir, cp } from 'node:fs/promises';

// Publish only the website, without rebuilding for each scheduled menu update.
// GitHub Actions continues to refresh the data served by GitHub Pages.
const source = await readFile(new URL('./index.html', import.meta.url), 'utf8');
const localMenu = '"./data/" + hall + ".json"';
if (source.split(localMenu).length !== 2) {
  throw new Error('Expected exactly one menu URL; check the menu loader before deploying.');
}
const output = new URL('./dist/', import.meta.url);
await mkdir(output, { recursive: true });
await writeFile(new URL('index.html', output), source.replace(
  localMenu,
  '"https://nbgraybeal.github.io/vol-dine/data/" + hall + ".json"'
));
await cp(new URL('./images/', import.meta.url), new URL('images/', output), { recursive: true });
console.log('Cloudflare site built in dist; menus remain connected to automatic updates.');
