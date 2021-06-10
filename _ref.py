import re
import urllib.parse
from functools import partial
# import sys

import aiohttp

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from markdownify import MarkdownConverter


# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _used


class DocMarkdownConverter(MarkdownConverter):
		# def convert_code(self, el, text):
		#     """Undo `markdownify`s underscore escaping."""
		#     print(el)
		#     print(el.strings)
		#     print(text)

		#     return f"`{text}`".replace('\\', '')

		def convert_pre(self, el, text):
				"""Wrap any codeblocks in `py` for syntax highlighting."""

				code = ''.join(el.strings)

				return f"```py\n{code}```"


def markdownify(html):
		return DocMarkdownConverter(bullets='•').convert(html)


async def _process_mozilla_doc(response, url):
		"""
		From a given url from developers.mozilla.org, processes format,
		returns tag formatted content
		"""

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as resp:
						if resp.status == 404:
								return await response.message(f'No results')
						if resp.status != 200:
								return await response.message(f'An error occurred (status code: {response.status}). Retry later.')

						body = BeautifulSoup(await response.text(), 'lxml').find('body')

		# if body.get('class')[0] == 'error':
		#     # 404
		#     return await ctx.send(f'No results for `{text}`')

		# First tag not empty
		contents = body.find(id='wikiArticle').find(lambda x: x.name == 'p' and x.text)
		result = markdownify(contents).replace('(/en-US/docs', '(https://developer.mozilla.org/en-US/docs')

		return result

async def html_ref(response, text):
		"""Displays informations on an HTML tag"""

		text = text.strip('<>`')

		base_url = f"https://developer.mozilla.org/en-US/docs/Web/HTML/Element/{text}"
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		output = await _process_mozilla_doc(response, url)
		if type(output) != str:
				# Error message already sent
				return

		response.message(f"*{text}\n```{output}```\n{url}*\n\nHTML5 Reference")

async def _http_ref(part, response, text):
		"""Displays informations about HTTP protocol"""

		base_url = f"https://developer.mozilla.org/en-US/docs/Web/HTTP/{part}/{text}"
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		output = await _process_mozilla_doc(response, url)
		if type(output) != str:
				# Error message already sent
				return

		response.message(f"*{text}\n```{output}```\n{url}*\n\nHTTP Protocol")

http_headers = partial(_http_ref, 'Headers')
http_methods = partial(_http_ref, 'Methods')
http_status = partial(_http_ref, 'Status')
csp_directives = partial(_http_ref, 'Headers/Content-Security-Policy')

async def _git_main_ref(part, response, text):
		"""Displays a git help page"""

		text = text.strip('`')

		if part and text == 'git':
				# just 'git'
				part = ''
		if not part and not text.startswith('git'):
				# gittutorial, giteveryday...
				part = 'git'
		base_url = f"https://git-scm.com/docs/{part}{text}"
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as res:
						if res.status != 200:
								return response.message(f'An error occurred (status code: {response.status}). Retry later.')
						if str(res.url) == 'https://git-scm.com/docs':
								# Website redirects to home page
								return response.message(f'No results')

						soup = BeautifulSoup(await res.text(), 'lxml')
						sectors = soup.find_all('div', {'class': 'sect1'}, limit=3)

						title = sectors[0].find('p').text

						list_ = []

						for tag in sectors[1:]:
								content = '\n'.join([markdownify(p) for p in tag.find_all(lambda x: x.name in ['p', 'pre'])])
								list_.append((tag.find('h2').text, content[:1024]))

						main = ''
						for i, j in list_:
							main = main + f"*{i}*\n```{j}```\n\n"
		
						response.message(f"*{title}*\n{url}\n{main}\n\nGit Reference")

git_ref = partial(_git_main_ref, 'git-')
git_tutorial_ref = partial(_git_main_ref, '')

async def sql_ref(response, text):
		"""Displays reference on an SQL statement"""

		text = text.strip('`').lower()
		if text in ('check', 'unique', 'not null'): text += ' constraint'
		text = re.sub(' ', '-', text)

		base_url = f"http://www.sqltutorial.org/sql-{text}/"
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as res:
						if res.status != 200:
								return response.message(f'An error occurred (status code: {res.status}). Retry later.')

						body = BeautifulSoup(await res.text(), 'lxml').find('body')
						intro = body.find(lambda x: x.name == 'h2' and 'Introduction to ' in x.string)
						title = body.find('h1').string

						ps = []
						for tag in tuple(intro.next_siblings):
								if tag.name == 'h2' and tag.text.startswith('SQL '): break
								if tag.name == 'p':
										ps.append(tag)

						description = '\n'.join([markdownify(p) for p in ps])[:2048]

						response.message(f"*{title}*\n```{description}```\n\n{url}\n\nSQL Reference")

async def haskell_ref(response, text):
		"""Displays informations on given Haskell topic"""

		text = text.strip('`')

		snake = '_'.join(text.split(' '))

		base_url = f"https://wiki.haskell.org/{snake}"
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as res:
						if res.status == 404:
								return await response.message(f'No results for `{text}`')
						if res.status != 200:
								return await response.message(f'An error occurred (status code: {res.status}). Retry later.')

						soup = BeautifulSoup(await res.text(), 'lxml').find('div', id='content')

						title = soup.find('h1', id='firstHeading').string
						description = '\n'.join([markdownify(p) for p in  soup.find_all(lambda x: x.name in ['p', 'li'] and tuple(x.parents)[1].name not in ('td', 'li'), limit=6)])[:2048]

						response.message(f"*{title}*\n```{description}```\n\n{url}\n\n")