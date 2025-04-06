# Logic Arcade API

A FastAPI server for the Logic Arcade application.

## Setup

1. Install dependencies:

Using Poetry:

```bash
poetry install
```

2. Configure your environment:

Edit the `.env` file with your desired settings:

```
API_MODE=dev  # Change to 'prod' for production mode
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=True
API_WORKERS=4  # Number of Gunicorn workers in production
```

3. Export the environment variables:

```bash
export $(grep -v '^#' .env | xargs)
```

## Running the server

### Development mode

Using Python directly:

```bash
python main.py
```

Using Poetry:

```bash
poetry run dev
```

By default, this will run in development mode using Uvicorn with hot-reloading enabled.

### Production mode

Using Python directly:

1. Set `API_MODE=prod` in your `.env` file, then run:

```bash
python main.py
```

2. Or override the setting temporarily:

```bash
API_MODE=prod python main.py
```

Using Poetry:

```bash
poetry run prod
```

This will start the server using Gunicorn with multiple workers.

## API Documentation

When the server is running, access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `GET /` - Welcome message
- `POST /pic-perfect/submit` - Submit an image with a prompt for evaluation
