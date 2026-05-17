# DrugBank Research Notes

## Data Source
- Official Docs: https://go.drugbank.com/clinical
- API Portal: https://docs.drugbank.com/
- Main Site: https://go.drugbank.com/

## Authentication
- Type: API Key
- Location: Header or Query parameter
- Requires: Commercial license for Clinical API

## Core Endpoints
1. `GET /drugs` - Search drugs by name, brand, substance
2. `GET /drugs/{drugbank_id}` - Get detailed drug information
3. `POST /ddi` - Check drug-drug interactions
4. `GET /indications` - Find drugs by condition
5. `GET /products/{barcode}` - Lookup by UPC/EAN barcode
6. `GET /categories` - Browse therapeutic categories

## Key Features
- Evidence-based structured drug information
- Comprehensive drug interaction checker
- ATC code cross-mappings
- Adverse effects data
- Contraindications and blackbox warnings
- Allergy information with cross-sensitivity
- Global drug coverage

## Modules Available
- Base Module: Drug products, search, categories, descriptions
- Adverse Effects Module: Side effects and clinical trials
- Allergies Module: Cross-sensitivity data
- Contraindications Module: Pregnancy, age, disease interactions
- Drug Interactions Module: Severity ratings and management

## Notes
- Requires commercial license for production use
- REST API with JSON responses
- Extensive cross-mapping capabilities (MeSH, ATC, etc.)
- Updated regularly with latest medical research
