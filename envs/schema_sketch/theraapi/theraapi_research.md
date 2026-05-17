# TheraApi Research Notes

## Data Source
- Official Site: https://theraapi.com/
- Developer Portal: Available on site
- API Base: https://api.theraapi.com/

## Authentication
- Type: API Key (Bearer Token)
- Get key: Free signup, key delivered in 30 seconds
- Sandbox environment available

## Core Endpoints
1. `GET /v1/therapists` - Search licensed therapists
2. `GET /v1/therapists/{id}` - Get detailed profile
3. `POST /v1/sessions` - Book therapy sessions
4. `GET /v1/sessions` - List sessions
5. `POST /v1/group-sessions` - Create/join group therapy
6. `GET /v1/wellness-reports` - Generate progress reports

## Key Features
- Therapist search with advanced filtering
- Video/audio/in-person session booking
- Group therapy session management
- Wellness progress analytics
- OAuth integration for authentication
- Real-time session management

## Therapist Data Includes
- Credentials and specialties
- Availability and timezone
- Languages spoken
- Insurance accepted
- Session rates
- Patient reviews

## Use Cases
- HR employee wellness platforms
- Mental health startup apps
- University counseling services
- Research platforms
- Therapy marketplace apps

## API Response Example
```json
{
  "therapists": [
    {
      "id": "dr_aisha_cbt",
      "name": "Dr. Aisha Rahman",
      "specialty": ["CBT", "Anxiety", "Trauma"],
      "languages": ["English", "Urdu"],
      "rating": 4.9,
      "experience_years": 12
    }
  ]
}
```

## Notes
- RESTful API design
- JSON responses
- Sandbox for testing
- Multi-tenant architecture
- HIPAA compliance considerations
