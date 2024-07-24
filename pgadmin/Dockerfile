FROM dpage/pgadmin4

# Установите переменную окружения, чтобы pgAdmin использовал другой порт
ENV PGADMIN_LISTEN_PORT=8080

# Измените команду запуска, чтобы она учитывала новый порт
ENTRYPOINT ["/entrypoint.sh"]
CMD ["--port", "8080"]