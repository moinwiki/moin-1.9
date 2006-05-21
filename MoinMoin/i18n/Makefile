POFILES = $(wildcard *.po)
UPDATEPOFILES = $(POFILES:.po=.po-update)
CATALOGS = $(POFILES:.po=.mo)
NOPFILES = $(POFILES:.po=.nop)
DOMAIN = MoinMoin

.SUFFIXES: .mo .po .po-update .nop

-include POTFILES

POTFILES: POTFILES.in
	@echo "POTFILES = \\" > POTFILES
	@sed -e '/^#/d' -e "/^[ ]*\$$/d" -e 's,.*,	../& \\,' -e '$$s/\(.*\) \\/\1/' < POTFILES.in >> POTFILES

.po.mo:
	@lang=`echo $@ | sed -e 's/\.mo$$//'`; \
	msgfmt $$lang.po -o mo/$$lang.$(DOMAIN).mo

.nop.po-update:
	@lang=`echo $@ | sed -e 's/\.po-update$$//'`; \
	echo "$$lang:"; \
	./wiki2po.py $${lang}; \
	echo "msgmerge $$lang.po $(DOMAIN).pot -o $$lang.new.po"; \
	if msgmerge $$lang.po $(DOMAIN).pot -o $$lang.new.po; then \
	  if cmp $$lang.po $$lang.new.po >/dev/null 2>&1; then \
	    rm -f $$lang.new.po; \
	  else \
	    echo XXX ./po2wiki.py $$lang <$$lang.new.po; \
	    rm -f $$lang.new.po; \
	  fi; \
	else \
	  echo "msgmerge for $$lang.po failed!" 1>&2; \
	  rm -f $$lang.new.po; \
	fi

# remove "--no-location" if you want to have file names and line numbers
# that's bad for merging branches - this is why we don't use it
$(DOMAIN).pot-update: $(POTFILES) POTFILES
	xgettext --default-domain=$(DOMAIN) --directory=.. \
	  --files-from=POTFILES.in \
	  --no-location \
	  --add-comments=TRANSLATORS:
	@test ! -f $(DOMAIN).po || { \
	  if test -f $(DOMAIN).pot; then \
	    sed -e 's/^"POT-Creation-Date: .*\"$$//' < $(DOMAIN).pot > $(DOMAIN).1po && \
	    sed -e 's/^"POT-Creation-Date: .*"$$//' < $(DOMAIN).po > $(DOMAIN).2po && \
	    if cmp $(DOMAIN).1po $(DOMAIN).2po >/dev/null 2>&1; then \
	      rm -f $(DOMAIN).1po $(DOMAIN).2po $(DOMAIN).po; \
	    else \
	      rm -f $(DOMAIN).1po $(DOMAIN).2po $(DOMAIN).pot && \
	      mv $(DOMAIN).po $(DOMAIN).pot; \
	    fi; \
	  else \
	    mv $(DOMAIN).po $(DOMAIN).pot; \
	  fi; \
	}

$(DOMAIN).pot:
	$(MAKE) $(DOMAIN).pot-update

$(POFILES):
	@lang=`echo $@ | sed -e 's,.*/,,' -e 's/\.po$$//'`; \
	./wiki2po.py $${lang}; \
	echo msgmerge $${lang}.po $(DOMAIN).pot -o $${lang}.new.po; \
	msgmerge $${lang}.po $(DOMAIN).pot -o $${lang}.new.po; \
	echo XXX ./po2wiki.py $${lang} <$$lang.new.po; \
	rm -f $$lang.new.po
	

$(NOPFILES):

update-po:
	@echo "Edit Makefile and remove some XXX after finally closing 1.5.x branch,"
	@echo "no 1.5.x i18n updates will be possible once this is run in 1.6."
	$(MAKE) $(DOMAIN).pot-update
	$(MAKE) $(UPDATEPOFILES)
	$(MAKE) $(CATALOGS)

stats:
	@files="$(POFILES)"; \
	for i in $$files; do \
	  lang=`echo $$i | sed -e 's,.*/,,' -e 's/\.po$$//'`; \
	  echo -n "$$lang: "; \
	  msgfmt -o /dev/null --statistics $$i; \
	done

clean:
	rm -f POTFILES

