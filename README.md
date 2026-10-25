# GhostTrace AI
## Ghost Data Still Exists — Data Deletion Verification and Evidence Orchestration

**Project Name:** GhostTrace AI  
**Challenge:** Ghost Data Still Exists  
**Project Type:** Data deletion verification and evidence analysis  
**Primary Language:** Python  
**Expected Input Cases:** 518 deletion-request cases  
**Primary Output:** `output.csv`

---

## 1. Project Overview

**GhostTrace AI** is a data deletion verification project designed to assess whether deletion requests have been completed, remain incomplete, or are not applicable based on available evidence.

Deleting a record from one database does not necessarily mean that every copy has been removed. Data may persist in replicas, caches, logs, backups, downstream services, identity mappings, or other storage systems. These residual copies are commonly described as *ghost data*.

GhostTrace AI processes deletion-request cases and their supporting evidence to produce a structured, case-by-case assessment. Each result contains a deletion status and a JSON-formatted list of findings, verification details, or follow-up actions.

The project aims to make deletion verification more systematic, traceable, and reproducible while avoiding unsupported conclusions when the evidence is insufficient.

## 2. Problem Statement

Organizations must be able to demonstrate that data deletion requests have been handled appropriately. A successful deletion workflow may require more than issuing a delete command. It can involve identifying the correct subject, locating associated records, checking relevant storage systems, validating deletion events, and determining whether the available evidence supports completion.

GhostTrace AI addresses the following challenges:

- **Identity resolution:** Connecting a deletion request to the correct user or account using available identifiers.
- **Evidence correlation:** Relating logs, identity mappings, service events, and other artifacts to the same request.
- **Deletion verification:** Distinguishing evidence of a deletion attempt from evidence that deletion was completed.
- **Incomplete evidence:** Avoiding false claims of successful deletion when required checks are missing or inconclusive.
- **Structured reporting:** Producing a consistent CSV result for all input cases.
- **Auditability:** Preserving case identifiers and machine-readable findings so results can be reviewed and tested.

## 3. Project Objectives

The primary objectives of GhostTrace AI are to:

1. Process each deletion-request case in the supplied dataset.
2. Analyze the available evidence relevant to each case.
3. Assign one of the permitted deletion statuses.
4. Record evidence-based findings and appropriate follow-up actions.
5. Serialize case steps as valid JSON arrays.
6. Generate a root-level `output.csv` with the required schema.
7. Support repeatable execution and validation of the generated output.
8. Provide supporting documentation and tests for evaluation.
9. Help reviewers identify cases where additional verification is required.

## 4. Deletion Status Definitions

Every case must use one of the following status values.

| Status | Meaning |
|---|---|
| `COMPLETE` | The available evidence supports that the applicable deletion requirements have been completed and adequately verified. |
| `INCOMPLETE` | Deletion is pending, evidence is insufficient, a relevant system has not been verified, or a required action remains unresolved. |
| `NOT_APPLICABLE` | The deletion workflow does not apply to the case, based on the available case information and evidence. |

### Classification Principles

GhostTrace AI should follow these evidence-handling principles:

- A deletion request or deletion command alone does not prove that all relevant data has been removed.
- A successful event in one system does not automatically prove deletion in every relevant system.
- Missing evidence must not be treated as proof of successful deletion.
- Identity matches should be based on available evidence, not assumptions.
- `NOT_APPLICABLE` should be used only when the evidence supports that classification.
- When the evidence cannot establish completion, the result should reflect that uncertainty.
- Findings should distinguish verified facts from missing checks and recommended follow-up actions.

These principles describe the intended interpretation of the statuses. Actual classification behavior depends on the implementation and its evaluation results.

## 5. Input Data and Evidence

GhostTrace AI is intended to operate on the deletion-request dataset supplied with the challenge.

The original dataset contains deletion requests and supporting evidence. Depending on the case, this evidence may include identity mappings, service events, logs, deletion records, and verification artifacts.

The dataset directory is expected to be named:

```text
dataset/
```

The exact filenames and subdirectory layout must be taken from the supplied dataset and project instructions.

### Evidence Processing Workflow

For each case, the solution should:

1. Read the deletion request and its identifiers.
2. Locate evidence associated with the request.
3. Correlate records using reliable identifiers where possible.
4. Determine which deletion requirements are supported by the evidence.
5. Identify unresolved checks or missing evidence.
6. Assign a status consistent with the findings.
7. Record the findings in the required output format.

The assessment should not claim that a system was checked or a remediation was performed unless that claim is supported by the evidence and actual execution.

The original dataset is an input to the analysis and should not be included in the final code archive when prohibited by the challenge instructions.

## 6. Output Specification

The primary generated artifact is:

```text
output.csv
```

It must be written to the project root and contain the following columns in the specified order:

