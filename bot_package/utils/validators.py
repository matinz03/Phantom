import re

def extract_links_from_text(text: str) -> list:
    """
    استخراج لینک‌های VPN از متن
    پشتیبانی از پروتکل‌های:
    http, https, vmess, vless, trojan, ss, ssr, tuic, hysteria, hysteria2
    """
    url_pattern = re.compile(
        r'(?:https?://|vmess://|vless://|trojan://|ss://|ssr://|tuic://|hysteria://|hysteria2://)'
        r'[^\s<>"\'{}|\\^`]+',
        re.IGNORECASE
    )
    
    links = url_pattern.findall(text)
    # حذف کاراکترهای اضافی از انتها
    cleaned_links = []
    for link in links:
        link = link.rstrip('.,;:!?\'\"')
        # اطمینان از اینکه لینک کامل گرفته شده
        if len(link) > 10:
            cleaned_links.append(link)
    
    return cleaned_links