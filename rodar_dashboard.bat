@echo off
docker run -p 8501:8501 --name esg-dashboard ^
  -v "%cd%\data:/app/data" ^
  esg-dashboard