```csv
case_id,deletion_status,steps_json
```

### Column Descriptions

| Column | Description |
|---|---|
| `case_id` | Unique identifier for the deletion-request case. |
| `deletion_status` | One of `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`. |
| `steps_json` | A valid JSON array containing structured findings, verification details, and/or follow-up steps. |

### Illustrative Output Example

The following example demonstrates the required structure. It is not a result for an actual dataset case.

```csv
case_id,deletion_status,steps_json
case_example,INCOMPLETE,"[{""step"":""verification"",""finding"":""Required deletion evidence is unavailable"",""action"":""Verify the relevant storage system""}]"
```

The JSON array is stored inside a CSV field. Double quotes inside that field must be escaped according to CSV rules.

### Output Requirements

The generated file should:

- Include the required header exactly.
- Contain one result for every input case.
- Preserve case identifiers.
- Use only the permitted status values.
- Store valid JSON arrays in `steps_json`.
- Sort rows by `case_id` if required by the challenge specification.
- Avoid duplicate or missing cases.
- Be a real CSV file rather than an HTML page or renamed error response.

For the expected dataset of 518 cases, validate that the file contains 518 data rows in addition to the header.

## 7. Repository Structure

The repository may contain the following components, depending on the project version:

```text
GhostTrace-AI/
├── README.md
├── AGENTS.md
├── agent_trace_instructions.md
├── problem_statement.md
├── package.json
├── vite.config.ts
├── server.ts
├── src/
│   └── ... frontend application files ...
├── backend/
│   └── ... backend application files and tests ...
├── code/
│   ├── main.py
│   ├── __init__.py
│   └── evaluation/
│       ├── evaluation_report.md
│       └── usage_report.md
├── dataset/
│   └── ... input data and supporting evidence ...
├── output.csv
└── log.txt
```

This is a reference structure, not a verified inventory of every file in the current working copy.

### Important Files

- `README.md` — project overview, setup, execution, and submission instructions.
- `AGENTS.md` — repository-specific development or execution instructions.
- `agent_trace_instructions.md` — task-specific agent guidance.
- `problem_statement.md` — original challenge definition.
- `code/main.py` — Python processing entry point, if configured as the main processor.
- `code/evaluation/evaluation_report.md` — evaluation findings and actual test results.
- `code/evaluation/usage_report.md` — execution and usage documentation.
- `backend/` — backend service and tests, where included.
- `src/` — frontend application source, where included.
- `dataset/` — source data and evidence; normally excluded from the code archive.
- `output.csv` — generated result, submitted separately when required.
- `log.txt` — authentic development or agent transcript, submitted separately when required.

## 8. Requirements

### Python

Python is required to run the processing script.

Check the installed version:

```powershell
python --version
```

If Python is unavailable, install it and ensure it is accessible from PowerShell.

### Frontend and Backend

If you intend to run the dashboard or API, install the dependencies specified by the project configuration files.

For a Node.js-based frontend, check:

```powershell
node --version
npm --version
```

Use the package manager and commands documented by the actual repository. Not every project copy necessarily contains the same scripts or backend configuration.

## 9. Installation and Setup

### Step 1: Open the Project Directory

Navigate to the directory containing `README.md` and the `code/` folder.

For example:

```powershell
cd "D:\remix-ghost-trace-orchestrate"
```

Replace this path if the project is stored elsewhere.

### Step 2: Inspect the Project Files

```powershell
Get-ChildItem
Get-ChildItem .\code -Recurse -File
```

Confirm that the Python entry point exists:

```powershell
Test-Path .\code\main.py
```

If the script depends on the original dataset, verify that the expected dataset directory and files are also available.

### Step 3: Review the Challenge Instructions

Read the following files before executing the solution:

```text
AGENTS.md
agent_trace_instructions.md
problem_statement.md
```

These documents may define additional requirements for evidence interpretation, execution, evaluation, or submission.

### Step 4: Restore Required Input Data

If the dataset is missing from the current working directory, restore it from the original project copy or the authorized source.

Do not create placeholder evidence or fabricate dataset records to make the script run.

## 10. Running the Python Processor

From the project root, run:

```powershell
python .\code\main.py
```

If the script expects a different working directory, configuration, or dataset path, follow the implementation and repository instructions.

Check whether the output exists:

```powershell
Test-Path .\output.csv
```

Inspect the first few lines:

```powershell
Get-Content .\output.csv -TotalCount 5
```

The expected successful behavior is for the processor to write results to the configured output location. The existence of the file alone does not establish correctness; validate the contents before submission.

## 11. Running the Frontend and Backend

The frontend and backend are separate from the Python CSV-generation task unless the project explicitly integrates them.

### Frontend Setup

From the project root, install dependencies if needed:

```powershell
npm install
```

Inspect the configured scripts:

