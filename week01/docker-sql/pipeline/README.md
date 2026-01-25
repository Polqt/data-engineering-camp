# Docker & PostgreSQL: Data Engineering Workshop

This repo contains code and materials from the Data Engineering Zoomcamp (Module 1 update).

---

## Preparing the environment
TODO describe how to connect to codespaces (use examples other workshops )

## Introduction to Docker
Docker is a containerization software that allows us to isolate software in a similar way to virtual machines but in a much leaner way.

A Docker image is a snapshot of a container that we can define to run our software, or in this case our data pipelines. By exporting our Docker images to Cloud providers such as Amazon Web Services or Google Cloud Platform we can run our containers there.

### Why Docker?

Docker provides the following advantages:

- Reproducibility: Same environment everywhere
- Isolation: Applications run independently
- Portability: Run anywhere Docker is installed

They are used in many situations:

- Integration tests: CI/CD pipelines
- Running pipelines on the cloud: AWS Batch, Kubernetes jobs
- Spark: Analytics engine for large-scale data processing
- Serverless: AWS Lambda, Google Functions

### Basic Docker Commands

Check Docker version:

```
docker --version
```

Run a simple container:

```
docker run hello-world
```

Run something more complex:

```
docker run ubuntu
```

Nothing happens. Need to run it in -it mode:

```
docker run -it ubuntu
```

We don't have python there so let's install it:

```
apt update && apt install python3
python3 -V
```

Important: Docker containers are stateless - any changes done inside a container will NOT be saved when the container is killed and started again.

When you exit the container and use it again, the changes are gone:

```
docker run -it ubuntu
python3 -V
```

This is good, because it doesn't affect your host system. Let's say you do something crazy like this:

```
docker run -it ubuntu
rm -rf / # don't run it on your computer! 
```

Next time we run it, all the files are back.

But, this is not completely correct. The state is saved somewhere. We can see stopped containers:

```
docker ps -a
```

We can restart one of them, but we won't do it, because it's not a good practice. They take space, so let's delete them:

```
docker rm `docker ps -aq`
```

Next time we run something, we add --rm:

```
docker run -it --rm ubuntu
```

There are other base images besides hello-world and ubuntu. For example, Python:

```
docker run -it --rm python:3.13.10
# add -slim to get a smaller version
```

This one starts python. If we want bash, we need to overwrite entrypoint:

```
docker run -it \
    --rm \
    --entrypoint=bash \
    python:3.13.11-slim
```

So, we know that with docker we can restore any container to its initial state in a reproducible manner. But what about data? A common way to do so is with volumes.

Let's create some data in test:

```
mkdir test
cd test
touch file1.txt file2.txt file3.txt
echo "Hello from host" > file1.txt
cd ..
```

Now let's create a simple script test/list_files.py that shows the files in the folder:

```python
from pathlib import Path

current_dir = Path.cwd()
current_file = Path(__file__).name

print(f"Files in {current_dir}:")

for filepath in current_dir.iterdir():
    if filepath.name == current_file:
        continue

    print(f"  - {filepath.name}")

    if filepath.is_file():
        content = filepath.read_text(encoding='utf-8')
        print(f"    Content: {content}")
```

Now let's map this to a Python container:

```
docker run -it \
    --rm \
    -v $(pwd)/test:/app/test \
    --entrypoint=bash \
    python:3.13.11-slim
```

Inside the container, run:

```
cd /app/test
ls -la
cat file1.txt
python list_files.py
```

You'll see the files from your host machine are accessible in the container!

## Virtual environment and Data Pipelines
A data pipeline is a service that receives data as input and outputs more data. For example, reading a CSV file, transforming the data somehow and storing it as a table in a PostgreSQL database.

In this workshop, we'll build pipelines that:

- Download CSV data from the web
- Transform and clean the data with pandas
- Load it into PostgreSQL for querying
- Process data in chunks to handle large files

Let's create an example pipeline. First, create a directory pipeline and inside, create a file pipeline.py:

```python
import sys
print("arguments", sys.argv)

day = int(sys.argv[1])
print(f"Running pipeline for day {day}")
```

Now let's add pandas:

