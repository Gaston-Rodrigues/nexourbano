#!/bin/bash
# Instala un JDK 8, Sqoop 1.4.7 y el driver de MySQL dentro del contenedor del NameNode
# Cada parte se saltea si ya esta instalada

# 1. JDK 8: el contenedor solo trae el JRE y Sqoop necesita javac para compilar su clase
if [ ! -x /opt/jdk8/bin/javac ]; then
  mkdir -p /opt/jdk8
  cd /tmp
  curl -sSL -o jdk8.tar.gz "https://api.adoptium.net/v3/binary/latest/8/ga/linux/x64/jdk/hotspot/normal/eclipse"
  tar -xzf jdk8.tar.gz -C /opt/jdk8 --strip-components=1
  rm jdk8.tar.gz
fi
/opt/jdk8/bin/javac -version

# 2. Sqoop 1.4.7 (la ultima version, pensada para Hadoop 2)
if [ ! -d /opt/sqoop ]; then
  cd /tmp
  curl -sSLO https://archive.apache.org/dist/sqoop/1.4.7/sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz
  tar -xzf sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz
  mv sqoop-1.4.7.bin__hadoop-2.6.0 /opt/sqoop
  rm sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz
  # Driver JDBC de MySQL y commons-lang (Sqoop las necesita; Hadoop 3 ya no trae commons-lang)
  curl -sSL -o /opt/sqoop/lib/mysql-connector-java-8.0.30.jar https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.30/mysql-connector-java-8.0.30.jar
  curl -sSL -o /opt/sqoop/lib/commons-lang-2.6.jar https://repo1.maven.org/maven2/commons-lang/commons-lang/2.6/commons-lang-2.6.jar
fi

# 3. Probar Sqoop
export JAVA_HOME=/opt/jdk8
export HADOOP_COMMON_HOME=/opt/hadoop
export HADOOP_MAPRED_HOME=/opt/hadoop
/opt/sqoop/bin/sqoop version