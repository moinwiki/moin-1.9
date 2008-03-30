POFILES = $(wildcard *.po)
UPDATEPOFILES = $(POFILES:.po=.po-update)
NOPFILES = $(POFILES:.po=.nop)
DOMAIN = MoinMoin

.SUFFIXES: .po .po-update .nop

-include POTFILES

POTFILES.in POTFILES:
	@python tools/mk_POTFILES.py

.nop.po-update:
	@lang=`echo $@ | sed -e 's/\.MoinMoin\.po-update$$//'`; \
	echo "$$lang:"; \
	tools/wiki2po.py $${lang}; \
	echo "msgmerge $$lang.$(DOMAIN).po $(DOMAIN).pot -o $$lang.$(DOMAIN).new.po"; \
	if msgmerge $$lang.$(DOMAIN).po $(DOMAIN).pot -o $$lang.$(DOMAIN).new.po; then \
	  if cmp $$lang.$(DOMAIN).po $$lang.$(DOMAIN).new.po >/dev/null 2>&1; then \
	    rm -f $$lang.$(DOMAIN).new.po; \
	  else \
	    tools/po2wiki.py $$lang <$$lang.$(DOMAIN).new.po; \
	    rm -f $$lang.$(DOMAIN).new.po; \
	  fi; \
	else \
	  echo "msgmerge for $$lang.$(DOMAIN).po failed!" 1>&2; \
	  rm -f $$lang.$(DOMAIN).new.po; \
	fi

# remove "--no-location" if you want to have file names and line numbers
# that's bad for merging branches - this is why we don't use it
$(DOMAIN).pot-update: $(POTFILES) POTFILES.in
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

$(DOMAIN).pot: $(POTFILES) POTFILES.in
	$(MAKE) $(DOMAIN).pot-update

$(POFILES):
	@lang=`echo $@ | sed -e 's,.*/,,' -e 's/\.MoinMoin\.po$$//'`; \
	tools/wiki2po.py $${lang}; \
	echo msgmerge $${lang}.$(DOMAIN).po $(DOMAIN).pot -o $${lang}.$(DOMAIN).new.po; \
	msgmerge $${lang}.$(DOMAIN).po $(DOMAIN).pot -o $${lang}.$(DOMAIN).new.po; \
	tools/po2wiki.py $${lang} <$$lang.$(DOMAIN).new.po; \
	rm -f $$lang.$(DOMAIN).new.po

$(NOPFILES):

update-po: clean
	$(MAKE) $(DOMAIN).pot-update
	$(MAKE) $(UPDATEPOFILES)

stats:
	@files="$(POFILES)"; \
	for i in $$files; do \
	  lang=`echo $$i | sed -e 's,.*/,,' -e 's/\.MoinMoin\.po$$//'`; \
	  echo -n "$$lang: "; \
	  msgfmt -o /dev/null --statistics $$i; \
	done

clean:
	rm -f POTFILES POTFILES.in

