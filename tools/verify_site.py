import argparse
import base64
from functools import partial
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements = []
        self.text = []
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag, attrs))
        if 'id' in attrs:
            require(attrs['id'] not in self.ids, f'Duplicate HTML id: {attrs["id"]}')
            self.ids.add(attrs['id'])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        self.text.append(data)


def check_sources():
    for name in ('layouts/baseof.html', 'layouts/home.html', 'layouts/page.html', 'layouts/list.html', 'layouts/taxonomy.html', 'layouts/archive.html', 'layouts/404.html', 'layouts/home.rss.xml', 'assets/css/site.css'):
        require(Path(name).is_file(), f'Missing required source: {name}')
    config = tomllib.loads(Path('hugo.toml').read_text())
    require(config['title'] == config['params']['author'] == 'Rinyo', 'Public name must be Rinyo.')
    require(config['markup']['goldmark']['renderer']['unsafe'] is False, 'Raw Markdown HTML must stay disabled.')
    for directory in ('layouts', 'assets', 'static', 'content'):
        for path in Path(directory).rglob('*'):
            if path.is_file() and path.suffix in ('.html', '.css', '.svg', '.md', '.xml'):
                text = path.read_text()
                require('rinyo77' not in text.lower(), f'Deployment username in public source: {path}')
                require('fieldnotes' not in text.lower(), f'Old display name in public source: {path}')
                if path.suffix == '.html':
                    require('<script' not in text.lower(), f'Script in template: {path}')
                    for name in re.findall(r'partial "([^"]+)"', text):
                        require((Path('layouts/_partials') / name).is_file(), f'Missing partial: {name}')
    for path in Path('content').rglob('*.md'):
        parts = path.read_text().split('+++', 2)
        require(len(parts) == 3 and not parts[0].strip(), f'Expected TOML front matter: {path}')
        require(tomllib.loads(parts[1]).get('title'), f'Missing title: {path}')
    ET.parse('static/favicon.svg')
    print('PASS: source identity, configuration, content headers, partial references, favicon XML.', flush=True)


def local_target(root, base_url, page_url, link):
    parsed = urlsplit(urljoin(page_url, link))
    base = urlsplit(base_url)
    if parsed.scheme not in ('http', 'https') or parsed.netloc != base.netloc:
        return None, ''
    prefix = base.path.rstrip('/') + '/'
    path = unquote(parsed.path)
    require(path.startswith(prefix), f'URL escapes deployment base path: {link}')
    relative = Path(path[len(prefix):])
    require('..' not in relative.parts, f'Unsafe generated URL: {link}')
    target = root / relative
    if target.is_dir():
        target /= 'index.html'
    require(target.is_file(), f'Broken local link: {page_url} → {link}')
    return target, unquote(parsed.fragment)


