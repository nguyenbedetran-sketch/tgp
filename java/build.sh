#!/usr/bin/env bash
# Fallback build script for the Java report service using only javac + jar
# (no Maven / internet access required). Prefer `mvn -f pom.xml package`
# when you have access to Maven Central; use this script otherwise
# (e.g. inside an offline/sandboxed CI environment).
set -euo pipefail
cd "$(dirname "$0")"

rm -rf target
mkdir -p target/classes

javac -encoding UTF-8 -d target/classes src/main/java/com/trangiaphat/report/*.java

(
  cd target/classes
  jar --create --file ../tgp-report-service.jar \
      --main-class com.trangiaphat.report.Main com
)

echo "Built target/tgp-report-service.jar"
