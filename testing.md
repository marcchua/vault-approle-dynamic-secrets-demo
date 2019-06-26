# Testing 

0. (Optional) Build docker container
```
export docker_user="<your-username>"
docker build -t "${docker_user}/pyapprole:0.0.1" .
docker images
```

1. (Optional) Start postgres server and install client. The following example commands use a local `postgres` Docker container. If you are using RDS, please adjust database endpoints in steps 2 and 4.
```
export psql_user="postgres"
export psql_pass="bigdata"
export psql_host="localhost"

# On an EC2 instance run: export psql_host="$(curl -s http://169.254.169.254/latest/meta-data/local-ipv4)"

docker run -e POSTGRES_USER=${psql_user} -e POSTGRES_PASSWORD=${psql_pass} -d -p 5432:5432 postgres:9.6
docker ps

# Install psql client and test login
sudo apt-get install postgresql-client -y
psql -h ${psql_host} -U ${psql_user} postgres
```

2. Enable dynamic secrets. Adjust `psql_host`, `psql_user`, and `psql_pass` here if needed.
```
export VAULT_TOKEN="<admin-token>"
export VAULT_ADDR="https://<vault-ip>:8200"
vault token lookup
vault secrets enable database

# Configure auth method:
vault write database/config/postgresql plugin_name=postgresql-database-plugin allowed_roles="*" connection_url="postgresql://{{username}}:{{password}}@${psql_host}:${psql_port}/postgres?sslmode=disable" username="${psql_user}" password="${psql_pass}"

# Create a dba role and test dynamic credentials::
tee all.sql <<EOF
CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
GRANT ALL ON ALL TABLES IN SCHEMA public TO "{{name}}";
EOF

vault write database/roles/dba db_name=postgresql creation_statements=@all.sql \
    default_ttl=5m max_ttl=1h

vault read database/roles/dba
vault read database/creds/dba

# Create application role and test dynamic credentials:
tee readonly.sql <<EOF
CREATE ROLE "{{name}}" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO "{{name}}";
EOF

vault write database/roles/pythonapp-role db_name=postgresql creation_statements=@readonly.sql \
    default_ttl=5m max_ttl=1h

vault read database/roles/pythonapp-role
vault read database/creds/pythonapp-role
```

3. Vault AppRole configuration
```
vault policy write pyapp vault-policy.hcl
vault auth enable approle
vault write auth/approle/role/my-role \
    secret_id_ttl=10m \
    token_num_uses=10 \
    token_ttl=20m \
    token_max_ttl=30m \
    secret_id_num_uses=40 \
    policies="pyapp"

vault read -format=json auth/approle/role/my-role/role-id > role.json
vault write -format=json -f auth/approle/role/my-role/secret-id > secretid.json
```

4. Deploy app and check logs
Note: if you are running Vault locally, you may need to add the `--network host` parameter for the `docker run` command.
```
export ROLE_ID="$(cat role.json | jq -r .data.role_id )"
export SECRET_ID="$(cat secretid.json | jq -r .data.secret_id )"
docker run --name pyapprole \
    -e VAULT_ADDR="${VAULT_ADDR}" \
    -e DB_HOST="${psql_host}" \
    -e ROLE_ID="${ROLE_ID}" \
    -e SECRET_ID="${SECRET_ID}" \
    -e SECRETS_PATH="database/creds/pythonapp-role" \
    -d kawsark/pyapprole:0.0.1

docker logs -f pyapprole

# Expected output is a successful set of Database credentials: Note: never print out passwords from an App, this is for a demo only.
***********************
Starting loop
secret id is:7d1cad08-4b59-413b-5451-f453c8b9f1dd
ROLE_ID              = ddb43a35-f976-be4d-d6d8-93e2b56bf21d
SECRET_ID            = 7d1cad08-4b59-413b-5451-f453c8b9f1dd
Request_ID           = dbe45a18-26fa-4114-e91c-c5838ad95651
Lease ID             = database/creds/pythonapp-role/q2Kx4h0a72UoguAFMFnSdrW3
Database User        = v-approle-pythonap-IRKRvykvPTHlLp2Z8X7H-1561498389
Database Password    = A1a-YefpLKxpI1EqvcrR
------------------------
('PostgreSQL 9.6.14 on x86_64-pc-linux-gnu (Debian 9.6.14-1.pgdg90+1), compiled by gcc (Debian 6.3.0-18+deb9u1) 6.3.0 20170516, 64-bit',)
```

5. Deploy app with DBA role and check logs
```
docker run -name "pyapprole1" \
           -e VAULT_ADDR="${VAULT_ADDR}" \
           -e DB_HOST="${psql_host}" \
           -e ROLE_ID="${ROLE_ID}" \
           -e SECRET_ID="${SECRET_ID}" \
           -e SECRETS_PATH="database/creds/dba" 
           -d kawsark/pyapprole:0.0.1

# Expected output is a permission denied error:
hvac.exceptions.Forbidden: 1 error occurred:
	* permission denied
```

