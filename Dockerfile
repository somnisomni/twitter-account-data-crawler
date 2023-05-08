# Use latest Python 3 stable version running on slim Debian bullseye
FROM python:3-slim-bullseye

# Workdir
WORKDIR /app

# Update packages
RUN apt -y update; apt -y upgrade

# Set timezone to KST
RUN apt install -y tzdata
RUN echo "Asia/Seoul" > /etc/timezone; \
    echo "Asia/Seoul" > /etc/localtime
ENV TZ=Asia/Seoul

# Install Chromium and Chromium WebDriver (provided by Debian)
RUN apt install -y --no-install-recommends chromium
RUN apt install -y --no-install-recommends chromium-driver
RUN printf "\n\n\n  Chromium WebDriver installed at `which chromedriver`  \n\n\n"

# Copy project files
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Entrypoint
ENTRYPOINT ["python", "index.py"]
