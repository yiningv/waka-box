
import os
import base64
import math

from dotenv import load_dotenv
import requests
from github import Github, InputFileContent

load_dotenv(verbose=True)


WAKATIME_API_KEY = os.getenv('WAKATIME_API_KEY')
GH_TOKEN = os.getenv('GH_TOKEN')
GIST_ID = os.getenv('GIST_ID')
MARKDOWN_FILE = os.getenv('MARKDOWN_FILE')

FILE_NAME = '📊 每周工作报告'

MD_START = '<!-- waka-box start -->'
MD_END = '<!-- waka-box end -->'


github = Github(GH_TOKEN)


def main():
    stats = get_stats()
    stats_bar = '\n'.join(stats)
    if GIST_ID:
        update_gist(GIST_ID, '\n'.join(stats))
    if MARKDOWN_FILE:
        title = f'### <a href="https://gist.github.com/{GIST_ID}" target="_blank">{FILE_NAME}</a>' if GIST_ID else FILE_NAME
        update_markdown(title, stats_bar)

def get_stats():
    """获取wakatime上的每周工作报告"""
    url = 'https://wakatime.com/api/v1/users/current/stats/last_7_days'
    headers = {'Authorization': f'Basic {base64.b64encode(f"{WAKATIME_API_KEY}:".encode()).decode()}'}
    response = requests.get(url, headers=headers)
    stats = response.json()
    stats = stats.get('data', {}).get('languages', [])
    if len(stats) == 0:
        return [FILE_NAME]
    return generate_gist_lines(stats)


def generate_gist_lines(stats):
    max_lang_len = 11
    max_time_len = 14
    for stat in stats:
        stat['text'] = convert_duration(stat['text'])
        if len(stat['name']) > max_lang_len:
            max_lang_len = len(stat['name'])
        if len(stat['text']) > max_time_len:
            max_time_len = len(stat['text'])
    lines = []
    for index, stat in enumerate(stats):
        if index >= 5:
            break
        percent = stat['percent']
        lines.append(f'{stat["name"]:{max_lang_len}s}🕓{stat["text"]:{max_time_len}s}{generate_bar_chart(percent, 21)}{percent:5.1f}%')
    return lines
    
def generate_bar_chart(percent, size):
    syms = '░▏▎▍▌▋▊▉█'
    frac = int(math.floor((size * 8 * percent) / 100))
    bars_full = int(math.floor(frac / 8))
    
    if bars_full >= size:
        return syms[8:9] * size
    
    semi = frac % 8
    
    bar = syms[8:9] * bars_full + syms[semi:semi+1]
    return bar.ljust(size, syms[0:1])


def convert_duration(dur_str):
    return dur_str.replace("hr", "h").replace("min", "m").replace("sec", "x").replace(" ", "").replace("s", "").replace("x", "s")


def update_gist(gist_id, content):
    gist = github.get_gist(gist_id)
    gist.edit(files={FILE_NAME: InputFileContent(content)})
    
def update_markdown(title, content):
    md = ''
    try:
        with open(MARKDOWN_FILE, 'r', encoding='utf8') as f:
            md = f.read()
    except Exception as e:
        raise Exception(f'open {MARKDOWN_FILE} failed: {e}')
    before = md[:md.find(MD_START)]
    after = md[md.find(MD_END) + len(MD_END):]
    with open(MARKDOWN_FILE, 'w', encoding='utf8') as f:
        f.write(before)
        f.write('\n' + title + '\n')
        f.write('```text\n')
        f.write(content)
        f.write('\n')
        f.write('```\n')
        f.write(after)

main()