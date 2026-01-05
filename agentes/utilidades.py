import re

def limpiar_url_markdown(url):
    """
    Limpia el formato markdown u otros caracteres de una cadena URL.
    """
    if not url:
        return url

    match = re.search(r'\(https?://[^\)]+\)', url)
    if match:
        return match.group(0).strip('()')

    url = url.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('\"', '').strip()
    url = url.split(' ')[0]
    return url.strip()
