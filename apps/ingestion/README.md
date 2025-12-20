# Federal Bills Explainer - Ingestion Module

This module fetches federal bills that became law from the Congress.gov API, generates plain-language explanations using local OSS models, and creates semantic embeddings for search.

## Features

- **Data Fetching**: Retrieves federal bills that became law from Congress.gov API
- **Explanation Generation**: Creates human-readable explanations using Google's Flan-T5 or other models
- **Embeddings**: Generates vector embeddings using sentence-transformers for semantic search
- **Database Storage**: Persists bills, explanations, and embeddings to PostgreSQL with pgvector
- **Batch Processing**: Handles ingestion in configurable batches with rate limiting
- **Dry Run Mode**: Preview what would be ingested without database writes

## Setup

### 1. Prerequisites

- Python 3.11 or higher (3.13 also works)
- Docker Desktop for PostgreSQL with pgvector extension
- Congress.gov API key (get from https://api.congress.gov/sign-up/)
- 4GB+ RAM for models (8GB+ recommended)
- Windows PowerShell or Linux/Mac terminal

### 2. Complete Installation

#### Windows PowerShell:
```powershell
# Navigate to ingestion directory
cd apps\ingestion

# Create virtual environment
py -3.11 -m venv .venv

# Set execution policy for PowerShell scripts
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip
pip install -U pip setuptools wheel

# Install core package (from ingestion directory)
pip install -e ..\..\packages\py-core

# Install ingestion package
pip install -e .

# Install ML dependencies
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers

# Install API requirements (for database migrations)
pip install -r ..\api\requirements.txt
```

#### Linux/Mac:
```bash
# Navigate to ingestion directory
cd apps/ingestion

# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install -U pip setuptools wheel

# Install core package
pip install -e ../../packages/py-core

# Install ingestion package
pip install -e .

# Install ML dependencies
pip install torch transformers sentence-transformers

# Install API requirements
pip install -r ../api/requirements.txt
```

### 3. Configuration

Copy the example environment file:
```powershell
cp apps\ingestion\.env.example apps\ingestion\.env
```

Edit `.env` and set:
- `INGEST_CONGRESS_API_KEY`: Your Congress.gov API key
- `INGEST_DATABASE_URL`: PostgreSQL connection string (e.g., `postgresql+psycopg2://postgres:postgres@localhost:5432/fbx`)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

### 4. Database Setup

#### Start Docker and Database:
```powershell
# Start Docker Desktop manually on Windows
# Then navigate to infra directory
cd ..\..\infra

# Start PostgreSQL container
docker compose up -d db

# Verify database is running
docker compose ps

# Check logs
docker compose logs db --tail 20
```

#### Run Database Migrations:
```powershell
# Set database URL environment variable
$env:DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/fbx"

# Navigate back to repository root
cd ..

# Run migrations
py -m alembic -c apps\api\alembic.ini upgrade head

# Verify tables were created
cd infra
docker compose exec db psql -U postgres -d fbx -c "\dt"
```

## Usage

### Dry Run (Preview Mode)

Test the ingestion without writing to database:

```powershell
python -m fbx_ingest.cli sync --dry-run --from-date 2024-01-01 --to-date 2024-12-31 --max-records 2
```

### Live Ingestion

Process and store bills in the database:

```powershell
python -m fbx_ingest.cli sync --no-dry-run --from-date 2024-06-01 --to-date 2024-06-30 --max-records 10
```

### Options

- `--dry-run/--no-dry-run`: Run without/with database persistence (default: dry-run)
- `--from-date`: Start date in ISO format (YYYY-MM-DD)
- `--to-date`: End date in ISO format (YYYY-MM-DD)
- `--max-records`: Maximum number of bills to process
- `--batch-size`: Number of bills to process in batch
- `--explain-model`: Model for generating explanations
- `--embed-model`: Model for generating embeddings
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--sample-bill`: Fetch specific bill (e.g., '118-hr-1234')

### Test Configuration

Test connectivity and configuration:

```powershell
python -m fbx_ingest.cli test
```

## Models

### Explanation Generation

Default model: `google/flan-t5-base`
- Lightweight T5 model for text generation
- ~250MB download
- Works well on CPU

Alternative: `microsoft/phi-3-mini-4k-instruct`
- More powerful but larger
- Requires more memory

### Embedding Generation

Default model: `sentence-transformers/all-MiniLM-L6-v2`
- 384-dimensional embeddings
- ~90MB download
- Fast and efficient

## Performance Tips

### CPU Usage
- Models run on CPU by default
- Processing speed: ~1-2 bills per minute
- Sufficient for daily ingestion

### GPU Usage
- Set `INGEST_USE_GPU=true` in `.env`
- Requires CUDA-compatible GPU
- 5-10x faster processing

### Model Caching
Models are downloaded and cached on first use:
- Windows: `%USERPROFILE%\.cache\huggingface`
- Linux/Mac: `~/.cache/huggingface`

To pre-download models:
```python
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# Download explanation model
pipeline("text2text-generation", model="google/flan-t5-base")

# Download embedding model
SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

## Troubleshooting

### Common Installation Issues

**Missing Python Packages:**
```powershell
# If you get ModuleNotFoundError for torch, transformers, or sentence-transformers:
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install transformers sentence-transformers
```

**Pydantic Configuration Error:**
If you see "Extra fields not permitted" error, ensure the settings file uses `model_config` instead of `Config` class:
```python
# Correct format in settings.py:
model_config = ConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore"
)
```

**Import Errors for fbx_core:**
Ensure `__init__.py` files exist in:
- `packages/py-core/fbx_core/db/`
- `packages/py-core/fbx_core/models/`

Install packages in editable mode:
```powershell
pip install -e ..\..\packages\py-core
pip install -e .
```

### Windows Issues

**PowerShell Execution Policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Or for current session only:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Long Path Support:**
Enable if you encounter path length errors:
```powershell
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**Docker Not Running:**
```powershell
# Check Docker status
docker ps

# If error, start Docker Desktop manually via Windows Start Menu
# Wait for Docker to fully start (system tray icon turns green)
# Then retry container commands
```

### Database Connection

**pgvector Extension:**
Ensure pgvector is installed:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Connection Issues:**
- Check PostgreSQL is running
- Verify connection string format
- Ensure database exists

### API Rate Limiting

The Congress.gov API has rate limits:
- Default delay: 0.5 seconds between requests
- Adjust `INGEST_API_DELAY_SECONDS` if needed
- Use smaller date ranges for initial testing

### Memory Issues

If you encounter out-of-memory errors:
- Reduce `INGEST_BATCH_SIZE`
- Use smaller models
- Close other applications
- Consider using a cloud instance

## Database Schema

The ingestion creates three main tables:

### bills
- `external_id`: Unique identifier (e.g., "118-hr-1234")
- `title`: Full bill title
- `summary`: Bill summary text
- `law_number`: Public law number if enacted

### explanations
- `bill_id`: Foreign key to bills
- `explanation_text`: Generated explanation
- `model_name`: Model used for generation
- `word_count`: Length of explanation

### embeddings
- `entity_type`: Type of embedded content
- `entity_id`: ID of the entity
- `vector`: 384-dimensional embedding vector
- `model_name`: Model used for embedding

## Examples

### Initial Data Load

Start with a small batch to verify everything works:
```powershell
# Test with a known enacted bill
python -m fbx_ingest.cli sync --dry-run --sample-bill 117-hr-3076

# If successful, run without dry-run
python -m fbx_ingest.cli sync --no-dry-run --sample-bill 117-hr-3076

# Ingest recent bills (adjust dates as needed)
python -m fbx_ingest.cli sync --no-dry-run --from-date 2023-01-01 --to-date 2024-12-31 --max-records 50
```

### Daily Ingestion

Fetch bills from the last 24 hours:
```powershell
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-dd")
$today = (Get-Date).ToString("yyyy-MM-dd")
python -m fbx_ingest.cli sync --no-dry-run --from-date $yesterday --to-date $today
```

### Batch Processing Strategy

For large historical data loads:
```powershell
# Process by year to avoid timeouts
$years = @(2023, 2024)
foreach ($year in $years) {
    $start = "$year-01-01"
    $end = "$year-12-31"
    Write-Host "Processing year $year..."
    python -m fbx_ingest.cli sync --no-dry-run --from-date $start --to-date $end --max-records 100
    Start-Sleep -Seconds 5  # Brief pause between batches
}
```

## Best Practices

### Production Deployment

1. **Use Environment Variables:**
   ```powershell
   # Set persistent environment variables
   setx CONGRESS_API_KEY "your_key_here"
   setx DATABASE_URL "postgresql+psycopg2://user:pass@host:5432/db"
   ```

2. **Schedule Regular Ingestion:**
   - Use Windows Task Scheduler or cron for daily runs
   - Run during off-peak hours (e.g., 2 AM)
   - Include error notifications

3. **Monitor and Log:**
   ```powershell
   # Run with detailed logging
   python -m fbx_ingest.cli sync --no-dry-run --log-level DEBUG 2>&1 | Tee-Object -FilePath "ingestion_$(Get-Date -Format 'yyyyMMdd').log"
   ```

4. **Database Maintenance:**
   ```sql
   -- Regular VACUUM for performance
   VACUUM ANALYZE bills, explanations, embeddings;
   
   -- Monitor table sizes
   SELECT 
     schemaname,
     tablename,
     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables 
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

### Performance Optimization

1. **Batch Size:** Start with 10, increase if stable
2. **Rate Limiting:** Respect API limits (1000/hour)
3. **Model Selection:** Use smaller models for faster processing
4. **GPU Acceleration:** Enable if available for 5-10x speedup

### Historical Backfill

Process all 2024 bills:
```powershell
python -m fbx_ingest.cli sync --no-dry-run --from-date 2024-01-01 --to-date 2024-12-31 --max-records 500
```

### Test Specific Bill

```powershell
python -m fbx_ingest.cli sync --dry-run --sample-bill "118-hr-2882"
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs in the console output
3. Ensure all dependencies are installed correctly
4. Verify API keys and database credentials
