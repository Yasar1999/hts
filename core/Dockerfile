# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
WORKDIR /usr/src/app

# Copy the requirements file into the container
COPY requirements/base.txt ./
RUN pip install --no-cache-dir -r base.txt

# Install gunicorn
RUN pip install gunicorn

# Copy the current directory contents into the container
COPY . .

# Copy the .env file
COPY .env /usr/src/app/.env

# Apply database migrations
RUN python manage.py migrate

RUN python manage.py collectstatic --noinput

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run gunicorn when the container launches
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
