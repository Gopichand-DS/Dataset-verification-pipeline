from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.discovery.health import SourceHealth, classify_http
from app.discovery.normalize_candidates import candidate_key, normalize_candidate
from app.discovery.public_page import PublicPageDiscovery, SourceBlockedError
from app.source_registry import discovery_sources, secondary_sources

@dataclass
class DiscoveryRun:
    module: str
    started_at: str
    candidates: list[dict]=field(default_factory=list)
    sources: list[dict]=field(default_factory=list)
    def to_dict(self):
        return {"module":self.module,"started_at":self.started_at,
                "candidate_count":len(self.candidates),"candidates":self.candidates,
                "sources":self.sources}

class DiscoveryEngine:
    def __init__(self,page_discovery=None): self.page_discovery=page_discovery or PublicPageDiscovery()
    def discover_module(self,module,include_secondary=True):
        run=DiscoveryRun(module,datetime.now(timezone.utc).isoformat())
        sources=list(discovery_sources(module))
        if include_secondary: sources.extend(secondary_sources(module))
        seen={}
        for source in sources:
            if source.get("type") not in {"discovery","official","publication"}: continue
            name,url=source.get("name",""),source.get("url","")
            if not url: continue
            try:
                raw=self.page_discovery.discover(url,source=source)
                http_status=raw[0].get("status_code") if raw else None
                status=classify_http(http_status) if http_status is not None else "ok"
                added=0
                for item in raw:
                    c=normalize_candidate(item,source)
                    if not c.get("name"): continue
                    k=candidate_key(c)
                    if k in seen:
                        seen[k]["discovery_sources"]=list(dict.fromkeys(
                            seen[k].get("discovery_sources",[])+c.get("discovery_sources",[])))
                    else: seen[k]=c; added+=1
                run.sources.append(SourceHealth(name,url,status,http_status,candidate_count=added).to_dict())
            except SourceBlockedError as exc:
                run.sources.append(SourceHealth(name,url,"blocked_or_rate_limited",error=str(exc)).to_dict())
            except Exception as exc:
                run.sources.append(SourceHealth(name,url,"error",error=str(exc)).to_dict())
        run.candidates=list(seen.values())
        return run
