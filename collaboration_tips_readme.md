# Contributing Guide (GPT suggested, some edits)

See https://chatgpt.com/share/68b6e7af-58a0-8002-a639-0a3488a3884b

Thanks for contributing! To keep things smooth and reproducible, please follow these steps.

## Getting started
1. Clone the repo from GitHub.
2. Open the project in RStudio by double-clicking the `.Rproj` file in the repo root.
3. Run:
```r
   install.packages("renv")
   renv::restore()
```
This installs the correct package versions from renv.lock.
- Install additional packages through renv: renv::install("...")
- After installing the package and checking that your code works, 
you should call renv::snapshot() to record the latest package versions 

## Day-to-day workflow
Always git pull before starting work.

PROBLY NOT GONNA DO THIS: Use feature branches (never commit directly to main):

Commit only source code and small data/config files.


## What not to commit
These are already in .gitignore, but just in case:

.Rproj.user/, .Rhistory, .RData

renv/library/ (your local package cache)

Secrets in .Renviron (keep those local!)

Your API keys in .key/

## Updating dependencies
If you add or update packages:

```
renv::snapshot()
```

Commit the updated renv.lock.

## RStudio tips

Turn off automatic workspace saving:

Tools --> Global Options  --> General --> [Save workspace: Never].

Don’t rely on .RData files. Always make analysis reproducible via scripts.

Copy code


## How to discuss code and output (tbd)

hypothes.is ?

giscuss.app ? 

GH projects?
