"""Builds dark_mode.svg and light_mode.svg: a neofetch-style profile card.

Run by .github/workflows/build.yaml every day so the uptime and GitHub stats stay current.
Locally: set GITHUB_TOKEN (e.g. `gh auth token`) and run `python today.py`.
Edit INFO / CONTACT below to change what the card says; ascii.txt holds the portrait.
"""
import datetime
import html
import os

import requests

USER = os.environ.get('USER_NAME', 'DAPHOENIX2000')
TOKEN = os.environ.get('GITHUB_TOKEN') or os.environ.get('ACCESS_TOKEN')
UPTIME_SINCE = datetime.date(2022, 11, 7)  # GitHub join date; swap for a birthday if you like
WIDTH = 60  # characters per info line

# (key, value) rows; None = blank spacer row. Dotted keys render as Key.Sub.
INFO = [
    ('OS', 'Windows 11, Android, Linux'),
    ('Uptime', '__UPTIME__'),
    ('Host', 'Harbin Institute of Technology, Shenzhen'),
    ('Kernel', 'M.Eng. Computer Technology'),
    ('IDE', 'VSCode, Jupyter, Claude Code'),
    None,
    ('Languages.Programming', 'Python, JS/TS, Kotlin, Java, C++'),
    ('Languages.Computer', 'HTML, CSS, SQL, LaTeX, JSON'),
    ('Languages.Real', 'Arabic, French, English, Chinese'),
    None,
    ('Research.Thesis', 'Radar nowcasting + LoRA / S2FT'),
    ('Projects.Built', 'Dusty AI, Sprout Android, Study App'),
    ('Hobbies.Creative', 'UI/UX & graphic design, photography'),
    ('Hobbies.Physical', 'Swimming, fitness'),
]
CONTACT = [
    ('Email.Personal', 'yachouak19@gmail.com'),
    ('GitHub', USER),
    ('Website', 'daphoenix2000.github.io/study-app'),
]

THEMES = {
    'dark_mode.svg': dict(bg='#161b22', text='#c9d1d9', key='#ffa657', value='#a5d6ff', cc='#616e7f'),
    'light_mode.svg': dict(bg='#f6f8fa', text='#24292f', key='#953800', value='#0a3069', cc='#c2cfde'),
}


def gql(query, variables=None):
    r = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables or {}},
                      headers={'Authorization': f'bearer {TOKEN}'}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if 'errors' in data:
        raise RuntimeError(data['errors'])
    return data['data']


def github_stats():
    user = gql('''query($login: String!) { user(login: $login) {
        createdAt
        followers { totalCount }
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
        repositories(ownerAffiliations: OWNER, first: 100, isFork: false) { totalCount nodes { stargazerCount } }
    } }''', {'login': USER})['user']
    commits = 0
    start = int(user['createdAt'][:4])
    for year in range(start, datetime.date.today().year + 1):
        c = gql('''query($login: String!, $from: DateTime!, $to: DateTime!) { user(login: $login) {
            contributionsCollection(from: $from, to: $to) { totalCommitContributions restrictedContributionsCount }
        } }''', {'login': USER, 'from': f'{year}-01-01T00:00:00Z', 'to': f'{year}-12-31T23:59:59Z'})
        cc = c['user']['contributionsCollection']
        commits += cc['totalCommitContributions'] + cc['restrictedContributionsCount']
    repos = user['repositories']
    return {
        'repos': repos['totalCount'],
        'contrib': user['repositoriesContributedTo']['totalCount'],
        'stars': sum(n['stargazerCount'] for n in repos['nodes']),
        'commits': commits,
        'followers': user['followers']['totalCount'],
    }


def uptime(since):
    today = datetime.date.today()
    y, m, d = today.year - since.year, today.month - since.month, today.day - since.day
    if d < 0:
        m -= 1
        prev = today.replace(day=1) - datetime.timedelta(days=1)
        d += prev.day
    if m < 0:
        y -= 1
        m += 12
    plural = lambda n, w: f'{n} {w}' + ('' if n == 1 else 's')
    return ', '.join([plural(y, 'year'), plural(m, 'month'), plural(d, 'day')])


