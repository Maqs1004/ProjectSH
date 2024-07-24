FROM alpine:latest

RUN apk --no-cache add postgresql-client bash nano
RUN mkdir -p /scripts /backups/backup_files /var/log
WORKDIR /app
COPY scripts/backup.sh .
RUN chmod +x backup.sh
CMD ["./backup.sh"]