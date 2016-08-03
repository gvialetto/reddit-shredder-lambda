# Makefile for ShredditLambda lambda function
TARGET=reddit-shredder.zip

all: deps
	zip -r ${TARGET} app/* main.py config.json
	test -d deps || exit 1
	cd deps; zip -r ../${TARGET} *

deps:
	mkdir -p deps
	pip2 install requests -t deps
	pip2 install transitions -t deps

clean:
	rm -rf deps
	rm -f ./${TARGET}
	find . -name '*.pyc' -exec rm -v {} \;
