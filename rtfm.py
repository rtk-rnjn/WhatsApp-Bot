
from yaml import safe_load as yaml_load

import asyncio
import os
import re
import sys
import urllib.parse
from io import BytesIO
from hashlib import algorithms_available as algorithms

import aiohttp

# from pytio import Tio, TioRequest
from bs4 import BeautifulSoup
from bs4.element import NavigableString

import hashlib 
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _ref, _doc
from _used import get_raw, paste
from _tio import Tio

def get_content(tag):
	"""Returns content between two h2 tags"""

	bssiblings = tag.next_siblings
	siblings = []
	for elem in bssiblings:
			# get only tag elements, before the next h2
			# Putting away the comments, we know there's
			# at least one after it.
			if type(elem) == NavigableString:
					continue
			# It's a tag
			if elem.name == 'h2':
					break
			siblings.append(elem.text)
	content = '\n'.join(siblings)
	if len(content) >= 1024:
			content = content[:1021] + '...'

	return content

wrapping = {
		'c': '#include <stdio.h>\nint main() {code}',
		'cpp': '#include <iostream>\nint main() {code}',
		'cs': 'using System;class Program {static void Main(string[] args) {code}}',
		'java': 'public class Main {public static void main(String[] args) {code}}',
		'rust': 'fn main() {code}',
		'd': 'import std.stdio; void main(){code}',
		'kotlin': 'fun main(args: Array<String>) {code}'
	}

referred = {
		"csp-directives": _ref.csp_directives,
		"git": _ref.git_ref,
		"git-guides": _ref.git_tutorial_ref,
		"haskell": _ref.haskell_ref,
		"html5": _ref.html_ref,
		"http-headers": _ref.http_headers,
		"http-methods": _ref.http_methods,
		"http-status-codes": _ref.http_status,
		"sql": _ref.sql_ref
}

# TODO: lua, java, javascript, asm
documented = {
		'c': _doc.c_doc,
		'cpp': _doc.cpp_doc,
		'haskell': _doc.haskell_doc,
		'python': _doc.python_doc
}

async def run(response, arguments:str):
			"""Execute code in a given programming language"""
			# Powered by tio.run

			arguments = arguments.split(" ", 1)

			language = str(arguments[0])
			code = str(arguments[1])

			with open('default_langs.yml', 'r') as file: default = yaml_load(file)
			options = {
					'--stats': False,
					'--wrapped': False
			}

			lang = language.strip('`').lower()

			optionsAmount = len(options)

			# Setting options and removing them from the beginning of the command
			# options may be separated by any single whitespace, which we keep in the list
			code = re.split(r'(\s)', code, maxsplit=optionsAmount)
	
			for option in options:
					if option in code[:optionsAmount*2]:
							options[option] = True
							i = code.index(option)
							code.pop(i)
							code.pop(i) # remove following whitespace character

			code = ''.join(code)

			compilerFlags, commandLineOptions, args, inputs = [], [], [], []

			lines = code.split('\n')
			code = []
			for line in lines:
					if line.startswith('input '):
							inputs.append(' '.join(line.split(' ')[1:]).strip('`'))
					elif line.startswith('compiler-flags '):
							compilerFlags.extend(line[15:].strip('`').split(' '))
					elif line.startswith('command-line-options '):
							commandLineOptions.extend(line[21:].strip('`').split(' '))
					elif line.startswith('arguments '):
							args.extend(line[10:].strip('`').split(' '))
					else:
							code.append(line)

			inputs = '\n'.join(inputs)

			code = '\n'.join(code)

			text = None

			
			#if ctx.message.attachments:
			#		# Code in file
			#		file = ctx.message.attachments[0]
			#		if file.size > 20000:
			#				return await response.message("File must be smaller than 20 kio.")
			#		buffer = BytesIO()
			#		await ctx.message.attachments[0].save(buffer)
			#		text = buffer.read().decode('utf-8')
			if code.split(' ')[-1].startswith('link='):
					# Code in a webpage
					base_url = urllib.parse.quote_plus(code.split(' ')[-1][5:].strip('/'), safe=';/?:@&=$,><-[]')

					url = get_raw(base_url)

					async with aiohttp.ClientSession() as client_session:
							async with client_session.get(url) as res:
									if res.status == 404:
											return response.message('Nothing found. Check your link')
									elif res.status != 200:
											return response.message(f'An error occurred (status code: {res.status}). Retry later.')
									text = await res.text()
									if len(text) > 20000:
											return response.message('Code must be shorter than 20,000 characters.')
			elif code.strip('`'):
					# Code in message
					text = code.strip('`')
					firstLine = text.splitlines()[0]
					if re.fullmatch(r'( |[0-9A-z]*)\b', firstLine):
							text = text[len(firstLine)+1:]
			print(text)
			if text is None:
					# Ensures code isn't empty after removing options
					return


			quickmap = {
					'asm': 'assembly',
					'c#': 'cs',
					'c++': 'cpp',
					'csharp': 'cs',
					'f#': 'fs',
					'fsharp': 'fs',
					'js': 'javascript',
					'nimrod': 'nim',
					'py': 'python',
					'q#': 'qs',
					'rs': 'rust',
					'sh': 'bash',
			}

			if lang in quickmap:
					lang = quickmap[lang]

			if lang in default:
					lang = default[lang]
			
			with open('lang.txt') as f:
				languages = f.read()
				
			if not lang in languages:
					matches = '\n'.join([language for language in languages if lang in language][:10])
					
					message = f"`{lang}` not available."
					if matches:
							message = message + f" Did you mean:\n{matches}"

					return response.message(message)

			if options['--wrapped']:
					if not (any(map(lambda x: lang.split('-')[0] == x, wrapping))) or lang in ('cs-mono-shell', 'cs-csi'):
							return response.message(f'`{lang}` cannot be wrapped')

					for beginning in wrapping:
							if lang.split('-')[0] == beginning:
									text = wrapping[beginning].replace('code', text)
									break

			tio = Tio(lang, text, compilerFlags=compilerFlags, inputs=inputs, commandLineOptions=commandLineOptions, args=args)
			print(1)
			result = await tio.send()

			if not options['--stats']:
					try:
							start = result.rindex("Real time: ")
							end = result.rindex("%\nExit code: ")
							result = result[:start] + result[end+2:]
					except ValueError:
							# Too much output removes this markers
							pass

			if len(result) > 1991 or result.count('\n') > 40:

					link = await paste(result)

					if link is None:
							return response.message("Your output was too long, but I couldn't make an online bin out of it")
					return response.message(f'Output was too long (more than 2000 characters or 40 lines) so I put it here: {link}')

			zero = '\N{zero width space}'
			result = re.sub('```', f'{zero}`{zero}`{zero}`{zero}', result)

			# ph, as placeholder, prevents Discord from taking the first line
			# as a language identifier for markdown and remove it
			print(result)
			response.message(f'Output:\n```{result}```')

		

