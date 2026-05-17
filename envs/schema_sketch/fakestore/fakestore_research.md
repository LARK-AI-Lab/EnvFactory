# Fake Store API Research Notes

## Data Source
- Official Docs: https://fakestoreapi.com/docs
- GitHub: https://github.com/keikaavousi/fake-store-api
- Base URL: https://fakestoreapi.com/

## API Overview
- **Purpose**: A free fake API for testing and prototyping e-commerce applications with realistic product data
- **Category**: ecommerce
- **Target users**: Frontend developers, students, QA engineers needing mock data for e-commerce development

## Authentication
- **Type**: None (free public API) or JWT Token (for protected routes)
- **How to obtain**: Login endpoint returns JWT token
- **Header format**: `Authorization: Bearer {token}` (optional for protected routes)

## Core Endpoints & Design

### Products
- **Method & path**: `GET /products`
- **Purpose**: Get all products
- **Request params**: limit, sort (asc/desc)
- **Response structure**: Array of product objects

### Single Product
- **Method & path**: `GET /products/{id}`
- **Purpose**: Get specific product
- **Request params**: id (path)
- **Response structure**: Single product object

### Categories
- **Method & path**: `GET /products/categories`
- **Purpose**: Get all categories
- **Response structure**: Array of category strings

### Products by Category
- **Method & path**: `GET /products/category/{category}`
- **Purpose**: Filter products by category
- **Request params**: category (path)
- **Response structure**: Filtered products array

### Carts
- **Method & path**: `GET /carts`
- **Purpose**: Get all shopping carts
- **Request params**: limit, sort
- **Response structure**: Array of cart objects

### User Cart
- **Method & path**: `GET /carts/user/{userId}`
- **Purpose**: Get user's cart
- **Request params**: userId (path)
- **Response structure**: Cart object

### Authentication
- **Method & path**: `POST /auth/login`
- **Purpose**: Authenticate user
- **Request body**: {username, password}
- **Response structure**: {token}

## Data Models

### Product
- `id` (integer): Product ID (1-20)
- `title` (string): Product name
- `price` (float): Product price
- `description` (string): Product description
- `category` (string): Category name
- `image` (string): Image URL
- `rating` (object): {rate (float), count (integer)}

### Cart
- `id` (integer): Cart ID
- `userId` (integer): User ID
- `date` (string): ISO date string
- `products` (array): [{productId, quantity}]

### User
- `id` (integer): User ID
- `email` (string): Email address
- `username` (string): Username
- `password` (string): Password (hashed in real scenarios)
- `name` (object): {firstname, lastname}
- `address` (object): {city, street, number, zipcode, geolocation}
- `phone` (string): Phone number

## Use Cases
- Frontend development prototyping
- E-commerce UI/UX testing
- API integration learning
- Mobile app development
- Testing shopping cart functionality
- Mock data for demos

## Response Example
```json
{
  "id": 1,
  "title": "Fjallraven - Foldsack No. 1 Backpack, Fits 15 Laptops",
  "price": 109.95,
  "description": "Your perfect pack for everyday use and walks in the forest...",
  "category": "men's clothing",
  "image": "https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_.jpg",
  "rating": {
    "rate": 3.9,
    "count": 120
  }
}
```

## Additional Endpoints
- `POST /products` - Create product (returns mock)
- `PUT /products/{id}` - Update product (returns mock)
- `DELETE /products/{id}` - Delete product (returns mock)
- `POST /carts` - Create cart
- `PUT /carts/{id}` - Update cart
- `DELETE /carts/{id}` - Delete cart
- `GET /users` - Get all users
- `GET /users/{id}` - Get single user

## Notes
- Completely free, no API key required
- Data is static and resets on each request (mock data)
- Supports CORS for frontend development
- Perfect for testing without real transactions
- Not suitable for production use
