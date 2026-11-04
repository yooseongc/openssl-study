#!/bin/bash
set -eu
umask 077
mkdir -p /home/student/lab/{examples,pki,tls,notes}
python /opt/scripts/update-examples.py
cp -rn /opt/examples/. /home/student/lab/examples/
if [ ! -f /home/student/lab/tls/server.pem ]; then
  cd /home/student/lab/tls
  openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.pem -days 3650 -subj '/CN=OpenSSL Study Root' -addext 'basicConstraints=critical,CA:TRUE' -addext 'keyUsage=critical,keyCertSign,cRLSign' 2>/dev/null
  openssl req -new -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj '/CN=localhost' 2>/dev/null
  printf 'subjectAltName=DNS:localhost\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=serverAuth\n' > server.ext
  openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial -out server.pem -days 365 -extfile server.ext 2>/dev/null
fi
cat > /home/student/.bashrc <<'EOF'
export PS1='\[\e[38;5;114m\]student\[\e[0m\]:\[\e[38;5;75m\]\w\[\e[0m\] $ '
export HISTFILE=/home/student/lab/.bash_history
export HISTCONTROL=ignoredups
alias ll='ls -alF'
cd /home/student/lab
EOF
lab-server start
cd /opt/app
exec python server.py
