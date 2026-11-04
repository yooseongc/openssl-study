#!/bin/bash
set -eu
umask 077
dest=${1:-/home/student/lab/chain}
mkdir -p "$dest"
cd "$dest"
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout root.key -out root.pem -days 365 -subj '/CN=Chain Lab Root' -addext 'basicConstraints=critical,CA:TRUE,pathlen:1' -addext 'keyUsage=critical,keyCertSign,cRLSign'
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout intermediate.key -out intermediate.csr -subj '/CN=Chain Lab Intermediate'
printf 'basicConstraints=critical,CA:TRUE,pathlen:0\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n' > intermediate.ext
openssl x509 -req -in intermediate.csr -CA root.pem -CAkey root.key -CAcreateserial -days 180 -extfile intermediate.ext -out intermediate.pem
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -keyout leaf.key -out leaf.csr -subj '/CN=chain.local'
printf 'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\nsubjectAltName=DNS:chain.local\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n' > leaf.ext
openssl x509 -req -in leaf.csr -CA intermediate.pem -CAkey intermediate.key -CAcreateserial -days 30 -extfile leaf.ext -out leaf.pem
echo 'Created root.pem -> intermediate.pem -> leaf.pem'
