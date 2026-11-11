import logging
import httpx
from bs4 import BeautifulSoup
import trafilatura
from typing import Optional, Dict, Any
from backend.app.core.security import is_safe_url, sanitize_untrusted_text
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

async def extract_article_content(url: str) -> Optional[Dict[str, Any]]:
    """
    Safely retrieves and extracts readable article text and metadata from a web page.
    Enforces SSRF prevention, request timeouts, and safe HTML sanitization.
    """
    # 1. SSRF Safety Check
    is_safe, reason = is_safe_url(url)
    if not is_safe:
        logger.warning(f"Skipping unsafe URL: {url} - {reason}")
        return None

    try:
        async with httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
        ) as client:
            resp = await client.get(url)
            
            # Verify final redirected URL is still safe
            final_safe, final_reason = is_safe_url(str(resp.url))
            if not final_safe:
                logger.warning(f"Redirected to unsafe URL: {resp.url} - {final_reason}")
                return None
                
            if resp.status_code != 200:
                logger.debug(f"HTTP status {resp.status_code} for {url}")
                return None
                
            html = resp.text
            if not html or len(html) < 200:
                return None

            # 2. Extract using Trafilatura (best-in-class main-text extractor)
            extracted_text = trafilatura.extract(
                html,
                include_comments=False,
                include_tables=True,
                no_fallback=False
            )
            
            metadata = trafilatura.extract_metadata(html)
            title = metadata.title if metadata and metadata.title else None
            date_published = metadata.date if metadata and metadata.date else None

            # 3. BeautifulSoup fallback if trafilatura extracted insufficient text
            if not extracted_text or len(extracted_text.strip()) < 100:
                soup = BeautifulSoup(html, "html.parser")
                
                # Remove dangerous and noisy tags
                for tag in soup(["script", "style", "noscript", "iframe", "svg", "nav", "footer", "header", "aside", "form"]):
                    tag.decompose()
                    
                if not title and soup.title:
                    title = soup.title.string.strip() if soup.title.string else None

                paragraphs = [p.get_text().strip() for p in soup.find_all(["p", "article"])]
                valid_paras = [p for p in paragraphs if len(p) > 40]
                extracted_text = "\n\n".join(valid_paras)

            if not extracted_text or len(extracted_text.strip()) < 80:
                return None

            # 4. Sanitize extracted text to prevent prompt injection & limit length
            clean_body = sanitize_untrusted_text(extracted_text, max_chars=12000)

            return {
                "url": url,
                "title": title or "Untitled Article",
                "content": clean_body,
                "publication_date": date_published,
                "raw_char_count": len(clean_body)
            }

    except httpx.TimeoutException:
        logger.debug(f"Timeout while extracting {url}")
        return None
    except Exception as e:
        logger.debug(f"Extraction failed for {url}: {e}")
        return None
