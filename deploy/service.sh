#!/bin/sh

PLUGIN="${0##*/}"

### BEGIN INIT INFO
# Provides:          $PLUGIN
# Required-Start:    $all
# Required-Stop:     $all
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Starts a service for the Twisted plugin '$PLUGIN'
# Description:       Generic plugin starter for twistd plugins
### END INIT INFO
# Author: Garret Heaton (powdahound@gmail.com)

DAEMON=$(which twistd)
PIDFILE=/var/run/$PLUGIN.pid
LOGFILE=/var/log/$PLUGIN.log
DAEMON_OPTS="--pidfile=$PIDFILE --logfile=$LOGFILE $PLUGIN"

if [ ! -x $DAEMON ]; then
  echo "ERROR: Can't execute $DAEMON."
  exit 1
fi

start_service() {
  echo -n " * Starting $PLUGIN... "
  start-stop-daemon -Sq -p $PIDFILE -x $DAEMON -- $DAEMON_OPTS
  e=$?
  if [ $e -eq 1 ]; then
    echo "already running"
    return
  fi

  if [ $e -eq 255 ]; then
    echo "couldn't start :("
    return
  fi

  echo "done"
}

stop_service() {
  echo -n " * Stopping $PLUGIN... "
  start-stop-daemon -Kq -R 10 -p $PIDFILE
  e=$?
  if [ $e -eq 1 ]; then
    echo "not running"
    return
  fi

  echo "done"
}

case "$1" in
  start)
    start_service
    ;;
  stop)
    stop_service
    ;;
  restart)
    stop_service
    start_service
    ;;
  *)
    echo "Usage: /etc/init.d/$PLUGIN {start|stop|restart}" >&2
    exit 1   
    ;;
esac

exit 0