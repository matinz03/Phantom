import re


def extract_links_from_text(text: str) -> list:
    """Extract supported VPN subscription links from free-form text."""
    url_pattern = re.compile(
        r'(?:https?://|vmess://|vless://|trojan://|ss://|ssr://|tuic://|hysteria://|hysteria2://)'
        r'[^\s<>"\'{}|\\^`]+',
        re.IGNORECASE,
    )

    cleaned_links = []
    for link in url_pattern.findall(text):
        link = link.rstrip('.,;:!?\'"')
        if len(link) > 10:
            cleaned_links.append(link)

    return cleaned_links