def check_html(root, base_url):
    paths = sorted(root.rglob('*.html'))
    require(paths, 'Hugo produced no HTML pages.')
    documents = {path: Page(path.read_text()) for path in paths}
    for path, page in documents.items():
        try:
            visible = ' '.join(page.text)
            require('rinyo77' not in visible.lower(), 'GitHub username appears in page text.')
            require('fieldnotes' not in visible.lower(), 'Old display name appears in page text.')
            require('Rinyo' in visible, 'Public display name is missing.')
            require(sum(tag == 'h1' for tag, _ in page.elements) == 1, 'Expected exactly one h1.')
            require(sum(tag == 'main' for tag, _ in page.elements) == 1, 'Expected exactly one main landmark.')
            require(any(tag == 'html' and attrs.get('lang') == 'en' for tag, attrs in page.elements), 'Missing English language declaration.')
            require(any(tag == 'meta' and attrs.get('name') == 'author' and attrs.get('content') == 'Rinyo' for tag, attrs in page.elements), 'Incorrect author metadata.')
            policies = [attrs.get('content', '') for tag, attrs in page.elements if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'content-security-policy']
            require(len(policies) == 1 and "script-src 'none'" in policies[0], 'Missing script-blocking CSP.')
            require(any(tag == 'a' and attrs.get('href') == '#main' for tag, attrs in page.elements), 'Missing skip link.')
            page_url = urljoin(base_url, path.relative_to(root).as_posix())
            stylesheets = 0
            for tag, attrs in page.elements:
                require(tag not in ('script', 'iframe', 'object', 'embed', 'form', 'base'), f'Unexpected active element: {tag}')
                require('style' not in attrs and not any(name.startswith('on') for name in attrs), 'Inline styles or event handlers are not allowed.')
                for name in ('aria-label', 'title', 'alt'):
                    require('rinyo77' not in attrs.get(name, '').lower(), f'GitHub username in {name}.')
                if tag == 'img':
                    require('alt' in attrs, 'Image is missing alt text.')
                for name in ('href', 'src'):
                    if name not in attrs:
                        continue
                    target, fragment = local_target(root, base_url, page_url, attrs[name])
                    if name == 'src' or tag == 'link':
                        require(target is not None, f'External resource: {attrs[name]}')
                    if fragment and target in documents:
                        require(fragment in documents[target].ids, f'Broken fragment: {attrs[name]}')
                    if tag == 'link' and attrs.get('rel') == 'stylesheet':
                        stylesheets += 1
                        digest = base64.b64encode(hashlib.sha384(target.read_bytes()).digest()).decode()
                        require(attrs.get('integrity') == 'sha384-' + digest, 'Stylesheet integrity mismatch.')
            require(stylesheets == 1, 'Expected one local stylesheet.')
        except RuntimeError as error:
            raise RuntimeError(f'{path}: {error}') from error
    for required in ('index.html', 'about/index.html', 'archive/index.html', 'topics/index.html', '404.html'):
        require((root / required).is_file(), f'Missing required page: {required}')
    feed = ET.parse(root / 'index.xml')
    require(feed.findtext('channel/title') == 'Rinyo', 'Incorrect feed display name.')
    for item in feed.findall('channel/item'):
        require('rinyo77' not in (item.findtext('title', '') + item.findtext('description', '')).lower(), 'GitHub username appears in RSS display text.')
        local_target(root, base_url, base_url, item.findtext('link', ''))
    ET.parse(root / 'sitemap.xml')
    print(f'PASS: {len(paths)} generated HTML pages, identity, links/fragments, CSS integrity, RSS, sitemap at {base_url}', flush=True)


def executable(env_name, names):
    candidates = [os.environ[env_name]] if os.environ.get(env_name) else names
    for name in candidates:
        found = shutil.which(name)
        if found:
            relative = os.path.relpath(found)
            return relative if '/' in relative else './' + relative
    raise RuntimeError(f'{env_name} unavailable; provide an existing executable. No replacement or simulated result will be used.')


