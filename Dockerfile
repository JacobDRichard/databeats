FROM python:3

# Create our app directory and work from there
ENV APP /app
RUN mkdir $APP
WORKDIR $APP

# Expose the port uWSGI will listen on
EXPOSE 5000

# Copy the requirements file over and install them
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install fluidsynth
RUN apt-get update && apt-get -y install fluidsynth

# Copy our code and directory structure into the container
COPY ./src .

# Run uWSGI with our ini
CMD [ "uwsgi", "--ini", "app.ini" ]