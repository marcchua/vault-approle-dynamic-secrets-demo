import os
import hvac
import boto3
import psycopg2
import json
import socket
import time

#set the VAULT Authentication Context

vault_client    = hvac.Client()
vault_client    = hvac.Client(url=os.environ['VAULT_ADDR'])
dbhostname      = "mydb1-database.ch8jg7uay5or.us-east-2.rds.amazonaws.com"
mydb            = "postgres"
vault_role_id   = "1639f905-9ab5-5de0-9b2a-85ae206bf4b1"
print("***********************")
print("VAULT_ADDR   = " + os.environ['VAULT_ADDR'])
print("HOSTNAME     = " + socket.gethostname())
print("RDS HOSTNAME = " + dbhostname)
print("DATABASE     = " + mydb)


while True:
    print("***********************")
    try:
        vault_client.auth_approle(vault_role_id, os.environ['SECRET_ID'])

        if vault_client.is_authenticated():

            json_data=vault_client.read('database/creds/pythonapp-role')
            dbuser      = json_data['data']['username']
            dbpassword  = json_data['data']['password']
            lease_id    = json_data['lease_id']
            request_id  = json_data['request_id']

            print("ROLE_ID              = " + vault_role_id)        
            print("SECRET_ID            = " + os.environ['SECRET_ID'])
            print("Request_ID           = " + request_id)
            print("Lease ID             = " + lease_id)
            print("Database User        = " + dbuser)
            print("Database Password    = " + dbpassword)
            print("------------------------")
            for x in range (0, 3):
                conn = psycopg2.connect(host=dbhostname, database=mydb, user=dbuser, password=dbpassword) 
                cursor = conn.cursor()
                cursor.execute('SELECT version()')

                db_version = cursor.fetchone()
                print(db_version)
                cursor.close()
                time.sleep(4)

        else: 
            print("Unable to get Approle token for authentication")

        
    except psycopg2.OperationalError as poe:
        print("OperationalError - "+ str(poe))
        print(poe)

    except hvac.exceptions.InvalidRequest as hvac_ir:
        print("Invalid Authentication Request - " + str(hvac_ir))

    time.sleep(5)