def screenshots(browser, base_url, output):
    require(not hasattr(os, 'geteuid') or os.geteuid() != 0, 'Run the browser as an ordinary user, not with sudo.')
    routes = [('home', ''), ('about', 'about/'), ('topics', 'topics/'), ('archive', 'archive/'), ('not-found', '404.html')]
    for label, section in (('article', 'journal'), ('topic', 'topics')):
        candidates = sorted(output.glob(f'{section}/*/index.html'))
        if candidates:
            routes.append((label, candidates[0].parent.relative_to(output).as_posix() + '/'))
    destination = Path('.verification/screenshots')
    destination.mkdir(parents=True, exist_ok=True)
    for name, route in routes:
        for width, height in ((1440, 1050), (390, 844)):
            image = destination / f'{name}-{width}.png'
            image.unlink(missing_ok=True)
            with tempfile.TemporaryDirectory(dir='.verification', prefix='chrome-') as profile:
                flags = [browser, '--headless', '--disable-gpu', '--disable-background-networking', '--no-first-run', '--no-default-browser-check', '--force-device-scale-factor=1', f'--user-data-dir={profile}', f'--window-size={width},{height}', '--timeout=10000']
                url = urljoin(base_url, route)
                capture = subprocess.run(flags + [f'--screenshot={image}', url], text=True, capture_output=True, timeout=45)
                require(capture.returncode == 0, f'Browser capture failed for {route}: {capture.stderr[-2000:]}')
                result = subprocess.run(flags + ['--dump-dom', url], text=True, capture_output=True, timeout=45)
                require(result.returncode == 0, f'Browser failed for {route}: {result.stderr[-2000:]}')
                dom = Page(result.stdout)
                require(any(tag == 'main' for tag, _ in dom.elements), f'Browser did not load the site: {route}')
                require('rinyo77' not in ' '.join(dom.text).lower(), f'GitHub username in browser DOM: {route}')
                require(image.is_file(), f'Browser did not create {image}')
                header = image.read_bytes()[:24]
                require(header[:8] == b'\x89PNG\r\n\x1a\n', f'Invalid screenshot: {image}')
                require(int.from_bytes(header[16:20], 'big') == width and int.from_bytes(header[20:24], 'big') == height, f'Unexpected screenshot dimensions: {image}')
                print(f'CAPTURED: {image}', flush=True)


def main():
    parser = argparse.ArgumentParser(description='Build with actual Hugo and verify actual browser output.')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--source-only', action='store_true')
    mode.add_argument('--html-only', action='store_true', help='Run Hugo without a browser; not visual sign-off.')
    args = parser.parse_args()
    check_sources()
    if args.source_only:
        print('SOURCE CHECKS ONLY: no Hugo build or rendered verification was performed.')
        return
    Path('.verification').mkdir(exist_ok=True)
    report_path = Path('.verification/automatic-status.json')
    report = {'hugo_builds_passed': False, 'browser_captures_passed': False, 'manual_visual_review': 'pending', 'site_complete': False}
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    hugo = executable('HUGO_BIN', ['.cache/hugo/hugo', 'hugo'])
    version = subprocess.run([hugo, 'version'], check=True, capture_output=True, text=True).stdout.strip()
    require(re.search(r'\bv0\.166\.0(?:\D|$)', version), 'Use Hugo 0.166.0 to match this handoff.')
    report['hugo_version'] = version
    print(version, flush=True)
    browser = None
    if not args.html_only:
        browser = executable('CHROME_BIN', ['google-chrome', 'chromium', 'chromium-browser', 'chrome'])
        browser_version = subprocess.run([browser, '--version'], check=True, capture_output=True, text=True).stdout.strip()
        report['browser_version'] = browser_version
        print(browser_version, flush=True)
    with tempfile.TemporaryDirectory(dir='.verification', prefix='build-') as directory:
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=directory))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f'http://127.0.0.1:{server.server_port}/'
            output = Path(directory)
            subprocess.run([hugo, '--gc', '--minify', '--panicOnWarning', '--baseURL', base_url, '--destination', str(output)], check=True)
            check_html(output, base_url)
            project_output = output / 'notebook'
            subprocess.run([hugo, '--gc', '--minify', '--panicOnWarning', '--baseURL', base_url + 'notebook/', '--destination', str(project_output)], check=True)
            check_html(project_output, base_url + 'notebook/')
            report['hugo_builds_passed'] = True
            report_path.write_text(json.dumps(report, indent=2) + '\n')
            if browser:
                screenshots(browser, base_url, output)
                report['browser_captures_passed'] = True
                report_path.write_text(json.dumps(report, indent=2) + '\n')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
    print('PASS: requested automated checks. Site remains incomplete until manual visual and keyboard review pass.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError, tomllib.TOMLDecodeError, ET.ParseError) as error:
        print(f'INCOMPLETE: {error}', file=sys.stderr)
        sys.exit(1)