```powershell
Get-Content .\package.json
```

If the project defines a `dev` script, start it using:

```powershell
npm run dev
```

Open the local URL printed by the development server.

### Backend Setup

Inspect the `backend/` directory and its setup instructions before starting the API.

If the backend is Python-based and contains a requirements file, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies from the requirements file that actually exists in the repository.

If the backend exposes a health endpoint, test the endpoint documented by the application. Do not assume `/health` is implemented unless the source confirms it.

## 12. Testing and Validation

Testing should cover both the structure of the generated file and the correctness of the case-level assessments.

### Run the Test Suite

If the repository contains Python tests and `pytest` is installed, run:

```powershell
python -m pytest
```

Install missing dependencies using the repository's documented setup.

A passing test suite is useful evidence of correctness, but it does not independently prove that every deletion decision is accurate.

### Validate the CSV

Run the following PowerShell command from the project root. It checks the required columns, row count, permitted statuses, JSON syntax, uniqueness, and ordering.

```powershell
@'
import csv
import json
from pathlib import Path

path = Path("output.csv")
expected_columns = ["case_id", "deletion_status", "steps_json"]
allowed_statuses = {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}

if not path.is_file():
    raise SystemExit("ERROR: output.csv was not found.")

with path.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    if reader.fieldnames != expected_columns:
        raise SystemExit(
            f"ERROR: Expected columns {expected_columns}; "
            f"found {reader.fieldnames}"
        )

    rows = list(reader)

errors = []

if len(rows) != 518:
    errors.append(f"Expected 518 data rows; found {len(rows)}")

case_ids = [row["case_id"] for row in rows]

if any(not case_id for case_id in case_ids):
    errors.append("One or more rows have an empty case_id")

if len(case_ids) != len(set(case_ids)):
    errors.append("Duplicate case_id values were found")

if case_ids != sorted(case_ids):
    errors.append("Rows are not sorted by case_id")

for line_number, row in enumerate(rows, start=2):
    if row["deletion_status"] not in allowed_statuses:
        errors.append(
            f"Line {line_number}: invalid status "
            f"{row['deletion_status']!r}"
        )

    try:
        steps = json.loads(row["steps_json"])
        if not isinstance(steps, list):
            errors.append(
                f"Line {line_number}: steps_json is not a JSON array"
            )
    except (TypeError, json.JSONDecodeError) as exc:
        errors.append(
            f"Line {line_number}: invalid steps_json: {exc}"
        )

if errors:
    print("VALIDATION FAILED")
    for error in errors:
        print("-", error)
    raise SystemExit(1)

print("VALIDATION PASSED")
print(f"Rows checked: {len(rows)}")
print("CSV schema, statuses, JSON arrays, uniqueness, and ordering passed.")
'@ | python -
```

This validation assumes that the dataset contains 518 cases and that lexicographic ordering by `case_id` is required. Follow the official challenge specification if it defines different requirements.

### Review the Results

In addition to structural validation:

- Compare sample cases against supplied expected outputs or official tests.
- Check that each case has relevant evidence or a clear explanation of missing evidence.
- Review `COMPLETE` classifications carefully.
- Confirm that the status agrees with the associated JSON steps.
- Investigate unexpected empty step arrays.
- Ensure that the output does not claim unsupported deletion verification.

## 13. Evaluation Reports

The submission instructions require the following documentation files:

```text
code/evaluation/evaluation_report.md
code/evaluation/usage_report.md
```

### Evaluation Report

The `evaluation_report.md` file should document:

- Test commands and environment.
- Number of input cases processed.
- Structural validation results.
- Test pass/fail counts.
- Known mismatches and unresolved defects.
- Evaluation limitations.
- Whether results were checked against reference outputs.

Record actual results. Do not claim that tests passed unless they were run successfully.

### Usage Report

The `usage_report.md` file should document:

- The command used to execute the processor.
- Required runtime and dependencies.
- Input data required.
- Output files generated.
- Configuration requirements.
- Relevant execution limitations.

Include execution time or resource measurements only if they were actually recorded.

## 14. Submission Packaging

When required by the challenge, prepare the following artifacts separately:

| Artifact | Purpose |
|---|---|
| `output.csv` | Generated deletion-status results for the input cases. |
| `code.zip` | Runnable source code, required documentation, evaluation reports, and necessary configuration. |
| `log.txt` | Authentic chat or agent transcript, submitted using the required transcript field. |

Follow the official HackerRank upload fields and naming requirements.

### Create the Code Archive

First, confirm that the `code/` directory contains the required files, including both evaluation reports.

If the root README and `code/` directory are sufficient for your solution, create the archive with:

```powershell
Compress-Archive -Path .\README.md, .\code -DestinationPath .\code.zip -Force
```

