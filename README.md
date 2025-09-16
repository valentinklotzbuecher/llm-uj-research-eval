# LLM-based Research Evaluation Demo 📑🤖

This Quarto book uses LLMs to evaluate research papers based on The Unjournal metrics, and compares the results to human evaluations. (See our abstract for more detail)

We are working on this collaboratively in [this Github repo](https://github.com/valentinklotzbuecher/llm-uj-research-eval#)


## Live site

<https://llm-uj-research-eval.netlify.app>

<!-- DR @VK Explain how to update this here.-->

## Data layout
papers/    raw PDFs (tracked, large files OK)
results/   generated JSON + CSV <!-- DR: there is no such folder, at least I couldn't find one. Was it .gitignored? -->
key/       openai_key.txt (git-ignored)

## Other notes

May need to do 

```
conda env create -f environment.yml
conda activate qpy311

# 2) (belt & braces) point Quarto at this exact python
export QUARTO_PYTHON="$(which python)"


quarto render

```


### Development setup notes

This project uses R (managed by renv) and Python (managed by conda) together in Quarto. Follow these steps to reproduce the environment:

1. R setup
Open the project in RStudio.

Run:
install.packages("renv")
renv::restore()

This installs the R packages listed in renv.lock.

2. Python setup

We use a conda environment defined in environment.yml.
Install Miniforge or Miniconda

Create the environment (first time only):
conda env create -f environment.yml

Or update an existing one:
conda env update -n qpy311 -f environment.yml

Activate it:
conda activate qpy311

3. Quarto + rendering

To check your setup:
quarto check

To render the site:
quarto render


Optional: add this to your shell config so Quarto always picks the right Python without needing conda activate:

export QUARTO_PYTHON="$(conda run -n qpy311 which python)"
