.PHONY: srpm

srpm:
	rpmbuild -D "_sourcedir ." -D "_disable_source_fetch 0" -D "_srcrpmdir $(outdir)" -bs "$(spec)"
