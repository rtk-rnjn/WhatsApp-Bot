import aiohttp


def get_raw(link):
    """Returns the url for raw version on a hastebin-like"""

    link = link.strip('<>/')  # Allow for no-embed links

    authorized = (
        'https://hastebin.com',
        'https://gist.github.com',
        'https://gist.githubusercontent.com'
    )

    if not any([link.startswith(url) for url in authorized]):
        return

    domain = link.split('/')[2]

    if domain == 'hastebin.com':
        if '/raw/' in link:
            return link
        token = link.split('/')[-1]
        if '.' in token:
            token = token[:token.rfind('.')]  # removes extension
        return f'https://hastebin.com/raw/{token}'
    else:
        # Github uses redirection so raw -> usercontent and no raw -> normal
        # We still need to ensure we get a raw version after this potential redirection
        if '/raw' in link:
            return link
        return link + '/raw'


async def paste(text):
    """Return an online bin of given text"""

    async with aiohttp.ClientSession() as aioclient:
        post = await aioclient.post('https://hastebin.com/documents', data=text)
        if post.status == 200:
            response = await post.text()
            return f'https://hastebin.com/{response[8:-2]}'

        # Rollback bin
        post = await aioclient.post("https://bin.readthedocs.fr/new", data={'code': text, 'lang': 'txt'})
        if post.status == 200:
            return post.url
