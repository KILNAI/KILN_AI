# Kiln AI Core Library

<p align="center">
    <picture>
        <img width="205" alt="Kiln AI Logo" src="https://github.com/user-attachments/assets/5fbcbdf7-1feb-45c9-bd73-99a46dd0a47f">
    </picture>
</p>

[![PyPI - Version](https://img.shields.io/pypi/v/kiln-ai.svg?logo=pypi&label=PyPI&logoColor=gold)](https://pypi.org/project/kiln-ai)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kiln-ai.svg)](https://pypi.org/project/kiln-ai)
[![Docs](https://img.shields.io/badge/docs-pdoc-blue)](https://kiln-ai.github.io/Kiln/kiln_core_docs/index.html)

---

## Installation

```console
pip install kiln_ai
```

## About

This package is the Kiln AI core library. There is also a separate desktop application and server package. Learn more about Kiln AI at [getkiln.ai](https://getkiln.ai) and on Github: [github.com/Kiln-AI/kiln](https://github.com/Kiln-AI/kiln).

# Guide: Using the Kiln Python Library

In this guide we'll walk common examples of how to use the library.

## Documentation

The library has a [comprehensive set of docs](https://kiln-ai.github.io/Kiln/kiln_core_docs/index.html).

## Table of Contents

- [Using the Kiln Data Model](#using-the-kiln-data-model)
  - [Understanding the Kiln Data Model](#understanding-the-kiln-data-model)
  - [Datamodel Overview](#datamodel-overview)
  - [Load a Project](#load-a-project)
  - [Load an Existing Dataset into a Kiln Task Dataset](#load-an-existing-dataset-into-a-kiln-task-dataset)
  - [Using your Kiln Dataset in a Notebook or Project](#using-your-kiln-dataset-in-a-notebook-or-project)
  - [Using Kiln Dataset in Pandas](#using-kiln-dataset-in-pandas)
- [Advanced Usage](#advanced-usage)

## Installation

```bash
pip install kiln-ai
```

## Using the Kiln Data Model

### Understanding the Kiln Data Model

Kiln projects are simply a directory of files (mostly JSON files with the extension `.kiln`) that describe your project, including tasks, runs, and other data.

This dataset design was chosen for several reasons:

- Git compatibility: Kiln project folders are easy to collaborate on in git. The filenames use unique IDs to avoid conflicts and allow many people to work in parallel. The files are small and easy to compare using standard diff tools.
- JSON allows you to easily load and manipulate the data using standard tools (pandas, polars, etc)

The Kiln Python library provides a set of Python classes that which help you easily interact with your Kiln dataset. Using the library to load and manipulate your dataset is the fastest way to get started, and will guarantees you don't insert any invalid data into your dataset. There's extensive validation when using the library, so we recommend using it to load and manipulate your dataset over direct JSON manipulation.

### Datamodel Overview

- Project: a Kiln Project that organizes related tasks
  - Task: a specific task including prompt instructions, input/output schemas, and requirements
    - TaskRun: a sample (run) of a task including input, output and human rating information
    - DatasetSplit: a frozen collection of task runs divided into train/test/validation splits
    - Finetune: configuration and status tracking for fine-tuning models on task data

### Load a Project

Assuming you've created a project in the Kiln UI, you'll have a `project.kiln` file in your `~/Kiln Projects/Project Name` directory.

```python
from kiln_ai.datamodel import Project

project = Project.load_from_file("path/to/your/project.kiln")
print("Project: ", project.name, " - ", project.description)

# List all tasks in the project, and their dataset sizes
tasks = project.tasks()
for task in tasks:
    print("Task: ", task.name, " - ", task.description)
    print("Total dataset size:", len(task.runs()))
```

### Load an Existing Dataset into a Kiln Task Dataset

If you already have a dataset in a file, you can load it into a Kiln project.

**Important**: Kiln will validate the input and output schemas, and ensure that each datapoint in the dataset is valid for this task.

- Plaintext input/output: ensure "output_json_schema" and "input_json_schema" not set in your Task definition.
- JSON input/output: ensure "output_json_schema" and "input_json_schema" are valid JSON schemas in your Task definition. Every datapoint in the dataset must be valid JSON fitting the schema.

Here's a simple example of how to load a dataset into a Kiln task:

```python

import kiln_ai
import kiln_ai.datamodel

# Created a project and task via the UI and put its path here
task_path = "/Users/youruser/Kiln Projects/test project/tasks/632780983478 - Joke Generator/task.kiln"
task = kiln_ai.datamodel.Task.load_from_file(task_path)

# Add data to the task - loop over you dataset and run this for each item
item = kiln_ai.datamodel.TaskRun(
    parent=task,
    input='{"topic": "AI"}',
    output=kiln_ai.datamodel.TaskOutput(
        output='{"setup": "What is AI?", "punchline": "content_here"}',
    ),
)
item.save_to_file()
print("Saved item to file: ", item.path)
```

And here's a more complex example of how to load a dataset into a Kiln task. This example sets the source of the data (human in this case, but you can also set it be be synthetic), the created_by property, and a 5-star rating.

```python
import kiln_ai
import kiln_ai.datamodel

# Created a project and task via the UI and put its path here
task_path = "/Users/youruser/Kiln Projects/test project/tasks/632780983478 - Joke Generator/task.kiln"
task = kiln_ai.datamodel.Task.load_from_file(task_path)

# Add data to the task - loop over you dataset and run this for each item
item = kiln_ai.datamodel.TaskRun(
    parent=task,
    input='{"topic": "AI"}',
    input_source=kiln_ai.datamodel.DataSource(
        type=kiln_ai.datamodel.DataSourceType.human,
        properties={"created_by": "John Doe"},
    ),
    output=kiln_ai.datamodel.TaskOutput(
        output='{"setup": "What is AI?", "punchline": "content_here"}',
        source=kiln_ai.datamodel.DataSource(
            type=kiln_ai.datamodel.DataSourceType.human,
            properties={"created_by": "Jane Doe"},
        ),
        rating=kiln_ai.datamodel.TaskOutputRating(score=5,type="five_star"),
    ),
)
item.save_to_file()
print("Saved item to file: ", item.path)
```

### Using your Kiln Dataset in a Notebook or Project

You can use your Kiln dataset in a notebook or project by loading the dataset into a pandas dataframe.

```python
import kiln_ai
import kiln_ai.datamodel

# Created a project and task via the UI and put its path here
task_path = "/Users/youruser/Kiln Projects/test project/tasks/632780983478 - Joke Generator/task.kiln"
task = kiln_ai.datamodel.Task.load_from_file(task_path)

runs = task.runs()
for run in runs:
    print(f"Input: {run.input}")
    print(f"Output: {run.output.output}")

print(f"Total runs: {len(runs)}")
```

### Using Kiln Dataset in Pandas

You can also use your Kiln dataset in a pandas dataframe, or a similar script for other tools like polars.

```python
import glob
import json
import pandas as pd
from pathlib import Path

task_dir = "/Users/youruser/Kiln Projects/test project/tasks/632780983478 - Joke Generator"
dataitem_glob = task_dir + "/runs/*/task_run.kiln"

dfs = []
for file in glob.glob(dataitem_glob):
    js = json.loads(Path(file).read_text())

    df = pd.DataFrame([{
        "input": js["input"],
        "output": js["output"]["output"],
    }])

    # Alternatively: you can use pd.json_normalize(js) to get the full json structure
    # df = pd.json_normalize(js)
    dfs.append(df)
final_df = pd.concat(dfs, ignore_index=True)
print(final_df)
```

### Advanced Usage

The library can do a lot more than the examples we've shown here.

See the [docs](https://kiln-ai.github.io/Kiln/kiln_core_docs/index.html) for more information.