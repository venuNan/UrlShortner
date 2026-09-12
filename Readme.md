# URL Shortener

A lightweight URL shortening REST API built with **Python, Flask, SQLite, Flask-SQLAlchemy, and Redis**.

The project is designed to explore backend concepts such as REST APIs, database persistence, caching, request handling, and containerization.

## Features

* Create a shortened URL from a long URL
* Store URL mappings in SQLite
* Use Redis as a caching layer for frequently accessed URLs
* Track the number of URL accesses
* Delete shortened URLs using a passkey
* RESTful API endpoints
* Docker support
* Simple and lightweight architecture

## Tech Stack

| Technology       | Purpose                |
| ---------------- | ---------------------- |
| Python 3.11      | Application runtime    |
| Flask            | REST API framework     |
| Flask-SQLAlchemy | Database ORM           |
| SQLite           | Persistent URL storage |
| Redis            | In-memory cache        |
| Docker           | Containerization       |

## Architecture

The application uses SQLite as the persistent data store and Redis as a cache.

```text
                 Client
                   |
                   | HTTP Request
                   v
             +-------------+
             |    Flask    |
             |   REST API  |
             +-------------+
                /       \
               /         \
              v           v
        +---------+   +---------+
        |  Redis  |   | SQLite  |
        |  Cache  |   |   DB    |
        +---------+   +---------+
```

### URL lookup flow

When a client requests a shortened URL:

```text
Client
  |
  v
Flask
  |
  v
Check Redis
  |
  +---- Cache HIT ----> Return URL
  |
  +---- Cache MISS
           |
           v
       Query SQLite
           |
           v
       Store result
       in Redis
           |
           v
       Return URL
```

Redis entries are cached with a **30-minute TTL**.

## How URL Generation Works

When a URL is submitted, the application generates a short identifier using Python's `hashlib.shake_128`:

```python
shortened_url = hashlib.shake_128(url.encode()).hexdigest(5)
```

The generated identifier is stored together with the original URL and passkey.

For example:

```text
Original URL:
https://www.example.com/some/very/long/path

Short ID:
a1b2c3d4e5

Short URL:
http://localhost:5000/url/a1b2c3d4e5
```

> **Note:** The current implementation derives the identifier directly from the URL. Therefore, this should not be considered a collision-proof or cryptographically secure short-code generation strategy for a large production system.

## API Endpoints

### 1. Create Short URL

**POST** `/shorten`

Creates a shortened URL.

#### Request

```json
{
    "url": "https://www.example.com",
    "passkey": "mypassword"
}
```

#### Successful Response

**HTTP 201**

```json
{
    "Message": "Successful",
    "URL_ID": "generated-id"
}
```

#### Missing Data

**HTTP 400**

```json
{
    "Error": "Missing required data"
}
```

---

### 2. Resolve Short URL

**GET** `/url/<short_url>`

Retrieves the original URL associated with a short URL.

Example:

```text
GET /url/a1b2c3d4e5
```

If the URL is found in Redis, it is served from the cache.

If it is not present in Redis, the application queries SQLite and then caches the result in Redis.

The application also increments the access counter when the URL is retrieved from the cache.

#### Successful Response

**HTTP 301**

```json
{
    "Message": "Successfull",
    "URL": "https://www.example.com"
}
```

#### URL Not Found

**HTTP 404**

```json
{
    "Error": "URL doesnt exist"
}
```

---

### 3. Delete Short URL

**DELETE** `/delete`

Deletes a shortened URL after validating the associated passkey.

#### Request

```json
{
    "short_url": "a1b2c3d4e5",
    "passkey": "mypassword"
}
```

If the URL exists and the passkey matches, the database record is deleted and the corresponding Redis cache entry is removed.

#### Successful Response

**HTTP 200**

```json
{
    "Message": "https://www.example.com deleted successfully"
}
```

## Database Model

The application contains a `URL` model with the following fields:

| Field     | Type         | Description                        |
| --------- | ------------ | ---------------------------------- |
| `url_id`  | String(10)   | Short URL identifier / primary key |
| `url`     | String(2048) | Original URL                       |
| `passkey` | String(2048) | Passkey used for deletion          |
| `count`   | Integer      | Number of accesses                 |

The `count` field defaults to `0`.

Conceptually:

```text
URL
+----------------+
| url_id (PK)    |
| url            |
| passkey        |
| count          |
+----------------+
```

## Redis Caching

Redis is used as a read cache in front of SQLite.

```text
GET /url/<short_url>
        |
        v
   Redis lookup
        |
   +----+----+
   |         |
  HIT      MISS
   |         |
   v         v
 Return    SQLite
 URL       lookup
             |
             v
        Redis SET
        TTL = 1800s
             |
             v
         Return URL
```

This reduces repeated database reads for URLs that are accessed frequently.

Redis is configured on:

```text
localhost:6379
```

and uses database `0`.

## Local Setup

### Prerequisites

Install:

* Python 3.11+
* Redis
* Git

