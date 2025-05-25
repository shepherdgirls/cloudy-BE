FROM python:3.12-slim

WORKDIR /app

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# pip 최신화 및 의존성 설치
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 코드 복사
COPY . .

EXPOSE 8000

CMD ["python", "cloudy/manage.py", "runserver", "0.0.0.0:8000"]
