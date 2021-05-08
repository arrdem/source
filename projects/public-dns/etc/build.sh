#!/bin/bash

function pants2docker() {
  # $1 MUST BE a pants target including : final component
  ./pants -q binary "$1"
  f=$(mktemp)
  target=$(echo "$1" | awk -F: '{print $2; exit}')
  pex="${target}.pex"
  sed "s/\$pex/$pex/g" "${DOCKERFILE:-src/docker/pex.docker}" > "${f}"

  # Build with tags
  t="arrdem.${target}:latest"
  rt="registry.apartment.arrdem.com:5000/${t}"

  # FIXME (arrdem 2019-09-17):
  #   Create a tag for the SHA and short SHA of the current ref if clean
  docker build -f $f -t "${t}" -t "${rt}" $gt .
  docker push "${rt}"
}

DOCKERFILE=src/docker/arrdem/updater/Dockerfile pants2docker src/python/arrdem/updater:updater

sudo docker stack deploy --compose-file ./src/docker/arrdem/updater/docker-compose.yml arrdem_updater
