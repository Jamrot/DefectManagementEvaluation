# ChatGPT-Vulnerability-Management

## Description
This repository serves as a database for our evaluation of ChatGPT's Capabilities on Vulnerability Management. It contains source code, datasets and prompts used across six vulnerability management tasks.

## Structure
| Directory/File      | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `src`             | Source code to evaluate ChatGPT's capibilities. |
| ├─ `request.py`   | Call API through HTTP requests. |
| ├─ `prompt.py`    | Generate prompt from templates. |
| └─ `vulfix`       | Combine the response and original code. Evaluate the correctness of fixing codes. |
| `data`            | Datasets and prompt templates used across 6 tasks. |
| ├─ `title`        | dataset and prompt templates used for bug report title generation task. |
| ├─ `SBRP`         | dataset and prompt templates used for security bug report prediction task. |
| ├─ `cvss`         | dataset and prompt templates used for vulnerability severity evaluation task. |
| ├─ `vulfix`       | dataset and prompt templates used for vulnerability repair task. |
| ├─ `APCA`         | dataset and prompt templates used for patch correctness assessment task. |
| └─ `stable`       | dataset and prompt templates used for stable patch classification task. |

