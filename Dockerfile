FROM node:22-bookworm-slim AS assets
WORKDIR /assets
RUN npm install --save-exact @xterm/xterm@5.5.0 @xterm/addon-fit@0.10.0



FROM python:3.13-slim-trixie
ARG OPENSSL_DEB_VERSION=3.5.7-1~deb13u3
RUN apt-get update && apt-get install -y --no-install-recommends openssl=${OPENSSL_DEB_VERSION} libssl-dev=${OPENSSL_DEB_VERSION} libssl3t64=${OPENSSL_DEB_VERSION} gcc g++ libboost-system-dev libc6-dev make curl procps ca-certificates clangd clang-format gdb less \
    && rm -rf /var/lib/apt/lists/*
RUN openssl version | grep -E '^OpenSSL 3\.5\.7 '
RUN pip install --no-cache-dir aiohttp==3.12.15
RUN useradd -m -u 1000 -s /bin/bash student && mkdir -p /home/student/lab && chown student:student /home/student/lab
WORKDIR /opt/app
ARG CODE_SERVER_VERSION=4.145.2
RUN curl -fL --retry 3 "https://github.com/coder/code-server/releases/download/v${CODE_SERVER_VERSION}/code-server-${CODE_SERVER_VERSION}-linux-amd64.tar.gz" -o /tmp/code-server.tgz \
    && echo '2f6db6c3e8b733dd6b3aeee83532e148b2bae2e392353ba85452d03572348962  /tmp/code-server.tgz' | sha256sum -c - \
    && mkdir -p /opt/code-server && tar -xzf /tmp/code-server.tgz -C /opt/code-server --strip-components=1 \
    && rm /tmp/code-server.tgz && ln -s /opt/code-server/bin/code-server /usr/local/bin/code-server
RUN mkdir -p /opt/ide-extensions /home/student/ide-data && chown -R student:student /opt/ide-extensions /home/student/ide-data
USER student
RUN code-server --extensions-dir /opt/ide-extensions --install-extension llvm-vs-code-extensions.vscode-clangd@0.6.0
USER root
RUN curl -fL --retry 3 https://github.com/vadimcn/codelldb/releases/download/v1.12.3/codelldb-linux-x64.vsix -o /tmp/codelldb.vsix \
    && echo '1cd7f386598022b51a5b93b9ffa23e812b23f519cfe1833384ec4bef4bfd1be1  /tmp/codelldb.vsix' | sha256sum -c -
USER student
RUN code-server --extensions-dir /opt/ide-extensions --install-extension /tmp/codelldb.vsix
USER root
COPY app/ ./
COPY examples/ /opt/examples/
COPY .clang-format /opt/study.clang-format
COPY scripts/ /opt/scripts/
COPY --from=assets /assets/node_modules/@xterm/xterm/lib/xterm.js /opt/app/static/vendor/xterm.js
COPY --from=assets /assets/node_modules/@xterm/xterm/css/xterm.css /opt/app/static/vendor/xterm.css
COPY --from=assets /assets/node_modules/@xterm/addon-fit/lib/addon-fit.js /opt/app/static/vendor/addon-fit.js
RUN chmod +x /opt/scripts/*.sh && ln -s /opt/scripts/lab-server.sh /usr/local/bin/lab-server && ln -s /opt/scripts/study-build.sh /usr/local/bin/study-build
ENV PYTHONUNBUFFERED=1 TERM=xterm-256color LANG=C.UTF-8
COPY ide-extension/ /opt/study-extension/
RUN python /opt/scripts/package-extension.py
USER student
RUN code-server --extensions-dir /opt/ide-extensions --install-extension /tmp/study-bridge.vsix
EXPOSE 8080
ENTRYPOINT ["/opt/scripts/entrypoint.sh"]
