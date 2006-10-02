#
# Makefile for MoinMoin
#

# location for the wikiconfig.py we use for testing:
export PYTHONPATH=`pwd`/tests

testwiki := ./testwiki
share := ./wiki

all:
	python setup.py build

install-docs:
	-mkdir build
	wget -U MoinMoin/Makefile -O build/INSTALL.html "http://moinmaster.wikiwikiweb.de/MoinMoin/InstallDocs?action=print"
	sed \
		-e 's#href="/#href="http://moinmaster.wikiwikiweb.de/#g' \
		-e 's#http://[a-z\.]*/wiki/classic/#/wiki/classic/#g' \
		-e 's#http://[a-z\.]*/wiki/modern/#/wiki/modern/#g' \
		-e 's#http://[a-z\.]*/wiki/rightsidebar/#/wiki/rightsidebar/#g' \
		-e 's#/wiki/classic/#wiki/htdocs/classic/#g' \
		-e 's#/wiki/modern/#wiki/htdocs/modern/#g' \
		-e 's#/wiki/rightsidebar/#wiki/htdocs/rightsidebar/#g' \
        build/INSTALL.html >docs/INSTALL.html
	-rm build/INSTALL.html

	-rmdir build

interwiki:
	wget -U MoinMoin/Makefile -O $(share)/data/intermap.txt "http://moinmaster.wikiwikiweb.de/InterWikiMap?action=raw"
	chmod 664 $(share)/data/intermap.txt

check-tabs:
	@python -c 'import tabnanny ; tabnanny.check("MoinMoin")'

# Create documentation
epydoc: patchlevel
	@epydoc -o ../html-1.6 -n MoinMoin -u http://moinmoin.wikiwikiweb.de MoinMoin

# Create new underlay directory from MoinMaster
# Should be used only on TW machine
underlay:
	rm -rf $(share)/underlay
	MoinMoin/script/moin.py --config-dir=/srv/de.wikiwikiweb.moinmaster/bin15 --wiki-url=moinmaster.wikiwikiweb.de/ maint globaledit
	MoinMoin/script/moin.py --config-dir=/srv/de.wikiwikiweb.moinmaster/bin15 --wiki-url=moinmaster.wikiwikiweb.de/ maint reducewiki --target-dir=$(share)/underlay
	rm -rf $(share)/underlay/pages/InterWikiMap/
	echo -ne "#acl All:read\r\nSee MoinMoin:EditingOnMoinMaster.\r\n" > \
	    $(share)/underlay/pages/MoinPagesEditorGroup/revisions/00000001
	cd $(share); rm -rf underlay.tar.bz2; tar cjf underlay.tar.bz2 underlay

pagepacks:
	@python tests/maketestwiki.py
	@MoinMoin/script/moin.py maint mkpagepacks # must NOT use --config-dir or --wiki-url here!
	cd $(share) ; rm -rf underlay
	cp -a $(testwiki)/underlay $(share)/
	
dist:
	-rm MANIFEST
	python setup.py sdist

# Create patchlevel module
patchlevel:
	@echo -e patchlevel = "\"`hg identify`\"\n" >MoinMoin/patchlevel.py
	@MoinMoin/version.py update

# Report translations status
check-i18n:
	MoinMoin/i18n/check_i18n.py

# Update the workdir from the default pull repo
update:
	hg pull -u
	$(MAKE) patchlevel

# Update underlay directory from the tarball
update-underlay:
	cd $(share); rm -rf underlay; tar xjf underlay.tar.bz2

test: 
	@python tests/maketestwiki.py
	@python tests/runtests.py

coverage:
	@python tests/maketestwiki.py
	@python -u -m trace --count --coverdir=cover --missing tests/runtests.py


clean: clean-testwiki clean-pyc
	rm -rf build

clean-testwiki:
	rm -rf $(testwiki)/*

clean-pyc:
	find . -name "*.pyc" -exec rm -rf "{}" \; 

.PHONY: all dist install-docs check-tabs epydoc underlay patchlevel \
	check-i18n update update-underlay test testwiki clean \
	clean-testwiki clean-pyc

