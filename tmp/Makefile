build:
	which sed
	sed --version
	printf '%s\n' 's/\\/\\\\/g'
	echo 1 | sed --debug -e 's/\\\\/\\\\\\\\/g'
	echo 1 | sed --debug -e s/\\\\/\\\\\\\\/g
	echo 1 | sed --debug -e 's/\\/\\\\/g'
