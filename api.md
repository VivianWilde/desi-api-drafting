---
author: Vivien Goyal
title: Api
---

# Mail

Hi Stephen,

I\'ve run into an error with the `"spectra/plot/fujilite/radec/210.9,24.8,180"`{.verbatim} endpoint, which I\'ve narrowed down to a bug in how my code interacts with `prospect.viewer.plot_spectra`{.verbatim}.

Specifically, the Plot endpoint fails, but if I try the same request with Download instead it works fine, so I\'m pretty sure the bug is specifically related to `plotspectra`{.verbatim}.

I\'ve attached the relevant function call (this is the only time I call `plotspectra`{.verbatim} in my code), as well as the relevant part of the traceback. My guess is that the naive call to `plotspectra`{.verbatim} asks it to plot a target of type `QSO`{.verbatim}, and either `plotspectra`{.verbatim} doesn\'t know how to draw those or it isn\'t able to find the template/specifications for drawing them.

``` python
plotspectra(
            spectra,
            zcatalog=spectra.extra_catalog,
            html_dir=save_dir,
            title=file_name,
            with_vi_widgets=False,
            with_full_2ndfit=False,
            num_approx_fits=0,
        )
```

      File "/home/vivien/OneDrive_Personal/work/urap/desi-api/webapp.py", line 282, in spectra_to_html
        plotspectra(
      File "/home/vivien/.local/lib/python3.11/site-packages/prospect-1.3.1.dev536-py3.11.egg/prospect/viewer/__init__.py", line 275, in plotspectra
        model = create_model(spectra, zcatalog,
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/home/vivien/.local/lib/python3.11/site-packages/prospect-1.3.1.dev536-py3.11.egg/prospect/viewer/__init__.py", line 109, in create_model
        tx    = templates[(zb['SPECTYPE'], subtype)]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    KeyError: ('QSO', '')
