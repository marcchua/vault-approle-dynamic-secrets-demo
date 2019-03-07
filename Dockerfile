FROM python:3 

#ARG vault_addr
#ENV VAULT_ADDR "http://127.0.0.1:8200"

ADD vault_approle.py /

RUN pip install hvac psycopg2-binary boto3 psycopg2

CMD ["python", "./vault_approle.py"]

