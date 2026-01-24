# Module 1: Docker & SQL

This repository contains my solution for **Module 1 – Docker & SQL**.

---

## Question 1: What's the version of pip in the python:3.13 image?

### Task
Run Docker with the `python:3.13` image, use `bash` as the entrypoint, and check the version of `pip`.

### Commands Used
```bash
docker image ls
docker run -it --entrypoint bash python:3.13
pip --version
```

### Answer
`pip 25.3`

### Screenshot
![Question 1 Screenshot](week01/docker-sql//screenshots/1.png)

---

## Question 2: Given the docker-compose.yaml, what is the hostname and port that pgadmin should use to connect to the postgres database?

### Task