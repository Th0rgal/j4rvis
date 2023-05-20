FROM python:3.11
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /j4rvis
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8090
VOLUME /indexer/data
ENV PYTHONUNBUFFERED "1"
CMD ["python", "-u", "indexer"]
