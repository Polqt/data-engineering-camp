# Docker & PostgreSQL: Data Engineering Workshop

This repo contains code and materials from the Data Engineering Zoomcamp (Module 1 update).

## What you'll learn
- Docker basics & containerization
- Running PostgreSQL in Docker
- Data ingestion into PostgreSQL
- Using pgAdmin for DB management
- Docker networking & port mapping
- Docker Compose for multi-container apps
- Building a data ingestion pipeline
- SQL refresher with real data
- Best practices for containerized data workflows

## Prerequisites
- Basic Python knowledge
- Some SQL (helpful, not required)
- Docker & Python installed
- Git (optional)

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

## Quickstart
1. Clone this repo and open in Codespaces or locally.
2. See `docker-compose.yaml` for multi-container setup.
3. Use the provided scripts in `pipeline/` to ingest NYC taxi data into PostgreSQL.

---

Happy learning! 🐳📊
