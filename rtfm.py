from os import system as sys
from datetime import datetime
import json
sys('pip install lxml')

from pygicord import Paginator
from yaml import safe_load as yaml_load

import asyncio
import os
import re
import sys
import urllib.parse
from io import BytesIO
from hashlib import algorithms_available as algorithms

import aiohttp
import requests 

import textwrap
# from pytio import Tio, TioRequest
from bs4 import BeautifulSoup
from bs4.element import NavigableString

import hashlib 
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _ref, _doc
from _used import typing, get_raw, paste
from _tio import Tio

#class Coding(commands.Cog, name="RTFM Bot"):
#		"""To test code and check docs"""

#		def __init__(self, bot):
#				self.bot = bot
#				self.algos = sorted([h for h in hashlib.algorithms_available if h.islower()])
#				
#				self.bot.languages = ()
def get_content(self, tag):
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

async def run(response, language, code:str=''):
			"""Execute code in a given programming language"""
			# Powered by tio.run
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

			
			if ctx.message.attachments:
					# Code in file
					file = ctx.message.attachments[0]
					if file.size > 20000:
							return await response.message("File must be smaller than 20 kio.")
					buffer = BytesIO()
					await ctx.message.attachments[0].save(buffer)
					text = buffer.read().decode('utf-8')
			elif code.split(' ')[-1].startswith('link='):
					# Code in a webpage
					base_url = urllib.parse.quote_plus(code.split(' ')[-1][5:].strip('/'), safe=';/?:@&=$,><-[]')

					url = get_raw(base_url)

					async with aiohttp.ClientSession() as client_session:
							async with client_session.get(url) as response:
									if response.status == 404:
											return response.message('Nothing found. Check your link')
									elif response.status != 200:
											return response.message(f'An error occurred (status code: {response.status}). Retry later.')
									text = await response.text()
									if len(text) > 20000:
											return response.message('Code must be shorter than 20,000 characters.')
			elif code.strip('`'):
					# Code in message
					text = code.strip('`')
					firstLine = text.splitlines()[0]
					if re.fullmatch(r'( |[0-9A-z]*)\b', firstLine):
							text = text[len(firstLine)+1:]

			if text is None:
					# Ensures code isn't empty after removing options
					return

			# common identifiers, also used in highlight.js and thus discord codeblocks
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
				languages = f.read
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
			response.message(f'```ph\n{result}```')

		

async def reference(response, language, *, query: str):
			"""Returns element reference from given language"""

			lang = language.strip('`')

			if not lang.lower() in referred:
					return await response.message(f"{lang} not available. See `[p]list references` for available ones.")
			await referred[lang.lower()](ctx, query.strip('`'))

async def documentation(response, language, *, query: str):
			"""Returns element reference from given language"""

			lang = language.strip('`')

			if not lang.lower() in documented:
					return await response.message(f"{lang} not available. See `[p]list documentations` for available ones.")
			await documented[lang.lower()](ctx, query.strip('`'))
			

async def man(self, ctx, *, page: str):
			"""Returns the manual's page for a (mostly Debian) linux command"""

			base_url = f'https://man.cx/{page}'
			url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

			async with aiohttp.ClientSession() as client_session:
					async with client_session.get(url) as response:
							if response.status != 200:
									return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

							soup = BeautifulSoup(await response.text(), 'lxml')

							nameTag = soup.find('h2', string='NAME\n')

							if not nameTag:
									# No NAME, no page
									return await ctx.send(f'No manual entry for `{page}`. (Debian)')

							# Get the two (or less) first parts from the nav aside
							# The first one is NAME, we already have it in nameTag
							contents = soup.find_all('nav', limit=2)[1].find_all('li', limit=3)[1:]

							if contents[-1].string == 'COMMENTS':
									contents.remove(-1)

							title = self.get_content(nameTag)

							emb = discord.Embed(title=title, url=f'https://man.cx/{page}')
							emb.set_author(name='Debian Linux man pages')
							emb.set_thumbnail(url='https://www.debian.org/logos/openlogo-nd-100.png')

							for tag in contents:
									h2 = tuple(soup.find(attrs={'name': tuple(tag.children)[0].get('href')[1:]}).parents)[0]
									emb.add_field(name=tag.string, value=self.get_content(h2))

							await ctx.send(embed=emb)



async def list(self, ctx, *, group=None):
			"""Lists available choices for other commands"""

			choices = {
					"documentations": self.documented,
					"hashing": sorted([h for h in algorithms if h.islower()]),
					"references": self.referred,
					"wrapped argument": self.wrapping,
			}

			if group == 'languages':
					emb = discord.Embed(title=f"Available for {group}:",
							description='View them on [tio.run](https://tio.run/#), or in [JSON format](https://tio.run/languages.json)')
					return await ctx.send(embed=emb)

			if not group in choices:
					emb = discord.Embed(title="Available listed commands", description=f"`languages`, `{'`, `'.join(choices)}`")
					return await ctx.send(embed=emb)

			availables = choices[group]
			description=f"`{'`, `'.join([*availables])}`"
			emb = discord.Embed(title=f"Available for {group}: {len(availables)}", description=description)
			await ctx.send(embed=emb)
	

async def ascii(self, ctx, *, text: str):
			"""Returns number representation of characters in text"""

			emb = discord.Embed(title="Unicode convert", description=' '.join([str(ord(letter)) for letter in text]))
			emb.set_footer(text=f'Invoked by {str(ctx.message.author)}')
			await ctx.send(embed=emb)

async def unascii(self, ctx, *, text: str):
			"""Reforms string from char codes"""

			try:
					codes = [chr(int(i)) for i in text.split(' ')]
					emb = discord.Embed(title="Unicode convert",
							description=''.join(codes))
					emb.set_footer(text=f'Invoked by {str(ctx.message.author)}')
					await ctx.send(embed=emb)
			except ValueError:
					await ctx.send("Invalid sequence. Example usage : `[p]unascii 104 101 121`")
	

async def byteconvert(self, ctx, value: int, unit='Mio'):
			"""Shows byte conversions of given value"""

			units = ('o', 'Kio', 'Mio', 'Gio', 'Tio', 'Pio', 'Eio', 'Zio', 'Yio')
			unit = unit.capitalize()

			if not unit in units and unit != 'O':
					return await ctx.send(f"Available units are `{'`, `'.join(units)}`.")

			emb = discord.Embed(title="Binary conversions")
			index = units.index(unit)

			for i,u in enumerate(units):
					result = round(value / 2**((i-index)*10), 14)
					emb.add_field(name=u, value=result)

			await ctx.send(embed=emb)
	

async def _hash(self, ctx, algorithm, *, text: str):
			"""
			Hashes text with a given algorithm
			UTF-8, returns under hexadecimal form
			"""

			algo = algorithm.lower()

			if not algo in self.algos:
					matches = '\n'.join([supported for supported in self.algos if algo in supported][:10])
					message = f"`{algorithm}` not available."
					if matches:
							message += f" Did you mean:\n{matches}"
					return await ctx.send(message)

			try:
					# Guaranteed one
					hash_object = getattr(hashlib, algo)(text.encode('utf-8'))
			except AttributeError:
					# Available
					hash_object = hashlib.new(algo, text.encode('utf-8'))

			emb = discord.Embed(title=f"{algorithm} hash",
													description=hash_object.hexdigest())
			emb.set_footer(text=f'Invoked by {str(ctx.message.author)}')

			await ctx.send(embed=emb)