def esc(s):
    return html.escape(s, quote=False)


def key_spans(key):
    parts = key.split('.')
    return '.'.join(f'<tspan class="key">{esc(p)}</tspan>' for p in parts), len(key)


def info_line(key, value, width=WIDTH):
    """'. Key: ...... value' padded with dots to exactly `width` characters."""
    kspans, klen = key_spans(key)
    dots = width - 2 - klen - 1 - len(value) - 2
    dots = max(dots, 1)
    return (f'<tspan class="cc">. </tspan>{kspans}:<tspan class="cc"> {"." * dots} </tspan>'
            f'<tspan class="value">{esc(value)}</tspan>')


def pair(key, value, width):
    kspans, klen = key_spans(key)
    dots = max(width - klen - 1 - len(value) - 2, 1)
    return f'{kspans}:<tspan class="cc"> {"." * dots} </tspan><tspan class="value">{esc(value)}</tspan>'


def header(title, width=WIDTH):
    return f'{esc(title)} -' + '—' * (width - len(title) - 5) + '-—-'


def build(theme, ascii_rows, stats):
    x0, y0, lh, xr = 15, 30, 20, 390
    rows = []  # right column tspans
    y = y0
    rows.append(f'<tspan x="{xr}" y="{y}">{header("yassine@achouak")}</tspan>')
    for item in INFO:
        y += lh
        if item is None:
            rows.append(f'<tspan x="{xr}" y="{y}" class="cc">. </tspan>')
        else:
            k, v = item
            if v == '__UPTIME__':
                v = uptime(UPTIME_SINCE)
            rows.append(f'<tspan x="{xr}" y="{y}">{info_line(k, v)}</tspan>')
    y += lh * 2
    rows.append(f'<tspan x="{xr}" y="{y}">{header("- Contact")}</tspan>')
    for k, v in CONTACT:
        y += lh
        rows.append(f'<tspan x="{xr}" y="{y}">{info_line(k, v)}</tspan>')
    y += lh * 2
    rows.append(f'<tspan x="{xr}" y="{y}">{header("- GitHub Stats")}</tspan>')
    s = {k: f'{v:,}' for k, v in stats.items()}
    y += lh
    rows.append(f'<tspan x="{xr}" y="{y}"><tspan class="cc">. </tspan>'
                f'{pair("Repos", s["repos"], 16)} {{<tspan class="key">Contributed</tspan>: '
                f'<tspan class="value">{s["contrib"]}</tspan>}} | {pair("Stars", s["stars"], 14)}</tspan>')
    y += lh
    rows.append(f'<tspan x="{xr}" y="{y}"><tspan class="cc">. </tspan>'
                f'{pair("Commits", s["commits"], 34)} | {pair("Followers", s["followers"], 19)}</tspan>')

    height = max(y, y0 + lh * (len(ascii_rows) - 1)) + 20
    art = '\n'.join(f'<tspan x="{x0}" y="{y0 + i * lh}">{esc(r)}</tspan>' for i, r in enumerate(ascii_rows))
    t = theme
    return f'''<?xml version='1.0' encoding='UTF-8'?>
<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="985px" height="{height}px" font-size="16px">
<style>
@font-face {{
src: local('Consolas'), local('Consolas Bold');
font-family: 'ConsolasFallback';
font-display: swap;
-webkit-size-adjust: 109%;
size-adjust: 109%;
}}
.key {{fill: {t['key']};}}
.value {{fill: {t['value']};}}
.cc {{fill: {t['cc']};}}
text, tspan {{white-space: pre;}}
</style>
<rect width="985px" height="{height}px" fill="{t['bg']}" rx="15"/>
<text x="{x0}" y="{y0}" fill="{t['text']}" class="ascii">
{art}
</text>
<text x="{xr}" y="{y0}" fill="{t['text']}">
{chr(10).join(rows)}
</text>
</svg>
'''


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, 'ascii.txt'), encoding='utf-8') as f:
        ascii_rows = f.read().split('\n')
    stats = github_stats()
    print(stats)
    for name, theme in THEMES.items():
        with open(os.path.join(here, name), 'w', encoding='utf-8') as f:
            f.write(build(theme, ascii_rows, stats))
