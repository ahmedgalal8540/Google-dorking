# Google-dorking
This is a script to make google dorking more easy .
I’ve long skimmed articles about using Google dorking but never paid them much attention — the results always felt noisy and manual. I thought: why not automate the process so the script checks the results itself and exports them to a file?

The goal here is the idea rather than the implementation. My brother DeepSeek built a proof-of-concept script that produces good results, but it has a couple of practical caveats:

Requires Google Search JSON API and a Custom Search Engine. The script depends on Google’s JSON API and a created custom search engine to fetch results.

Rate / request limitation. In practice you can make roughly ~90 requests before you start getting errors; after that the script fails. Despite this limitation, the results it returns are real and usable.

This repo shares the concept and the PoC (script by DeepSeek) for demonstration and learning purposes — not as a finished tool. Use responsibly and follow Google’s terms of service.

(Script provided by : DeepSeek)
