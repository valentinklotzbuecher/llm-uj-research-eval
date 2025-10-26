# Global choices and parameters

model_choice <- "gpt-5-pro"

modelversion = "gpt-5-pro-2025-10-06"

data_path <- "data/"
results_path <- "results/"
papers_path <- "papers/"

# Add other parameters as needed
other_param <- "some_value"

# Count the number of papers in the papers/ folder
n_papers <- length(list.files(papers_path, pattern = "\\.pdf$", full.names = TRUE))

# Obtain/replace other objects, potentially those computed in previous runs with LLM (implying multiple runs may be needed for full replication)
n_paper_processed <- n_papers # Placeholder, replace with actual computation if needed
# n_paper_processed ...  assign from previous saved object
