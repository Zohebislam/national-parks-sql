.PHONY: all download build analyze test clean
all:      ; python run.py all
download: ; python run.py download
build:    ; python run.py build
analyze:  ; python run.py analyze
test:     ; python -m unittest discover tests -v
clean:    ; rm -f data/national_parks.db results/*.csv figures/*.png reports/*.md
