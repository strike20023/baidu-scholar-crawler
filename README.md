# baidu-scholar-crawler
Based on the Baidu Academic Literature Search using Selenium and the Selenium/Chrome container, a JSON file is generated through Github Actions using keyword indexing.

## run workflow
curl -X POST \                          
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/strike20023/baidu-scholar-crawler/dispatches \
  -d '{
    "event_type": "crawling_web",
    "client_payload": {
      "query": "dGVzdC1xdWVyeS0xMjM="
    }
  }'