### 1. Clone the repository

```bash
git clone https://github.com/venuNan/UrlShortner.git
cd UrlShortner
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project currently pins Flask 3.1.3, Flask-SQLAlchemy 3.1.1, Redis 8.1.0, SQLAlchemy 2.0.52 and related dependencies.

### 4. Start Redis

Make sure Redis is running on:

```text
localhost:6379
```

### 5. Start the application

```bash
python run.py
```

The Flask development server starts through `app.run(debug=True)`.

The API is available at:

```text
http://localhost:5000
```

## Docker

The repository includes a Dockerfile based on the Python 3.11 slim image. It installs the dependencies, copies the application, exposes port `5000`, and starts the application using `run.py`.

### Build the image

```bash
docker build -f DockerFile -t url-shortener .
```

### Run the container

```bash
docker run -p 5000:5000 url-shortener
```

> **Important:** The current application connects to Redis using `localhost:6379`. When running Flask inside Docker, `localhost` refers to the Flask container itself, not your host machine or a separate Redis container. For a multi-container Docker setup, Redis should be configured as a separate service and the application should connect to the Redis service name.

## Example Workflow

### Step 1 — Create a short URL

```bash
curl -X POST http://localhost:5000/shorten \
-H "Content-Type: application/json" \
-d "{\"url\":\"https://www.example.com\",\"passkey\":\"mypassword\"}"
```

Example response:

```json
{
    "Message": "Successful",
    "URL_ID": "abc123..."
}
```

### Step 2 — Retrieve the original URL

```bash
curl http://localhost:5000/url/abc123
```

The application first checks Redis.

If the URL is cached:

```text
Redis → Flask → Client
```

Otherwise:

```text
SQLite → Redis → Flask → Client
```

### Step 3 — Delete the URL

```bash
curl -X DELETE http://localhost:5000/delete \
-H "Content-Type: application/json" \
-d "{\"short_url\":\"abc123\",\"passkey\":\"mypassword\"}"
```

## Project Structure

```text
UrlShortner/
│
├── UrlShortner/
│   ├── __init__.py
│   ├── app.py
│   └── model.py
│
├── instance/
│
├── DockerFile
├── dockercompose.yml
├── gunicorn.conf.py
├── requirements.txt
├── .gitignore
├── test.py
└── Readme.md
```

### `app.py`

Contains the Flask application, API routes, Redis configuration, database configuration, URL shortening logic, caching logic, and deletion logic.

### `model.py`

Contains the SQLAlchemy database instance and `URL` model.

### `test.py`

For testing the server under concurrent requests to see the capcity of the backend api.

### `dockerfile`

Defines the container image and application startup command.

### `dockercompose.yml`

spins up multiple images like redis, application, mysql for production purposes.

## Design Considerations

### Why Redis?

URL resolution is a read-heavy operation. Frequently accessed short URLs do not need to query SQLite every time.

Caching the URL mapping in Redis allows repeated requests to be served from memory.

### Why SQLite?

SQLite provides a simple persistent database without requiring a separate database server. This makes the project easy to run locally while still demonstrating ORM-based database interaction.

### Cache Invalidation

When a URL is deleted:

```text
Delete from SQLite
       +
Delete from Redis
```

This prevents a deleted URL from remaining available through the cache.

## Limitations

This project is primarily a learning/backend engineering project and has several areas that would need improvement before being considered production-ready:

* Short IDs are generated deterministically from the original URL.
* Passkeys are currently stored directly in the database rather than hashed.
* Redis and database configuration are hard-coded.
* No authentication or authorization layer exists.
* No rate limiting is implemented.
* The application currently uses Flask's development server.
* The Redis configuration requires adjustment for Docker networking.
* URL access counting is not handled uniformly on cache misses and cache hits in the current implementation.
* There is no database migration system.
* There is no comprehensive automated test suite yet.

## Possible Future Improvements

* Use cryptographically random short IDs.
* Hash passkeys using a password-hashing algorithm.
* Move configuration to environment variables.
* Add authentication and authorization.
* Add request rate limiting.
* Add automated unit and integration tests.
* Use Gunicorn for production deployment.
* Add NGINX as a reverse proxy.
* Add Docker Compose for Flask + Redis.
* Add PostgreSQL/MySQL support for production deployments.
* Add monitoring and application metrics.
* Improve concurrency handling for URL access counters.
* Add expiration/TTL support for shortened URLs.
* Add API documentation using OpenAPI/Swagger.

## Learning Objectives

This project was built to understand practical backend engineering concepts including:

* REST API design
* Flask request/response lifecycle
* SQLAlchemy ORM
* Database persistence
* Redis caching
* Cache hit/miss behavior
* Cache invalidation
* HTTP status codes
* Docker containerization
* Separation between application storage and caching
* Backend performance considerations

## License

This project is available for learning and development purposes.

---

**Author:** Venu Dhagumati

**Repository:** [venuNan/UrlShortner](https://github.com/venuNan/UrlShortner)
