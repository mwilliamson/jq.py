.SHELLFLAGS = --noprofile --norc -c

build:
	which sed
	sed --version
	printf '%s\n' 's/\\/\\\\/g'
	echo 1 | printf '%s\n' 's/\\/\\\\/g'
	echo x > x
	echo "SHELL:" $(SHELL)
	echo 1 | echo "SHELL:" $(SHELL)
	echo ".SHELLFLAGS:" $(.SHELLFLAGS)
	sed --debug -e 's/\\/\\\\/g' x
	echo 1 | sed --debug -e 's/\\\\/\\\\\\\\/g'
	echo 1 | sed --debug -e s/\\\\/\\\\\\\\/g
	echo 1 | sed --debug -e 's/\\/\\\\/g'
