#!/bin/bash
# Instala Apache Pig 0.17.0 dentro del contenedor del NameNode (si todavia no esta)
# El contenedor no trae el comando which y Pig lo necesita para encontrar Hadoop
if ! command -v which >/dev/null 2>&1; then
  printf '#!/bin/bash\ncommand -v "$1"\n' > /usr/local/bin/which
  chmod +x /usr/local/bin/which
fi

if [ -d /opt/pig ]; then
  echo "Pig ya esta instalado"
  exit 0
fi
cd /tmp
curl -sSLO https://archive.apache.org/dist/pig/pig-0.17.0/pig-0.17.0.tar.gz
tar -xzf pig-0.17.0.tar.gz
mv pig-0.17.0 /opt/pig
rm pig-0.17.0.tar.gz
/opt/pig/bin/pig -version