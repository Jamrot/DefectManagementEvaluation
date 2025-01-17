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

## Citing the Paper
```
@inproceedings {299549,
	author = {Peiyu Liu and Junming Liu and Lirong Fu and Kangjie Lu and Yifan Xia and Xuhong Zhang and Wenzhi Chen and Haiqin Weng and Shouling Ji and Wenhai Wang},
	title = {Exploring ChatGPT's Capabilities on Vulnerability Management},
	booktitle = {33rd USENIX Security Symposium (USENIX Security 24)},
	year = {2024},
	isbn = {978-1-939133-44-1},
	address = {Philadelphia, PA},
	pages = {811--828},
	url = {https://www.usenix.org/conference/usenixsecurity24/presentation/liu-peiyu},
	publisher = {USENIX Association},
	month = aug
}
```