This command includes only the root README and the `code/` directory. If the runnable solution depends on `backend/`, `src/`, `server.ts`, or root-level configuration files, include the necessary files when permitted by the submission rules.

Do not use this command blindly if the application requires additional files to run.

### Exclude Unnecessary Files

Do not include the dataset, virtual environments, dependency installation directories, build caches, or nested ZIP archives when prohibited by the challenge instructions.

Common examples include:

```text
dataset/
.venv/
venv/
node_modules/
__pycache__/
.pytest_cache/
dist/
build/
code.zip
```

List the contents of the archive after creating it:

```powershell
tar -tf .\code.zip
```

Verify that the archive contains the intended source code and documentation and does not accidentally include the dataset or temporary files.

### Transcript Integrity

The `log.txt` file should contain the actual conversation or agent transcript required by the challenge. Do not reconstruct or invent messages and present them as an original transcript.

## 15. Troubleshooting

### `output.csv` Was Not Generated

Check that:

1. You ran the script from the expected directory.
2. `code/main.py` exists.
3. The dataset is present at the path expected by the script.
4. Required Python dependencies are installed.
5. The terminal shows no execution errors.

### The Output Contains Fewer Than 518 Cases

Check whether input files are missing, parsing failed, or the script filters records. Compare the processed case identifiers against the original input dataset.

### `steps_json` Contains Invalid JSON

Ensure JSON is serialized using a JSON encoder rather than assembled through string concatenation. Then ensure CSV quoting is handled by a CSV writer.

### The Exported File Contains HTML Instead of CSV

A file ending in `.csv` is not necessarily a valid CSV file.

Inspect the first bytes or lines of the downloaded file. If it contains `<!DOCTYPE html>`, `<html>`, or an error page, the export flow may be downloading an HTML response instead of the actual CSV artifact.

The export handler should retrieve the real CSV output and verify the response content type and content before starting the download.

### Tests Fail

Read the assertion message and determine whether the failure is caused by an implementation defect, a missing dependency, incorrect input paths, or a mismatch between actual output and expected results.

Record unresolved failures in the evaluation report.

### The ZIP File Is Incomplete

List the archive contents and verify that all required runtime files, instructions, and evaluation reports are included.

If the application depends on files outside `code/`, include the necessary files or restructure the submission according to the official requirements.

## 16. Limitations

The reliability of GhostTrace AI's classifications depends on the completeness, accuracy, and correlation quality of the available evidence.

Potential limitations include:

- Missing logs or records may prevent a conclusive decision.
- A deletion event may show that an operation was attempted without proving that every copy was removed.
- Identity ambiguity can lead to incorrect case-to-record matching.
- Evidence from one subsystem may not cover every storage location.
- Automated classification may require review when evidence conflicts or remains inconclusive.
- Passing structural tests does not prove that every underlying deletion claim is true.

The output should be interpreted as an evidence-based assessment of the supplied case data, not as an independent guarantee that every physical or logical copy of a record has been destroyed.

## 17. Security and Data Handling

Deletion evidence can contain personal identifiers, account references, event metadata, or other sensitive information.

When handling project data:

- Keep the supplied dataset within the authorized project environment.
- Avoid placing personal information in public repositories or unnecessary logs.
- Do not commit secrets, credentials, access tokens, or private environment-specific configuration.
- Exclude prohibited input datasets from the submission archive.
- Preserve evidence identifiers when required for traceability while avoiding unnecessary disclosure of sensitive content.
- Follow the challenge's data-handling and submission rules.

## 18. Future Improvements

Potential improvements for GhostTrace AI include:

- More explicit evidence-to-requirement mapping.
- Stronger identity resolution with ambiguity handling.
- Automated checks for replicas, caches, backups, and downstream systems where evidence is available.
- More comprehensive comparisons against reference outputs.
- Better diagnostics for missing or conflicting evidence.
- Export validation to prevent HTML responses from being saved as CSV.
- Automated packaging checks for required submission files.
- Expanded evaluation coverage for edge cases and incomplete evidence.

These are potential enhancements and should not be interpreted as existing capabilities unless they have been implemented and tested.

## 19. Conclusion

GhostTrace AI provides a structured approach to analyzing data deletion requests and their associated evidence under the challenge **Ghost Data Still Exists**.

The project aims to make the distinction between verified completion, unresolved deletion, and non-applicable cases explicit through consistent status labels and machine-readable findings.

A reliable submission should include a runnable implementation, a correctly formatted and validated `output.csv`, evaluation and usage reports, and the required authentic transcript. Every assessment should remain grounded in the evidence available for its case.

---

**Project Name:** GhostTrace AI  
**Challenge:** Ghost Data Still Exists  
**Primary Output:** `output.csv`  
**Expected Case Count:** 518  
**Permitted Statuses:** `COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE`
