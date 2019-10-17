SPHINXBUILD 	= sphinx-build -W
SOURCEDIR 	= .
OUTPUTDIR	= ../docs

DOCTREES	= -d ./doctrees

html:
	$(SPHINXBUILD) -b html $(DOCTREES) $(SOURCEDIR) $(OUTPUTDIR)
	cp ./CNAME $(OUTPUTDIR)
