FROM python:3.13-slim

WORKDIR /app

# התקנת תלויות הריצה של ה-SUT
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pyjwt cryptography

# העתקת קוד האפליקציה בלבד
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
