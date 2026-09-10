from urllib.parse import urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup
from app.adapters.webpage import WebPageAdapter

class SourceBlockedError(RuntimeError): pass

class PublicPageDiscovery:
    def __init__(self, adapter=None): self.adapter=adapter or WebPageAdapter()
    def discover(self, url: str, source: dict|None=None):
        pages=self.adapter.discover(url)
        if not pages: return []
        page=pages[0]
        if page.get("access_status")=="blocked_or_rate_limited":
            raise SourceBlockedError(f"Source returned HTTP {page.get('status_code')}: {url}")
        source=source or {"name":getattr(self.adapter,"name","public-page"),"url":url}
        try:
            r=requests.get(url,timeout=getattr(self.adapter,"timeout",15),
                headers={"User-Agent":getattr(self.adapter,"user_agent","AIOrbit-Curator/6.1"),
                         "Accept":"text/html,application/xhtml+xml"},allow_redirects=True)
            if r.status_code>=400: return [page]
            soup=BeautifulSoup(r.text,"html.parser")
        except requests.RequestException:
            return [page]
        out=[]; seen=set()
        for a in soup.find_all("a",href=True):
            label=a.get_text(" ",strip=True); href=a.get("href","").strip()
            if not label or not href: continue
            absolute=urljoin(r.url,href); p=urlparse(absolute)
            if p.scheme not in {"http","https"}: continue
            clean=urlunparse((p.scheme,p.netloc,p.path,"","",""))
            if clean in seen: continue
            seen.add(clean)
            out.append({"name":label[:512],"official_url":clean,"description":"",
                        "discovery_type":"public_page_link","status_code":r.status_code})
        return out or [{"name":page.get("title",""),"official_url":page.get("canonical_url") or page.get("final_url") or url,
                        "description":page.get("description",""),"discovery_type":"public_page",
                        "status_code":page.get("status_code")}]
