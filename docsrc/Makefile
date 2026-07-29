# -E -a forces a full rebuild. The invest-inputs directive generates its output
# from natcap.invest's MODEL_SPEC and from its own Python at build time, neither
# of which Sphinx tracks as a source dependency -- an incremental build happily
# leaves stale HTML behind when only the extension or the installed InVEST
# changes. Since docs/ is committed and served, the build must be reproducible.
SPHINXBUILD 	= sphinx-build -W -E -a
SOURCEDIR 	= .
OUTPUTDIR	= ../docs

DOCTREES	= -d ./doctrees

html:
	$(SPHINXBUILD) -b html $(DOCTREES) $(SOURCEDIR) $(OUTPUTDIR)
	cp ./CNAME $(OUTPUTDIR)
