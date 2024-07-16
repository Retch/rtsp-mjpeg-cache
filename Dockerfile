FROM python:3.12-slim

ENV RTSP_URL=rtsp://127.0.0.1
ENV MJPEG_FEED=mjpeg
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install Flask opencv-python
WORKDIR /app
COPY main.py /app/main.py
EXPOSE 5000
STOPSIGNAL SIGKILL
CMD ["python", "main.py"]
