FROM node:22-bookworm-slim AS assets
WORKDIR /assets
RUN npm install --save-exact @xterm/xterm@5.5.0 @xterm/addon-fit@0.10.0

RUN npm install --save-exact codemirror@5.65.18

FROM python:3.13-slim-trixie
ARG OPENSSL_DEB_VERSION=3.5.7-1~deb13u3
RUN apt-get update && apt-get install -y --no-install-recommends openssl=${OPENSSL_DEB_VERSION} libssl-dev=${OPENSSL_DEB_VERSION} libssl3t64=${OPENSSL_DEB_VERSION} gcc g++ libboost-system-dev libc6-dev make curl procps ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN openssl version | grep -E '^OpenSSL 3\.5\.7 '
RUN pip install --no-cache-dir aiohttp==3.12.15
RUN useradd -m -u 1000 -s /bin/bash student && mkdir -p /home/student/lab && chown student:student /home/student/lab
WORKDIR /opt/app
COPY app/ ./
COPY examples/ /opt/examples/
COPY scripts/ /opt/scripts/
COPY --from=assets /assets/node_modules/@xterm/xterm/lib/xterm.js /opt/app/static/vendor/xterm.js
COPY --from=assets /assets/node_modules/@xterm/xterm/css/xterm.css /opt/app/static/vendor/xterm.css
COPY --from=assets /assets/node_modules/@xterm/addon-fit/lib/addon-fit.js /opt/app/static/vendor/addon-fit.js
COPY --from=assets /assets/node_modules/codemirror/lib/codemirror.js /assets/node_modules/codemirror/lib/codemirror.css /assets/node_modules/codemirror/mode/clike/clike.js /assets/node_modules/codemirror/theme/material-darker.css /opt/app/static/vendor/
COPY --from=assets /assets/node_modules/codemirror/LICENSE /opt/app/static/vendor/codemirror-LICENSE
RUN chmod +x /opt/scripts/*.sh && ln -s /opt/scripts/lab-server.sh /usr/local/bin/lab-server && ln -s /opt/scripts/study-build.sh /usr/local/bin/study-build
ENV PYTHONUNBUFFERED=1 TERM=xterm-256color LANG=C.UTF-8
USER student
EXPOSE 8080
ENTRYPOINT ["/opt/scripts/entrypoint.sh"]
