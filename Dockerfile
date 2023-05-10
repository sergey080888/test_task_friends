FROM python:3.9.12-slim
WORKDIR /app/
COPY . .
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install -r requirements.txt