async def reference(response, language, query: str):
			"""Returns element reference from given language"""

			lang = language.strip('`')

			if not lang.lower() in referred:
					return response.message(f"{lang} not available. See `list references` for available ones.")
			await referred[lang.lower()](response, query.strip('`'))

async def documentation(response, language, query: str):
			"""Returns element reference from given language"""

			lang = language.strip('`')

			if not lang.lower() in documented:
					return response.message(f"{lang} not available. See `list documentations` for available ones.")
			await documented[lang.lower()](response, query.strip('`'))
			

async def man(response, page: str):
			"""Returns the manual's page for a (mostly Debian) linux command"""

			base_url = f'https://man.cx/{page}'
			url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

			async with aiohttp.ClientSession() as client_session:
					async with client_session.get(url) as res:
							if res.status != 200:
									return response.message(f'An error occurred (status code: {res.status}). Retry later.')

							soup = BeautifulSoup(await res.text(), 'lxml')

							nameTag = soup.find('h2', string='NAME\n')

							if not nameTag:
									# No NAME, no page
									return response.message(f'No manual entry for `{page}`. (Debian)')

							# Get the two (or less) first parts from the nav aside
							# The first one is NAME, we already have it in nameTag
							contents = soup.find_all('nav', limit=2)[1].find_all('li', limit=3)[1:]

							if contents[-1].string == 'COMMENTS':
									contents.remove(-1)

							title = get_content(nameTag)

							main = ''
							for tag in contents:
									h2 = tuple(soup.find(attrs={'name': tuple(tag.children)[0].get('href')[1:]}).parents)[0]
									main = main + f"{tag.string}\n```{get_content(h2)}```\n\n"

							response.message(f"*{title}*\n{url}\n\n{main}\n\nDebian Linux man pages")



async def list(response, group:str):
			"""Lists available choices for other commands"""

			choices = {
					"documentations": documented,
					"hashing": sorted([h for h in algorithms if h.islower()]),
					"references": referred,
					"wrapped argument": wrapping,
			}

			if group == 'languages':
					description='View them on (https://tio.run/#), or in (https://tio.run/languages.json)'
					return response.message(f"Available for {group}:\n\n```{description}```")

			if not group in choices:
					title="Available listed commands"
					description=f"`languages`, `{'`, `'.join(choices)}`"
					return response.message(f"{title}\n\n```{description}```")

			availables = choices[group]
			description=f"`{'`, `'.join([*availables])}`"
			title=f"Available for {group}: {len(availables)}"
			description=description
			return response.message(f"{title}\n\n```{description}```")
	

async def ascii(response, text: str):
			"""Returns number representation of characters in text"""
	
			response.message(f"Unicode Convert\n\n```{' '.join([str(ord(letter)) for letter in text])}```")

async def unascii(response, text: str):
			"""Reforms string from char codes"""

			try:
					codes = [chr(int(i)) for i in text.split(' ')]
					await response.message(f"Unicode Convert\n\n```{''.join(codes)}```")
			except ValueError:
					response.message("Invalid sequence. Example usage : `[p]unascii 104 101 121`")
	

async def byteconvert(response, value: int, unit='Mio'):
			"""Shows byte conversions of given value"""

			units = ('o', 'Kio', 'Mio', 'Gio', 'Tio', 'Pio', 'Eio', 'Zio', 'Yio')
			unit = unit.capitalize()

			if not unit in units and unit != 'O':
					return response.message(f"Available units are `{'`, `'.join(units)}`.")

			title = "Binary conversions"
			index = units.index(unit)

			main = ""
			for i,u in enumerate(units):
					result = round(value / 2**((i-index)*10), 14)
					main = main + "{} : {}\n".format(u, result)

			return response.message(f"Result:\n```\n{main}")
	

async def _hash(response, algorithm, text: str):
			"""
			Hashes text with a given algorithm
			UTF-8, returns under hexadecimal form
			"""

			algo = algorithm.lower()
			algos = sorted([h for h in hashlib.algorithms_available if h.islower()])
			if not algo in algos:
					matches = '\n'.join([supported for supported in algos if algo in supported][:10])
					message = f"`{algorithm}` not available."
					if matches:
							message += f" Did you mean:\n{matches}"
					return response.message(message)

			try:
					# Guaranteed one
					hash_object = getattr(hashlib, algo)(text.encode('utf-8'))
			except AttributeError:
					# Available
					hash_object = hashlib.new(algo, text.encode('utf-8'))

			
			response.message(f"{algorithm} hash\n\n```{hash_object.hexdigest()}```")


