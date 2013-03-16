#
# Makefile for MoinMoin
#

# location for the wikiconfig.py we use for testing:
export PYTHONPATH=$(PWD)

testwiki := ./tests/wiki
share := ./wiki

all:
	python setup.py build

install-docs:
	-mkdir build
	wget -U MoinMoin/Makefile -O build/INSTALL.html "http://master19.moinmo.in/InstallDocs?action=print"
	sed \
		-e 's|http://master19.moinmo.in/moin_static..|../MoinMoin/web/static/htdocs|g' \
		-e 's|http://static.moinmo.in/moin_static..|../MoinMoin/web/static/htdocs|g' \
		-e 's|/moin_static..|../MoinMoin/web/static/htdocs|g' \
		-e 's|/InstallDocs#|#|g' \
		-e 's|/InstallDocs/QuickInstall#qdlinux|#InstallDocs.2BAC8-QuickInstall.2BAC8-Linux.Linux:_Detailed_Quick_Installation|g' \
		-e 's|/InstallDocs/QuickInstall#qdmac|#InstallDocs.2BAC8-QuickInstall.2BAC8-MacOSX.Mac:_Detailed_Quick_Installation|g' \
		-e 's|/InstallDocs/QuickInstall#qdwindows|#InstallDocs.2BAC8-QuickInstall.2BAC8-Windows.Windows:__Detailed_Quick_Installation|g' \
        build/INSTALL.html >docs/INSTALL.html
	-rm build/INSTALL.html

	wget -U MoinMoin/Makefile -O build/UPDATE.html "http://master19.moinmo.in/HelpOnUpdating?action=print"
	sed \
		-e 's|http://master19.moinmo.in/moin_static..|../MoinMoin/web/static/htdocs|g' \
		-e 's|http://static.moinmo.in/moin_static..|../MoinMoin/web/static/htdocs|g' \
		-e 's|/moin_static..|../MoinMoin/web/static/htdocs|g' \
		-e 's|href=./MoinMoin|href=\"http://master19.moinmo.in/MoinMoin|g' \
		-e 's|href=./EditedSystemPages|href=\"http://master19.moinmo.in/EditedSystemPages|g' \
        build/UPDATE.html >docs/UPDATE.html
	-rm build/UPDATE.html
	-rmdir build

interwiki:
	wget -U MoinMoin/Makefile -O $(share)/data/intermap.txt "http://master19.moinmo.in/InterWikiMap?action=raw"
	chmod 664 $(share)/data/intermap.txt

check-tabs:
	@python -c 'import tabnanny ; tabnanny.check("MoinMoin")'

# Create documentation
epydoc: patchlevel
	@epydoc --parse-only -o ../html-1.9 --name=MoinMoin --url=http://moinmo.in/ MoinMoin

# Create new underlay directory from MoinMaster
# Should be used only on TW machine
underlay:
	rm -rf $(share)/underlay
	MoinMoin/script/moin.py --config-dir=/srv/cfg/1.9 --wiki-url=http://master19.moinmo.in/ maint globaledit
	MoinMoin/script/moin.py --config-dir=/srv/cfg/1.9 --wiki-url=http://master19.moinmo.in/ maint reducewiki --target-dir=$(share)/underlay
	rm -rf $(share)/underlay/pages/InterWikiMap
	rm -rf $(share)/underlay/pages/MoinPagesEditorGroup
	cd $(share); rm -f underlay.tar; tar cf underlay.tar underlay

pagepacks:
	@python MoinMoin/_tests/maketestwiki.py
	@MoinMoin/script/moin.py --config-dir=MoinMoin/_tests --wiki-url=http://localhost/ maint mkpagepacks
	cd $(share) ; rm -rf underlay
	cp -a $(testwiki)/underlay $(share)/

dist-clean:
	-rm MANIFEST
	-rm -rf tests/wiki
	-rm -rf wiki/data/cache/{__metalock__,__session__,wikiconfig}
	->wiki/data/event-log
	->wiki/data/edit-log

dist: dist-clean
	python setup.py sdist

dist-release: dist-clean
	python setup.py register sdist upload --identity="Thomas Waldmann" --sign

# Create patchlevel module
patchlevel:
	@echo -e patchlevel = "\"`hg identify`\"\n" >MoinMoin/patchlevel.py
	@MoinMoin/version.py update

# Report translations status
check-i18n:
	MoinMoin/i18n/tools/check_i18n.py

# Update the workdir from the default pull repo
update:
	hg pull -u
	$(MAKE) patchlevel

# Update underlay directory from the tarball
update-underlay:
	cd $(share); rm -rf underlay; tar xf underlay.tar

test:
	@echo Testing is now done using \`py.test\`. py.test can be installed by downloading from http://codespeak.net/py/dist/download.html
	@echo Writing tests is explained on http://codespeak.net/py/dist/test.html

coverage:
	@python MoinMoin/_tests/maketestwiki.py
	@python -u -m trace --count --coverdir=cover --missing tests/runtests.py

pylint:
	@pylint --disable-msg=W0142,W0511,W0612,W0613,C0103,C0111,C0302,C0321,C0322 --disable-msg-cat=R MoinMoin

clean: clean-testwiki clean-pyc
	rm -rf build

clean-testwiki:
	rm -rf $(testwiki)/*

clean-pyc:
	find . -name "*.pyc" -exec rm -rf "{}" \; 

.PHONY: all dist install-docs check-tabs epydoc underlay patchlevel \
	check-i18n update update-underlay test testwiki clean \
	clean-testwiki clean-pyc
