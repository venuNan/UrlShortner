# URL Shortener

A lightweight URL shortening REST API built with **Flask, SQLAlchemy, SQLite, Redis, and Gunicorn**.

The main goal of this project is to explore efficient URL retrieval using **Redis caching** while maintaining persistent URL data in a relational database.

## Features

* Create shortened URLs
* Retrieve the original URL using a short URL ID
* Redis caching for frequently accessed URLs
* Store URL data using SQLAlchemy
* Delete shortened URLs using a passkey
* Track URL access count
* SQLite database for persistent storage
* Docker support
* Gunicorn support

## Tech Stack

* **Python 3.12**
* **Flask**
* **Flask-SQLAlchemy**
* **SQLite**
* **Redis**
* **SQLAlchemy**
* **Gunicorn**
* **Docker**

The project dependencies are pinned in `requirements.txt`.

## How It Works

The application stores the original URL and its generated short ID in SQLite.

For URL retrieval, Redis is used as a cache:

```text
Client
  |
  v
Flask API
  |
  v
Redis Cache
  |
  +---- Cache Hit ----> Return URL
  |
  +---- Cache Miss
           |
           v
        SQLite
           |
           v
       Store in Redis
           |
           v
        Return URL
```

Cached URLs have a **30-minute expiration time**.

## API Endpoints

### Create Short URL

```http
POST /shorten
```

Request:

```json
{
    "url": "https://example.com",
    "passkey": "mypassword"
}
```

Response:

```json
{
    "Message": "Successful",
    "URL_ID": "generated-id"
}
```

Returns `201 Created` when the URL is successfully stored.

If the generated short URL already exists, the API returns `409 Conflict`.

---

### Retrieve Original URL

```http
GET /url/<short_url>
```

Example:

```http
GET /url/abc123
```

The application first checks Redis. If the URL is not cached, it queries SQLite and places the result into Redis.

Successful response:

```json
{
    "Message": "Successfull",
    "URL": "https://example.com"
}
```

Returns `404` when the short URL does not exist.

---

### Delete Short URL

```http
DELETE /delete
```

Request:

```json
{
    "short_url": "abc123",
    "passkey": "mypassword"
}
```

The passkey is checked against the stored URL before deletion. The corresponding Redis cache entry is also removed when present.

## Database Model

The `URL` model contains:

| Field     | Type    | Description                          |
| --------- | ------- | ------------------------------------ |
| `url_id`  | String  | Primary key and short URL identifier |
| `url`     | String  | Original URL                         |
| `passkey` | String  | Passkey used for deletion            |
| `count`   | Integer | URL access count                     |

The model is defined using Flask-SQLAlchemy.

## Project Structure

```text
UrlShortner/
│
├── app/
│   ├── __init__.py
│   ├── app.py
│   └── model.py
│
├── instance/
│
├── DockerFile
├── requirements.txt
├── test.py
├── .gitignore
└── Readme.md
```

### File Description

* **`UrlShortner/__init__.py`** — Initializes the Flask application package.
* **`UrlShortner/app.py`** — Contains the Flask API endpoints, URL-shortening logic, Redis caching, and database operations.
* **`UrlShortner/model.py`** — Defines the SQLAlchemy database model.
* **`instance/`** — Contains application-specific local data such as the SQLite database.
* **`DockerFile`** — Defines the Docker image and starts the application using Gunicorn.
* **`requirements.txt`** — Contains the project's Python dependencies.
* **`test.py`** — Reserved for application tests.
* **`.gitignore`** — Specifies files that should not be tracked by Git.
* **`Readme.md`** — Project documentation.

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/venuNan/UrlShortner.git
cd UrlShortner
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Redis

Redis must be running on:

```text
localhost:6379
```

### 5. Start the application

Run the Flask application using your preferred WSGI entry point.

For the Docker deployment, Gunicorn starts:

```text
UrlShortner.app:app
```

as defined in the Dockerfile.

## Docker

Build the image:

```bash
docker build -f DockerFile -t url-shortener .
```

Run the container:

```bash
docker run -p 5000:5000 url-shortener
```

The Docker image uses Python 3.12-slim, installs the requirements, exposes port `5000`, and starts the application with Gunicorn.

## Redis Configuration

The application currently connects to Redis using:

```text
Host: localhost
Port: 6379
Database: 0
```

Redis is used as a temporary cache, while SQLite remains the persistent data store.

## Future Improvements

* Move configuration values to environment variables
* Add proper automated API tests
* Hash stored passkeys
* Improve short ID generation
* Add Docker Compose for Flask and Redis
* Add production monitoring and logging
* Improve concurrency handling for access counters
