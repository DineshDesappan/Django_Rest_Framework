# IMDB CLONE REST API - PROJECT DOCUMENTATION

## 📚 Overview

This is a Django REST Framework project that implements a movie review platform similar to IMDB.

**Technology Stack:**

- Django REST Framework
- Python
- SQLite Database
- Token Authentication

---

## 🗂️ Project Structure

```
IMDB Clone/
├── Movie/                      # Main app
│   ├── models.py              # Database models (StreamPlatform, Movie, Review)
│   ├── serializers.py         # Data converters (Python ↔ JSON)
│   ├── views.py               # API endpoints and logic
│   ├── permissions.py         # Custom access control
│   ├── pagination.py          # Pagination settings
│   ├── throttling.py          # Rate limiting
│   └── urls.py                # URL routing
├── DRF/                        # Project settings
│   └── settings.py
├── db.sqlite3                  # Database file
└── manage.py                   # Django management
```

---

## 🗃️ Database Models

### 1. **StreamPlatform** (Netflix, Prime, etc.)

```python
Fields:
- name: Platform name
- about: Description
- website: URL

Relationships:
- Has many Movies (1 platform → many movies)
```

### 2. **Movie**

```python
Fields:
- title: Movie name
- storyline: Plot summary
- platform: Which platform (ForeignKey)
- active: Is available?
- avg_rating: Average rating (auto-calculated)
- number_rating: Review count (auto-calculated)

Relationships:
- Belongs to one StreamPlatform
- Has many Reviews (1 movie → many reviews)
```

### 3. **Review**

```python
Fields:
- review_user: Who wrote it (ForeignKey to User)
- rating: 1-5 stars
- description: Review text
- movie: Which movie (ForeignKey)
- active: Is approved?
- update: Last modified

Relationships:
- Belongs to one User
- Belongs to one Movie

Validation:
- Rating must be 1-5
- One user can only review a movie ONCE
```

---

## 🔗 API Endpoints

### **StreamPlatform API**

```
GET    /api/stream/         - List all platforms
POST   /api/stream/         - Create platform (admin only)
GET    /api/stream/<id>/    - Get platform + movies + reviews
PUT    /api/stream/<id>/    - Update platform (admin only)
DELETE /api/stream/<id>/    - Delete platform (admin only)
```

### **Movie API**

```
GET    /api/movie/          - List movies (paginated, 2 per page)
POST   /api/movie/          - Create movie
GET    /api/movie/<id>/     - Get movie + all reviews
PUT    /api/movie/<id>/     - Update movie
DELETE /api/movie/<id>/     - Delete movie

Features:
- Pagination (cursor-based)
- Filtering (?platform=1&active=true)
- Search (?search=<term>)
```

### **Review API**

```
GET    /api/movie/<id>/reviews/             - List reviews for movie
POST   /api/movie/<id>/review/create/       - Create review (auth required)
GET    /api/movie/<id>/review/<review_id>/  - Get specific review
PUT    /api/movie/<id>/review/<review_id>/  - Update review (owner only)
DELETE /api/movie/<id>/review/<review_id>/  - Delete review (owner only)

GET    /api/review?username=<username>      - Get user's reviews
```

---

## 🔐 Security & Permissions

### **1. IsAdminOrReadOnly**

- **Who:** StreamPlatform API
- **Rule:** Anyone can view, only admins can modify
- **Example:**
  - ✅ Anyone: GET /api/stream/
  - ❌ Regular user: POST /api/stream/
  - ✅ Admin: POST /api/stream/

### **2. IsReviewUserOrReadOnly**

- **Who:** Review API
- **Rule:** Anyone can view, only review owner/admin can modify
- **Example:**
  - ✅ Anyone: GET /api/movie/1/review/5/
  - ✅ Review author: PUT /api/movie/1/review/5/
  - ❌ Other users: PUT /api/movie/1/review/5/
  - ✅ Admin: PUT /api/movie/1/review/5/

### **3. Authentication Required**

- **Who:** ReviewCreate view
- **Rule:** Must be logged in to create review

---

## ⚙️ Key Features

### **1. Automatic Rating Calculation**

When a user creates a review:

```python
# First review: rating becomes average
if movie.number_rating == 0:
    movie.avg_rating = 5  # New rating
    movie.number_rating = 1

# Subsequent reviews: calculate new average
else:
    movie.avg_rating = (4.5 + 3) / 2 = 3.75
    movie.number_rating = 2
```

**Example:**

```
Movie: Inception (no reviews)
avg_rating = 0, number_rating = 0

User1 reviews with 5 stars:
  avg_rating = 5.0
  number_rating = 1

User2 reviews with 3 stars:
  avg_rating = (5.0 + 3) / 2 = 4.0
  number_rating = 2
```

### **2. One Review Per User**

Validation prevents duplicate reviews:

```python
# Check if user already reviewed this movie
if Review.objects.filter(movie=movie, review_user=user).exists():
    raise ValidationError("You have already reviewed this movie")
```

### **3. Nested Serialization**

API responses include related data:

```json
GET /api/stream/1/
{
  "id": 1,
  "name": "Netflix",
  "website": "netflix.com",
  "movies": [          ← Nested movies
    {
      "id": 1,
      "title": "Inception",
      "avg_rating": 4.5,
      "reviews": [     ← Double nested reviews
        {
          "id": 1,
          "review_user": "john_doe",
          "rating": 5,
          "description": "Amazing!"
        }
      ]
    }
  ]
}
```

### **4. Pagination**

Movies are paginated (2 per page):

```
GET /api/movie/
{
  "next": "http://api/movie/?cursor=xyz",
  "previous": null,
  "results": [...]  ← 2 movies
}
```

### **5. Throttling**

Rate limiting prevents API abuse:

- Anonymous users: Limited requests
- Authenticated users: Higher limit

---

## 🧩 How Components Work Together

### **Request Flow Example: Create a Review**

1. **User sends request:**

   ```
   POST /api/movie/1/review/create/
   Body: {"rating": 5, "description": "Amazing!"}
   Headers: Authorization: Token abc123
   ```

2. **Django REST Framework:**

   - Checks authentication (token valid?)
   - Routes to ReviewCreate view

3. **View (views.py):**

   - Validates user is authenticated (permission)
   - Calls `perform_create()`

4. **perform_create():**

   - Gets movie ID from URL
   - Checks if movie exists
   - Validates user hasn't reviewed before
   - Updates movie avg_rating
   - Increments number_rating

5. **Serializer (serializers.py):**

   - Validates data (rating 1-5?)
   - Auto-fills review_user from request
   - Saves to database

6. **Database:**

   - Creates new Review row
   - Updates Movie row (avg_rating, number_rating)

7. **Response:**
   ```json
   {
     "id": 10,
     "review_user": "john_doe",
     "rating": 5,
     "description": "Amazing!",
     "active": true,
     "update": "2025-01-06T12:00:00Z"
   }
   ```

---

## 📖 File-by-File Guide

### **models.py** - Database Structure

- Defines what data we store
- Sets up relationships between tables
- Validators for data integrity

### **serializers.py** - Data Transformation

- Converts Python objects → JSON (API responses)
- Converts JSON → Python objects (API requests)
- Handles nested data (movies with reviews)

### **views.py** - API Logic

- Defines what happens for each endpoint
- Business logic (rating calculation)
- Data filtering and pagination

### **permissions.py** - Access Control

- Who can view what?
- Who can modify what?
- Role-based restrictions

### **urls.py** - Routing

- Maps URLs to views
- Defines API endpoint structure
