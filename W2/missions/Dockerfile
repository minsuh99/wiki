FROM --platform=linux/amd64 quay.io/jupyter/scipy-notebook:latest

USER root

# Selenium용 헤드리스 Chromium + 워드클라우드 한글 폰트
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /home/jovyan/work

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# nltk stopwords 빌드 타임에 미리 받아두기
RUN python -m nltk.downloader stopwords

USER jovyan
COPY --chown=jovyan:users notebooks/ /home/jovyan/work/

EXPOSE 8888

CMD ["sh", "-c", "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --ServerApp.token= --ServerApp.password=''"]