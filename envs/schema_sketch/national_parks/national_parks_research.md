# NationalParks Research Notes

## Data Source
- Official Docs: https://www.nps.gov/subjects/developer/get-started.htm
- API Reference: https://www.nps.gov/subjects/developer/api-documentation.htm
- MCP Server: https://github.com/KyrieTangSheng/mcp-server-nationalparks
- Base URL: `https://developer.nps.gov/api/v1`

## API Overview
- **Purpose**: Retrieve U.S. National Park Service park, alert, campground, event, and visitor center data.
- **Category**: Parks and recreation
- **Target users**: Travel planning, education, and recreation applications.

## Authentication
- **Type**: API key
- **How to obtain**: Register through the NPS developer portal.
- **Header/param format**: `api_key={NPS_API_KEY}` query parameter.

## Core Endpoints & Design
- **GET /parks**: Search parks by state, text, activities, pagination.
- **GET /parks?parkCode=...**: Retrieve detailed park data.
- **GET /alerts**: Search alerts by park code or text.
- **GET /campgrounds**: Retrieve campground data and amenities.
- **GET /visitorcenters**: Retrieve visitor center information.

## Data Models
- `Park`: parkCode, fullName, states, description, activities, entranceFees, operatingHours
- `Alert`: id, parkCode, title, category, description
- `Campground`: id, name, parkCode, amenities, fees, reservationUrl
- `VisitorCenter`: id, name, parkCode, operatingHours, contacts, addresses

## Use Cases
- Plan trips based on parks, alerts, and facilities.
- Ask for campground amenities at selected parks.
- Match parks by activities and state.

## Response Example
```json
{
  "total": 1,
  "data": [{"parkCode": "yose", "fullName": "Yosemite National Park", "states": "CA"}]
}
```

