# makefile for building jq

.PHONY: jq_tarball jq_src jq_lib

jq_build_parent:=_deps/build
jq_version=$(shell echo $(shell ls deps/jq-*.tar.gz) | grep -oP 'jq-\K[\d.]+(?=.tar.gz)')
jq_tarball_path:=deps/jq-$(jq_version).tar.gz
jq_build_path:=$(jq_build_parent)/jq-$(jq_version)

all: $(jq_build_path)/.libs/libjq.a $(jq_build_path)/modules/oniguruma/src/.libs/libonig.a

jq_tarball: $(jq_tarball_path)
	echo "found jq tarball: $(jq_tarball_path)"
	
jq_src: jq_tarball
	# extract tarball to jq_build_path
	mkdir -p $(jq_build_path)
	tar -xf $(jq_tarball_path) -C $(jq_build_parent)

$(jq_build_path)/.libs/libjq.a $(jq_build_path)/modules/oniguruma/src/.libs/libonig.a: jq_lib

jq_lib: jq_src 
	# build jq
	cd $(jq_build_path) ; \
	./configure CFLAGS="-fPIC -pthread" --disable-maintainer-mode --with-oniguruma=builtin; \
	make

clean:
	rm -rf $(jq_build_parent)