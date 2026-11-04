#!/bin/bash
set -eu
PID=/home/student/lab/tls/server.pid
case "${1:-status}" in
start)
  if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo 'TLS server already running :4433'; exit 0; fi
  cd /home/student/lab/tls
  openssl s_server -accept 127.0.0.1:4433 -cert server.pem -key server.key -www -tls1_3 >server.log 2>&1 &
  echo $! > "$PID"
  echo 'TLS 1.3 server started at localhost:4433'
  ;;
stop)
  if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then kill "$(cat "$PID")"; fi
  rm -f "$PID"
  ;;
status)
  if [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; then echo 'running :4433'; else echo stopped; fi
  ;;
*) echo 'Usage: lab-server start|stop|status'; exit 1;;
esac
