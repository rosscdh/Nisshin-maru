.PHONY: all build login push run tag run-single-backend run-multi-backend

default: build

PREFIX   := rosscdh/nisshin-maru
TAG      := $(shell git describe --tags --always)
REGISTRY := registry.hub.docker.com

BUILD_REPO_ORIGIN := $(shell git config --get remote.origin.url)
BUILD_COMMIT_SHA1 := $(shell git rev-parse --short HEAD)
BUILD_COMMIT_DATE := $(shell git log -1 --date=short --pretty=format:%ct)
BUILD_BRANCH := $(shell git symbolic-ref --short HEAD)
BUILD_DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

all: build login push

build:
	docker build -t ${PREFIX}:latest -t ${REGISTRY}/${PREFIX}:latest -t ${REGISTRY}/${PREFIX}:${TAG} \
		--build-arg BUILD_COMMIT_SHA1=${BUILD_COMMIT_SHA1} \
		--build-arg BUILD_COMMIT_DATE=${BUILD_COMMIT_DATE} \
		--build-arg BUILD_BRANCH=${BUILD_BRANCH} \
		--build-arg BUILD_DATE=${BUILD_DATE} \
		--build-arg BUILD_REPO_ORIGIN=${BUILD_REPO_ORIGIN} \
		. --no-cache

login:
	docker login ${REGISTRY}

push: tag
	docker push ${REGISTRY}/${PREFIX}:latest
	docker push ${REGISTRY}/${PREFIX}:${TAG}

shell:
	docker run --rm -it \
			-e SHOW_ONLY_ERRORS=${SHOW_ONLY_ERRORS} \
			-e MAX_ERROR_RATE=${MAX_ERROR_RATE} \
			-e TOKEN=${TOKEN} \
			-e INSTANA_ENDPOINT=${INSTANA_ENDPOINT} \
			-v ${PWD}:/src \
			--entrypoint sh \
			rosscdh/nisshin-maru:latest