```python
import pandas as pd

df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
print(df.head())

df.to_parquet(f"output_day_{sys.argv[1]}.parquet")
```

We need pandas, but we don't have it. We want to test it before we run things in a container.

We can install it with pip:

```
pip install pandas pyarrow
```

But this installs it globally on your system. This can cause conflicts if different projects need different versions of the same package.

Instead, we want to use a virtual environment - an isolated Python environment that keeps dependencies for this project separate from other projects and from your system Python.

We'll use uv - a modern, fast Python package and project manager written in Rust. It's much faster than pip and handles virtual environments automatically.

```
pip install uv
```

Now initialize a Python project with uv:

```
uv init --python=3.13
```

This creates a pyproject.toml file for managing dependencies and a .python-version file.

Compare the Python versions:

```
uv run which python  # Python in the virtual environment
uv run python -V

which python        # System Python
python -V
```

You'll see they're different - uv run uses the isolated environment.

Now let's add pandas:

```
uv add pandas pyarrow
```

This adds pandas to your pyproject.toml and installs it in the virtual environment.

Now we can execute this file:

```
uv run python pipeline.py 10
```

We will see:

['pipeline.py', '10']
job finished successfully for day = 10

This script produces a binary (parquet) file, so let's make sure we don't accidentally commit it to git by adding parquet extensions to .gitignore:

```
*.parquet
```

## Dockerizing the Pipeline
Now let's containerize the script. Create the following Dockerfile file:

```
# base Docker image that we will build on
FROM python:3.13.11-slim

# set up our image by installing prerequisites; pandas in this case
RUN pip install pandas pyarrow

# set up the working directory inside the container
WORKDIR /app
# copy the script to the container. 1st name is source file, 2nd is destination
COPY pipeline.py pipeline.py

# define what to do first when the container runs
# in this example, we will just run the script
ENTRYPOINT ["python", "pipeline.py"]
```

Explanation:

- FROM: Base image (Python 3.13)
- RUN: Execute commands during build
- WORKDIR: Set working directory
- COPY: Copy files into the image
- ENTRYPOINT: Default command to run

Let's build the image:

```
docker build -t test:pandas .
```

The image name will be test and its tag will be pandas. If the tag isn't specified it will default to latest.
We can now run the container and pass an argument to it, so that our pipeline will receive it:

```
docker run -it test:pandas some_number
```

You should get the same output you did when you ran the pipeline script by itself.

Note: these instructions assume that pipeline.py and Dockerfile are in the same directory. The Docker commands should also be run from the same directory as these files.

What about uv? Let's use it instead of using pip:

```
# Start with slim Python 3.13 image
FROM python:3.13.10-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./
# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Copy application code
COPY pipeline.py pipeline.py

# Set entry point
ENTRYPOINT ["python", "pipeline.py"]
```

## Running PostgreSQL with Docker
Now we want to do real data engineering. Let's use a Postgres database for that.

You can run a containerized version of Postgres that doesn't require any installation steps. You only need to provide a few environment variables to it as well as a volume for storing data.

Create a folder anywhere you'd like for Postgres to store data in. We will use the example folder ny_taxi_postgres_data. Here's how to run the container:

```
docker run -it --rm \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

Explanation of parameters:

- -e sets environment variables (user, password, database name)
- -v ny_taxi_postgres_data:/var/lib/postgresql creates a named volume
- Docker manages this volume automatically
- Data persists even after container is removed
- Volume is stored in Docker's internal storage
- -p 5432:5432 maps port 5432 from container to host
- postgres:18 uses PostgreSQL version 18 (latest as of Dec 2025)

Alternative approach - bind mount:

First create the directory, then map it:

```
mkdir ny_taxi_postgres_data

docker run -it \
  -e POSTGRES_USER="root" \
  -e POSTGRES_PASSWORD="root" \
  -e POSTGRES_DB="ny_taxi" \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql \
  -p 5432:5432 \
  postgres:18
