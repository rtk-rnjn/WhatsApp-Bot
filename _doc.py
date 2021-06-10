import urllib.parse
from functools import partial
from string import ascii_uppercase

import aiohttp

from bs4 import BeautifulSoup


async def python_doc(response, text: str):
		"""Filters python.org results based on your query"""

		text = text.strip('`')

		url = "https://docs.python.org/3/genindex-all.html"
		alphabet = '_' + ascii_uppercase

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as res:
						if res.status != 200:
								return response.message(f'An error occurred (status code: {response.status}). Retry later.')
						else: response.message("Just a second!")
						soup = BeautifulSoup(str(await res.text()), 'lxml')

						def soup_match(tag):
								return all(string in tag.text for string in text.strip().split()) and tag.name == 'li'

						elements = soup.find_all(soup_match, limit=10)
						links = [tag.select_one("li > a") for tag in elements]
						links = [link for link in links if link is not None]

						if not links:
								return response.message("No results")

						content = [f"{a.string}\nhttps://docs.python.org/3/{a.get('href')}\n" for a in links]

						value='\n'.join(content)

						response.message(f"Python3 Doc\n\nResult for *{text}*\n\n{value}")

async def _cppreference(language, response, text: str):
		"""Search something on cppreference"""

		text = text.strip('`')

		base_url = 'https://cppreference.com/w/cpp/index.php?title=Special:Search&search=' + text
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as res:
						if res.status != 200:
								return response.message(f'An error occurred (status code: {res.status}). Retry later.')
						else: response.message("Just a second!")
						soup = BeautifulSoup(await res.text(), 'lxml')

						uls = soup.find_all('ul', class_='mw-search-results')

						if not len(uls):
								return response.message('No results')

						if language == 'C':
								wanted = 'w/c/'
								url = 'https://wikiprogramming.org/wp-content/uploads/2015/05/c-logo-150x150.png'
						else:
								wanted = 'w/cpp/'
								url = 'https://isocpp.org/files/img/cpp_logo.png'

						for elem in uls:
								if wanted in elem.select_one("a").get('href'):
										links = elem.find_all('a', limit=10)
										break

						content = [f"[{a.string}](https://en.cppreference.com/{a.get('href')})" for a in links]
						
						value='\n'.join(content)

						response.message(f"{language} Doc\n\nResult for *{text}*\n\n```{value}```")

c_doc = partial(_cppreference, 'C')
cpp_doc = partial(_cppreference, 'C++')

async def haskell_doc(response, text: str):
		"""Search something on wiki.haskell.org"""

		text = text.strip('`')

		snake = '_'.join(text.split(' '))

		base_url = f"https://wiki.haskell.org/index.php?title=Special%3ASearch&profile=default&search={snake}&fulltext=Search"
		url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

		async with aiohttp.ClientSession() as client_session:
				async with client_session.get(url) as res:
						if res.status != 200:
								return response.message(f'An error occurred (status code: {res.status}). Retry later.')
						else: response.message("Just a second!")
						results = BeautifulSoup(await res.text(), 'lxml').find('div', class_='searchresults')

						if results.find('p', class_='mw-search-nonefound') or not results.find('span', id='Page_title_matches'):
								return response.message("No results")

						# Page_title_matches is first
						ul = results.find('ul', 'mw-search-results')

						content = []
						for li in ul.find_all('li', limit=10):
								a = li.find('div', class_='mw-search-result-heading').find('a')
								content.append(f"[{a.get('title')}](https://wiki.haskell.org{a.get('href')})")

						value='\n'.join(content)

						response.message(f"Haskell Doc\n\nResult for *{text}*\n\n```{value}```")