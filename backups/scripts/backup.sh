#!/bin/bash

DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
DB_HOST=${DB_HOST}
DB_USER_DEV=${DB_USER_DEV}
DB_PASSWORD_DEV=${DB_PASSWORD_DEV}
DB_NAME_DEV=${DB_NAME_DEV}
DB_HOST_DEV=${DB_HOST_DEV}
BACKUP_DIR=/backups/backup_files


echo "Script backup starting!"

# Функция для выполнения резервного копирования
backup() {
  local user=$1
  local password=$2
  local name=$3
  local host=$4
  local backup_type=$5
  local log_file=$6

  BACKUP_FILE="$BACKUP_DIR/backup_${backup_type}_$(date +'%Y%m%d%H%M%S').sql"
  echo "$(date +'%Y-%m-%d %H:%M:%S') - Starting ${backup_type} backup: $BACKUP_FILE" >> $log_file
  if PGPASSWORD=$password pg_dump -h $host -U $user -F c $name > $BACKUP_FILE 2>> $log_file; then
    echo "${backup_type} backup successful: $BACKUP_FILE"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - ${backup_type} backup successful: $BACKUP_FILE" >> $log_file
  else
    echo "${backup_type} backup failed"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - ${backup_type} backup failed" >> $log_file
  fi

  # Удаление старых резервных копий (старше 3 дней)
  OLD_BACKUPS=$(find $BACKUP_DIR -type f -name "*.sql" -mtime +3)
  if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | xargs rm
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Old ${backup_type} backups deleted"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - Old ${backup_type} backups deleted" >> $log_file
  else
    echo "$(date +'%Y-%m-%d %H:%M:%S') - No old ${backup_type} backups to delete"
    echo "$(date +'%Y-%m-%d %H:%M:%S') - No old ${backup_type} backups to delete" >> $log_file
  fi
}

# Бесконечный цикл для выполнения резервного копирования каждые 6 часов
while true; do
  backup $DB_USER $DB_PASSWORD $DB_NAME $DB_HOST "prod" "/var/log/backup_dev.log"
  backup $DB_USER_DEV $DB_PASSWORD_DEV $DB_NAME_DEV $DB_HOST_DEV "dev" "/var/log/backup_dev.log"
  sleep 43200
done