```

When you create the directory first, it's owned by your user. If you let Docker create it, it will be owned by the Docker/root user, which can cause permission issues on Linux. On Windows and macOS with Docker Desktop, this is handled automatically.

Named volume vs Bind mount:

- Named volume (name:/path): Managed by Docker, easier
- Bind mount (/host/path:/container/path): Direct mapping to host filesystem, more control

Once the container is running, we can log into our database with pgcli.

Install pgcli:

```
uv add --dev pgcli
```

The --dev flag marks this as a development dependency (not needed in production). It will be added to the [dependency-groups] section of pyproject.toml instead of the main dependencies section.

Now use it to connect to Postgres:

```
uv run pgcli -h localhost -p 5432 -u root -d ny_taxi
```

uv run executes a command in the context of the virtual environment
- -h is the host. Since we're running locally we can use localhost.
- -p is the port.
- -u is the username.
- -d is the database name.

The password is not provided; it will be requested after running the command.
When prompted, enter the password: root

Try some SQL commands:

```
-- List tables
\dt

-- Create a test table
CREATE TABLE test (id INTEGER, name VARCHAR(50));

-- Insert data
INSERT INTO test VALUES (1, 'Hello Docker');

-- Query data
SELECT * FROM test;

-- Exit
\q
```

## Data Ingestion with Python
Let's build our first data ingestion pipeline. It will download NYC taxi data, process it and load it into our Postgres database.

### Downloading Data

Create a new file pipeline/download_data.py:

```python
import requests
import os

url = "https://example.com/nyc_taxi_data.csv"
output_dir = "data"

os.makedirs(output_dir, exist_ok=True)

response = requests.get(url)

with open(os.path.join(output_dir, "nyc_taxi_data.csv"), "wb") as f:
    f.write(response.content)

print("Data downloaded")
```

### Processing Data

Create a new file pipeline/process_data.py:

```python
import pandas as pd
from sqlalchemy import create_engine

# Database connection
engine = create_engine("postgresql://root:root@localhost:5432/ny_taxi")

# Read data from CSV
df = pd.read_csv("data/nyc_taxi_data.csv")

# Data cleaning and transformation
df["pickup_datetime"] = pd.to_datetime(df["pickup_datetime"])
df["dropoff_datetime"] = pd.to_datetime(df["dropoff_datetime"])

# Write data to PostgreSQL
df.to_sql("nyc_taxi_trips", engine, if_exists="replace", index=False)

print("Data processed and loaded into PostgreSQL")
```

### Running the Pipeline

Update your Dockerfile to include the new dependencies:

```
# Start with slim Python 3.13 image
FROM python:3.13.10-slim

# Copy uv binary from official uv image (multi-stage build pattern)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Set working directory
WORKDIR /app

# Add virtual environment to PATH so we can use installed packages
ENV PATH="/app/.venv/bin:$PATH"

# Copy dependency files first (better layer caching)
COPY "pyproject.toml" "uv.lock" ".python-version" ./
# Install dependencies from lock file (ensures reproducible builds)
RUN uv sync --locked

# Copy application code
COPY pipeline.py pipeline.py
COPY pipeline/download_data.py pipeline/download_data.py
COPY pipeline/process_data.py pipeline/process_data.py

# Set entry point
ENTRYPOINT ["python", "pipeline.py"]
```

Build the new image:

```
docker build -t ny_taxi_pipeline .
```

Run the data download:

```
docker run -it ny_taxi_pipeline python download_data.py
```

Run the data processing:

```
docker run -it ny_taxi_pipeline python process_data.py
```

## Orchestrating with Docker Compose
As our pipeline grows, we'll use Docker Compose to manage multi-container applications.

Create a docker-compose.yml file:

```yaml
version: "3.8"
services:
  postgres:
    image: postgres:18
    environment:
      POSTGRES_USER: root
      POSTGRES_PASSWORD: root
      POSTGRES_DB: ny_taxi
    volumes:
      - ny_taxi_postgres_data:/var/lib/postgresql
    ports:
      - "5432:5432"
  pipeline:
    image: ny_taxi_pipeline
    depends_on:
      - postgres
volumes:
  ny_taxi_postgres_data:
```

Start the services:

```
docker-compose up -d
```

Run the pipeline:

```
docker-compose run pipeline python process_data.py
```

Stop and remove the containers:

```
docker-compose down
```

---

Happy learning! 🐳📊
