FROM python:3.7
COPY "./dist/$pex" "/app/$pex"
WORKDIR /app
CMD ["/app/$pex", "--config", "/run/secrets/public-dns.yml"]
