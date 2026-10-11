import os
import re
import urllib.parse
import urllib.request
import requests
from bs4 import BeautifulSoup
from config import Config

# Junk email filter (framework assets, trackers, false positives)
IGNORED_EMAIL_DOMAINS = {
    "example.com", "yourdomain.com", "domain.com", "sentry.io", "w3.org",
    "github.com", "google.com", "facebook.com", "twitter.com", "apple.com",
    "schema.org", "wixpress.com", "cloudflare.com", "gravatar.com"
}
IGNORED_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".ico", ".woff", ".ttf"
)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")

class LeadScraper:
    """
    Automated company & email scraper using Agent Reach web scraping techniques
    (Jina Reader r.jina.ai, DuckDuckGo search, deep contact page crawling & AI entity extraction).
    """

    def __init__(self, gemini_api_key: str = None):
        self.api_key = gemini_api_key or Config.GEMINI_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7"
        })

    def read_page_with_jina(self, url: str) -> str:
        """
        Uses Agent Reach's primary web reader (Jina Reader r.jina.ai) to fetch clean Markdown.
        Falls back to direct requests + BeautifulSoup if Jina Reader is throttled.
        """
        clean_url = url.strip()
        if not clean_url.startswith("http"):
            clean_url = "https://" + clean_url

        jina_url = f"https://r.jina.ai/{clean_url}"
        try:
            req = urllib.request.Request(
                jina_url,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "text/plain"}
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw_bytes = resp.read(2 * 1024 * 1024)
                text = raw_bytes.decode("utf-8", errors="ignore")
                if "just a moment..." not in text.lower() and "requiring captcha" not in text.lower():
                    return text
        except Exception:
            pass

        # Fallback: direct HTML request
        try:
            r = self.session.get(clean_url, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style", "noscript", "svg"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)
        except Exception:
            pass

        return ""

    def search_leads(self, query: str, max_results: int = 15) -> list[dict]:
        """
        Searches the web using ddgs to find company URLs and snippets.
        """
        results = []
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for item in raw_results:
                    href = item.get("href", "")
                    if href and href.startswith("http"):
                        # Skip social media search engine pages directly
                        if not any(block in href for block in ["youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com"]):
                            results.append({
                                "title": item.get("title", ""),
                                "url": href,
                                "snippet": item.get("body", "")
                            })
        except Exception as e:
            # Silently fallback or log
            pass
        return results

    def extract_emails_from_text(self, text: str) -> list[str]:
        """Extracts and validates emails found in scraped text."""
        candidates = EMAIL_REGEX.findall(text)
        valid = []
        seen = set()

        for em in candidates:
            em_clean = em.lower().strip(".,:;!?'\"()[]{}")
            if any(em_clean.endswith(ext) for ext in IGNORED_EXTENSIONS):
                continue
            if "@" not in em_clean or "." not in em_clean.split("@")[-1]:
                continue
            domain = em_clean.split("@")[-1]
            if domain in IGNORED_EMAIL_DOMAINS:
                continue
            if em_clean not in seen and len(em_clean) >= 6:
                seen.add(em_clean)
                valid.append(em_clean)

        # Prioritize recruitment and contact emails
        def email_priority(e: str) -> int:
            if any(k in e for k in ["recrutement", "careers", "jobs", "rh", "talent"]):
                return 0
            if any(k in e for k in ["contact", "info", "hello", "bonjour"]):
                return 1
            return 2

        valid.sort(key=email_priority)
        return valid

    def extract_company_info(self, url: str, page_text: str, fallback_name: str, area: str, role: str) -> dict:
        """
        Uses Gemini AI or smart heuristics to structure company details.
        """
        # If Gemini API key is available, use AI to extract clean entity details
        if self.api_key and len(page_text) > 80:
            try:
                sample_text = page_text[:2500]
                prompt = f"""
Analyze this scraped webpage content from {url} and extract company info in JSON:
Page content excerpt:
\"\"\"
{sample_text}
\"\"\"

Area target: {area}
Desired role: {role}

Respond ONLY in raw JSON with:
{{
  "company_name": "Official clean company name",
  "contact_name": "Specific recruiter name or 'Équipe Recrutement' / 'Direction RH'",
  "company_notes": "1 concise sentence describing what this company does and their tech focus in {area}"
}}
"""
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 400, "responseMimeType": "application/json"}
                }
                r = requests.post(api_url, json=payload, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    raw = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    import json
                    parsed = json.loads(raw.strip().replace("```json", "").replace("```", ""))
                    return {
                        "company_name": parsed.get("company_name", fallback_name),
                        "contact_name": parsed.get("contact_name", "Équipe Recrutement"),
                        "company_notes": parsed.get("company_notes", f"Entreprise technologique et digitale basée à {area}")
                    }
            except Exception:
                pass

        # Heuristic fallback
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc.replace("www.", "")
        company_name = domain.split(".")[0].capitalize() if domain else fallback_name

        return {
            "company_name": company_name,
            "contact_name": "Équipe Recrutement",
            "company_notes": f"Entreprise spécialisée dans les services numériques et l'ingénierie logicielle ({area})"
        }

    def scrape_leads_for_area(
        self,
        area: str,
        industry: str,
        role: str = "Développeur Full Stack",
        max_leads: int = 10,
        progress_callback = None
    ) -> list[dict]:
        """
        End-to-End Discovery Pipeline:
        1. Formulates search queries targeting the specified area and industry.
        2. Discovers websites and directories.
        3. Scrapes content using Jina Reader & deep page crawls (/contact, /careers).
        4. Extracts verified recruitment/contact emails and generates notes.
        """
        discovered = []
        seen_domains = set()
        seen_emails = set()

        search_queries = [
            f'"{industry}" "{area}" contact email',
            f'startups "{industry}" "{area}" recrutement email',
            f'agences "{industry}" "{area}" contact'
        ]

        if progress_callback:
            progress_callback(f"Starting web search for '{industry}' in '{area}'...")

        # 1. Search candidate URLs
        candidate_sites = []
        for q in search_queries:
            results = self.search_leads(q, max_results=12)
            for res in results:
                url = res["url"]
                parsed = urllib.parse.urlparse(url)
                domain = parsed.netloc.replace("www.", "")
                if domain and domain not in seen_domains:
                    seen_domains.add(domain)
                    candidate_sites.append(res)
            if len(candidate_sites) >= max_leads * 3:
                break

        if progress_callback:
            progress_callback(f"Found {len(candidate_sites)} candidate websites. Scraping emails and company data...")

        # 2. Visit candidate sites and contact/career subpages
        for item in candidate_sites:
            if len(discovered) >= max_leads:
                break

            base_url = item["url"]
            fallback_title = item.get("title", "")
            if " - " in fallback_title:
                fallback_title = fallback_title.split(" - ")[0]

            if progress_callback:
                progress_callback(f"Scraping {base_url}...")

            # Fetch main page content
            page_text = self.read_page_with_jina(base_url)
            found_emails = self.extract_emails_from_text(page_text)

            # Check snippet if no emails on page directly
            if not found_emails and item.get("snippet"):
                found_emails = self.extract_emails_from_text(item["snippet"])

            # If still no email, probe /contact or /careers subpage
            if not found_emails:
                parsed_base = urllib.parse.urlparse(base_url)
                origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
                for subpath in ["/contact", "/contact-us", "/recrutement", "/careers"]:
                    sub_url = origin + subpath
                    sub_text = self.read_page_with_jina(sub_url)
                    sub_emails = self.extract_emails_from_text(sub_text)
                    if sub_emails:
                        found_emails = sub_emails
                        page_text += "\n" + sub_text
                        break

            # Filter valid unique emails
            target_email = None
            for em in found_emails:
                if em not in seen_emails:
                    seen_emails.add(em)
                    target_email = em
                    break

            if target_email:
                info = self.extract_company_info(base_url, page_text, fallback_title, area, role)
                record = {
                    "company_name": info["company_name"],
                    "email": target_email,
                    "contact_name": info["contact_name"],
                    "role": role,
                    "company_notes": info["company_notes"]
                }
                discovered.append(record)
                if progress_callback:
                    progress_callback(f" [+] Added: {record['company_name']} -> {record['email']}")

        return discovered
