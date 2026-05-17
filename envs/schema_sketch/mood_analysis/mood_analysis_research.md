# Mood Analysis API Research Notes

## Data Source
- Provider: Zyla API Hub
- Documentation: https://zylalabs.com/api-marketplace/tools/mood+analysis+api/2912
- Endpoint: POST https://zylalabs.com/api/2912/mood+analysis+api/3038/get+analysis

## Authentication
- Type: Bearer Token (API Key)
- Header: `Authorization: Bearer YOUR_API_KEY`
- Free trial: 7 days, 25% of plan quota

## Core Endpoint
1. `POST /get_analysis` - Analyze text emotions

## Emotions Detected (7 categories)
1. Joy
2. Sadness
3. Anger
4. Fear
5. Disgust
6. Surprise
7. Neutral

## API Request Format
```bash
curl --location --request POST 'https://zylalabs.com/api/2912/mood+analysis+api/3038/get+analysis' \
--header 'Authorization: Bearer YOUR_API_KEY' \
--data-raw '{
    "text": "I like to go to the park."
}'
```

## API Response Example
```json
[
  {"label": "joy", "score": 0.964},
  {"label": "sadness", "score": 0.013},
  {"label": "disgust", "score": 0.012},
  {"label": "anger", "score": 0.005},
  {"label": "neutral", "score": 0.004},
  {"label": "fear", "score": 0.001},
  {"label": "surprise", "score": 0.001}
]
```

## Use Cases
- Social media sentiment analysis
- Customer feedback evaluation
- Brand monitoring
- Content optimization
- Crisis management
- Mental health journaling apps

## Pricing (USD)
- Basic: $24.99/month - 1,000 requests
- Pro: $49.99/month - 2,000 requests
- Pro Plus: $99.99/month - 4,000 requests
- Premium: $199.99/month - 10,000 requests
- Enterprise: $10,000/year - Custom volume

## Features
- Multi-language support
- Real-time analysis
- Only pay for successful requests (200 status)
- Postman integration
- Rate limit headers in responses

## Notes
- REST API with HTTPS
- JSON input/output
- Rate limited based on plan
- Part of Zyla API Hub ecosystem
- Suitable for text-based emotion analysis
