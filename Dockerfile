FROM python:3.11
WORKDIR /j4rvis
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8090
VOLUME /indexer/data
ENV PYTHONUNBUFFERED "1"
CMD ["python", "-u", "indexer"]