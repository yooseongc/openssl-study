"""A local ephemeral TLS server that deliberately omits close_notify."""
import os
from pathlib import Path
import socket
import ssl
import subprocess
import sys
import threading

def exercise(binary, stall=False):
    context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('/home/student/lab/tls/server.pem','/home/student/lab/tls/server.key')
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0));listener.listen(1);listener.settimeout(12)
        port=listener.getsockname()[1]
        stop=threading.Event();errors=[]
        def serve():
            try:
                conn,_=listener.accept();conn.settimeout(12)
                with conn:
                    if stall:
                        stop.wait(10);return
                    with context.wrap_socket(conn,server_side=True) as tls:
                        tls.recv(4096)
                        fd=tls.detach() # Deliberate transport close, no TLS shutdown.
                        os.close(fd)
            except Exception as e:errors.append(str(e))
        thread=threading.Thread(target=serve,daemon=True);thread.start()
        try:
            result=subprocess.run([str(Path(binary).resolve()),'nonblock','localhost','/home/student/lab/tls/ca.pem',str(port)],capture_output=True,text=True,timeout=12)
        finally:
            stop.set();thread.join(timeout=2)
        text=result.stdout+result.stderr
        assert result.returncode==1,(result.returncode,text)
        assert ('deadline' in text if stall else 'unexpected eof while reading' in text),text
        assert not errors,errors
        return text

if __name__=='__main__':
    print(exercise(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='stall'))
    print('PASS: deadline enforced' if len(sys.argv)>2 else 'PASS: abrupt EOF rejected')
