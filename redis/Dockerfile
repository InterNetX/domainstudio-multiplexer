# Pull base image.
FROM ubuntu

# Install Redis.
RUN \
  apt update && \
  apt install wget -y && \
  apt install python3 -y && \
  apt install net-tools -y && \
  apt install build-essential -y && \
  cd /tmp && \
  wget http://download.redis.io/redis-stable.tar.gz && \
  tar xvzf redis-stable.tar.gz && \
  cd redis-stable && \
  make && \
  make install && \
  cp -f src/redis-sentinel /usr/local/bin && \
  mkdir -p /etc/redis && \
  cp -f *.conf /etc/redis && \
  rm -rf /tmp/redis-stable* && \
  sed -i 's/^\(bind .*\)$/# \1/' /etc/redis/redis.conf && \
  sed -i 's/^\(daemonize .*\)$/# \1/' /etc/redis/redis.conf && \
  sed -i 's/^\(dir .*\)$/# \1\ndir \/data/' /etc/redis/redis.conf && \
  sed -i 's/^\(logfile .*\)$/# \1/' /etc/redis/redis.conf
  
# Define working directory.
WORKDIR /data

#Copy scripts
COPY . .

# Make Script executable
RUN chmod +x ./redis_boot.sh && \
    chmod +x netcommand.sh

# Define default command.
CMD ["/bin/sh","./redis_boot.sh"]

# Expose ports.
EXPOSE 6379