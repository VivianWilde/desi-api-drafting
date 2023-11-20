FROM python

COPY dependencies.txt dependencies.txt

RUN pip3 install -r dependencies.txt

COPY . .

CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]
