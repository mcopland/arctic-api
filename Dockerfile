FROM python:3.7
RUN mkdir -p usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .
ENV PORT=8081
EXPOSE ${PORT}
CMD [ "python", "main.py" ]
