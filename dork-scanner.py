import requests
import time
import json
import argparse
import os
import sys
from urllib.parse import quote
import re

class GoogleDorkScanner:
    def __init__(self, domain, delay=2, api_key=None, search_engine_id=None):
        self.domain = domain
        self.delay = delay
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.results = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def load_dorks_from_file(self, file_path):
        """Load dorks from a text file"""
        dorks = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        dorks.append(line)
            return dorks
        except FileNotFoundError:
            print(f"Error: Dorks file '{file_path}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading dorks file: {e}")
            sys.exit(1)
    
    def default_dorks(self):
        """Default list of Google dorks"""
        return [
            'intitle:"index of"',
            'filetype:pdf',
            'inurl:admin',
            'intitle:"login"',
            'intitle:"error"',
            'intitle:"index of" "config"',
            'intitle:"index of" "backup"',
            'intitle:"index of" "database"',
            'intitle:"index of" "log"',
            'intitle:"index of" "wp-content"',
            'inurl:"/etc/passwd"',
            'filetype:sql'
        ]
    
    def get_dorks(self, dorks_file=None):
        """Get dorks from file or use default"""
        if dorks_file:
            return self.load_dorks_from_file(dorks_file)
        else:
            return self.default_dorks()
    
    def search_google(self, dork, max_results=10):
        """Search Google using either API or HTML parsing"""
        if self.api_key and self.search_engine_id:
            return self.search_google_api(dork, max_results)
        else:
            return self.search_google_html(dork, max_results)
    
    def search_google_html(self, dork, max_results=10):
        """Search Google using HTML parsing (fallback method)"""
        try:
            query = f'site:{self.domain} {dork}'
            encoded_query = quote(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={max_results}"
            
            response = self.session.get(url)
            response.raise_for_status()
            
            return self.parse_google_results(response.text)
            
        except requests.RequestException as e:
            print(f"Error searching for {dork}: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error for {dork}: {e}")
            return []
    
    def search_google_api(self, dork, max_results=10):
        """Use Google Custom Search API (recommended method)"""
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': f'site:{self.domain} {dork}',
                'num': min(max_results, 10)  # API limit per request
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            urls = []
            if 'items' in data:
                for item in data['items']:
                    urls.append(item['link'])
            
            print(f"API search: Found {len(urls)} results for '{dork}'")
            return urls
            
        except requests.RequestException as e:
            print(f"API Error for {dork}: {e}")
            if response.status_code == 403:
                print("API quota exceeded or invalid credentials")
            return []
        except Exception as e:
            print(f"Unexpected API error for {dork}: {e}")
            return []
    
    def parse_google_results(self, html):
        """Parse Google search results from HTML"""
        urls = []
        
        patterns = [
            r'<a href="(/url\?q=)([^&]+)',
            r'<a href="(http[^"]+)"[^>]*><h3',
            r'cite="([^"]+)"'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if isinstance(match, tuple):
                    url = match[1] if len(match) > 1 else match[0]
                else:
                    url = match
                
                if url.startswith('/url?q='):
                    url = url[7:].split('&')[0]
                
                try:
                    url = requests.utils.unquote(url)
                except:
                    pass
                
                if self.domain in url and url not in urls:
                    urls.append(url)
        
        return urls
    
    def scan_domain(self, dorks_file=None, max_results=10):
        """Execute all dorks against the domain"""
        method = "API" if self.api_key else "HTML"
        print(f"Starting Google dork scan for: {self.domain} (using {method} method)")
        print("=" * 60)
        
        dorks = self.get_dorks(dorks_file)
        
        print(f"Loaded {len(dorks)} dorks for scanning")
        
        for i, dork in enumerate(dorks, 1):
            print(f"Searching [{i}/{len(dorks)}]: {dork}")
            
            results = self.search_google(dork, max_results)
            self.results[dork] = {
                'count': len(results),
                'urls': results
            }
            
            print(f"Found {len(results)} results")
            
            if i < len(dorks):
                time.sleep(self.delay)
        
        return self.results
    
    def save_results(self, filename=None):
        """Save results to JSON file"""
        if not filename:
            filename = f"google_dork_results_{self.domain.replace('.', '_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {filename}")
        return filename
    
    def print_summary(self):
        """Print a summary of the findings"""
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        
        total_results = 0
        for dork, data in self.results.items():
            count = data['count']
            total_results += count
            print(f"{dork:50} : {count:3} results")
        
        print("=" * 60)
        print(f"TOTAL RESULTS: {total_results}")
        
        # Print interesting findings
        if total_results > 0:
            print("\nINTERESTING FINDINGS:")
            interesting_dorks = ['admin', 'login', 'config', 'backup', 'database', 'passwd', 'sql', 'password']
            for dork in interesting_dorks:
                found_any = False
                for search_dork, data in self.results.items():
                    if dork in search_dork.lower() and data['urls']:
                        if not found_any:
                            print(f"\n{dork.upper()} related findings:")
                            found_any = True
                        for url in data['urls']:
                            print(f"  - {url}")

def create_dorks_example_file():
    """Create an example dorks file if it doesn't exist"""
    example_dorks = """# Google Dorks List
# Add your dorks here, one per line
# Lines starting with # are comments

intitle:"index of"
filetype:pdf
inurl:admin
intitle:"login"
intitle:"error"
intitle:"index of" "config"
intitle:"index of" "backup"
intitle:"index of" "database"
intitle:"index of" "log"
intitle:"index of" "wp-content"
inurl:"/etc/passwd"
filetype:sql
filetype:env
inurl:".git"
intitle:"phpinfo"
filetype:log
inurl:wp-admin
filetype:xls
"""
    
    filename = "example_dorks.txt"
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(example_dorks)
        print(f"Created example dorks file: {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(description='Google Dork Scanner')
    parser.add_argument('domain', help='Target domain to scan (e.g., example.com)')
    parser.add_argument('-w', '--wordlist', help='File containing dorks to use (one per line)')
    parser.add_argument('-o', '--output', help='Output file name for results')
    parser.add_argument('--api-key', help='Google Custom Search API Key')
    parser.add_argument('--search-engine-id', help='Google Custom Search Engine ID')
    parser.add_argument('--delay', type=float, default=2, help='Delay between requests in seconds (default: 2)')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum results per dork (default: 10)')
    parser.add_argument('--create-example', action='store_true', help='Create an example dorks file and exit')
    
    args = parser.parse_args()
    
    if args.create_example:
        filename = create_dorks_example_file()
        print(f"Example dorks file created: {filename}")
        print("Edit this file and use it with: python script.py example.com -w example_dorks.txt")
        sys.exit(0)
    
    # Initialize scanner
    if args.api_key and args.search_engine_id:
        scanner = GoogleDorkScanner(
            domain=args.domain,
            delay=args.delay,
            api_key=args.api_key,
            search_engine_id=args.search_engine_id
        )
        print("Using Google Custom Search API")
    else:
        scanner = GoogleDorkScanner(args.domain, args.delay)
        print("Using HTML parsing method (less reliable)")
    
    # Perform scan
    results = scanner.scan_domain(
        dorks_file=args.wordlist,
        max_results=args.max_results
    )
    
    # Save results
    output_file = scanner.save_results(args.output)
    
    # Print summary
    scanner.print_summary()
    
    print(f"\nScan completed! Results saved to: {output_file}")

if __name__ == "__main__":
    main()