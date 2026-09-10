#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NODE_SCRIPT = os.path.join(SCRIPT_DIR, 'downloader.js')

def _ua():
    return (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/131.0.0.0 Safari/537.36'
    )


def _http_get(url, headers=None, timeout=17):

    req_headers = {
        'User-Agent': _ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Upgrade-Insecure-Requests': '1',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    resp = urllib.request.urlopen(req, timeout=timeout)
    raw = resp.read()
    enc = resp.headers.get('Content-Encoding', '')
    if enc == 'br':
        import brotli
        raw = brotli.decompress(raw)
    elif enc == 'gzip':
        import gzip
        raw = gzip.decompress(raw)
    return resp.status, raw, dict(resp.headers)


def scrape_metadata(url):
    """Scrape file metadata dari share page."""
    status, raw, _ = _http_get(url)
    data = raw.decode('utf-8', errors='replace')

    result = {
        'url': url,
        'title': None,
        'description': None,
        'download_url': None,
        'size': None,
        'downloads': None,
        'author': None,
        'category': None,
        'timestamp': datetime.now().isoformat(),
        'source': 'missav.com',
        'ustad': 'Black Swan ♤',
    }

    m = re.search(r'<title[^>]*>(.*?)</title>', data, re.I | re.S)
    if m:
        result['title'] = m.group(1).strip()

    m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)', data, re.I)
    if m:
        result['description'] = m.group(1)

    m = re.search(r'data-dw-url="([^"]+)"', data)
    if m:
        result['download_url'] = m.group(1)

    m = re.search(r'(\d+\.?\d*\s*(?:MB|GB|KB|bytes?))', data, re.I)
    if m:
        result['size'] = m.group(1)

    m = re.search(r'userInteractionCount["\':\s]+(\d+)', data)
    if m:
        result['downloads'] = int(m.group(1))

    m = re.search(r'<a[^>]*href=["\'][^"\']*/user/[^"\']*["\'][^>]*>([^<]+)', data)
    if m:
        result['author'] = m.group(1).strip()

    m = re.search(r'<a[^>]*href=["\'][^"\']*category[^"\']*["\'][^>]*>([^<]+)', data)
    if m:
        result['category'] = m.group(1).strip()

    return result


def _node_run(args, timeout=45):

    proc = subprocess.run(
        ['node', NODE_SCRIPT, *args],
        capture_output=True, text=True, timeout=timeout,
        cwd=SCRIPT_DIR,
    )
    if proc.returncode != 0:
        raise RuntimeError(f'node downloader.js failed: {proc.stderr.strip() or proc.stdout.strip()}')
    out = proc.stdout.strip()
    if not out:
        raise RuntimeError(f'node downloader.js produced no output. stderr: {proc.stderr.strip()}')
    return json.loads(out)


def resolve_direct_url(share_url):

    return _node_run(['resolve', share_url])


def download_from_share(share_url, output_path):

    return _node_run(['download', share_url, output_path])


def main():
    args = sys.argv[1:]
    url = None
    output_json = None
    output_file = None
    download_path = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '-o' and i + 1 < len(args):
            output_json = args[i + 1]; i += 2; continue
        elif a == '--direct':
            output_file = True; i += 1; continue
        elif a == '--download' and i + 1 < len(args):
            download_path = args[i + 1]; i += 2; continue
        elif a in ('-h', '--help'):
            print(__doc__); sys.exit(0)
        elif not a.startswith('-'):
            url = a; i += 1; continue
        else:
            print(f'Unknown arg: {a}', file=sys.stderr); sys.exit(2)

    if not url:
        print('Usage: python main.py <URL> [-o out.json] [--direct] [--download out.hc]', file=sys.stderr)
        sys.exit(1)

    if not url.startswith('http'):
        url = 'https://' + url

    result = scrape_metadata(url)

    if output_file or download_path:
        print('menganu sfile untuk dapat direct link with node.js...', file=sys.stderr)
        try:
            resolved = resolve_direct_url(url)
            result['direct_url'] = resolved.get('direct_url')
            result['cdn_url'] = resolved.get('cdn_url')
            result['bypassed_wait'] = resolved.get('bypassed_wait')
        except RuntimeError as e:
            print(f'  Resolve failed: {e}', file=sys.stderr)
            result['direct_url'] = None
            result['cdn_url'] = None

        if download_path:
            # PATH DL
            requested_path = os.path.abspath(download_path)
            filename = result.get('title') or os.path.basename(requested_path)
            filename = os.path.basename(filename)
            stem, extension = os.path.splitext(filename)
            if not extension:
                extension = '.hc'
                filename = stem + extension

            result_dir = os.path.join('result', stem)
            os.makedirs(result_dir, exist_ok=True)
            download_path = os.path.join(result_dir, filename)

            # Jika -o tidak diberikan, simpan metadata di folder yang sama.
            auto_output_json = not output_json
            if auto_output_json:
                output_json = os.path.join(result_dir, stem + '.json')

            print(f'Downloading to {download_path}...', file=sys.stderr)
            try:
                dl = download_from_share(url, download_path)
                result['download_result'] = dl.get('download')

                # Gunakan filename aktual yang dikembalikan downloader.
                actual_filename = os.path.basename(
                    result['download_result'].get('filename') or filename
                )
                if actual_filename != filename:
                    actual_stem = os.path.splitext(actual_filename)[0]
                    actual_dir = os.path.join('result', actual_stem)
                    os.makedirs(actual_dir, exist_ok=True)
                    actual_path = os.path.join(actual_dir, actual_filename)
                    if os.path.exists(download_path):
                        os.replace(download_path, actual_path)
                    download_path = actual_path
                    result['download_result']['path'] = actual_path
                    if auto_output_json:
                        output_json = os.path.join(actual_dir, actual_stem + '.json')

                if result['download_result'].get('success'):
                    print(f'  OK: {result["download_result"]["size"]} bytes', file=sys.stderr)
                else:
                    print(f'  FAIL: {result["download_result"].get("error")}', file=sys.stderr)
            except RuntimeError as e:
                result['download_result'] = {'success': False, 'error': str(e)}
                print(f'  FAIL: {e}', file=sys.stderr)

    out = json.dumps(result, indent=2, ensure_ascii=False)
    if output_json:
        with open(output_json, 'w', encoding='utf-8') as f:
            f.write(out)
        print(f'Saved to: {output_json}')
    else:
        print(out)


if __name__ == '__main__':
    main()

