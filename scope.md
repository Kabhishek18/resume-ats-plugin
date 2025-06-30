# 📘 ATS Resume Scoring Plugin - Scope

A Python-based plugin to score resumes based on ATS standards, match them against job descriptions, and provide actionable feedback to improve job matching performance.

---

## 🔍 Features & Modules

### 1. 📄 Resume Parsing Module

**Functionality:**

- Accept resumes in `.pdf`, `.docx`, or `.txt` format.
- Parse content using native Python libraries:
  - `python-docx` for `.docx`
  - `pdfminer.six` or `PyMuPDF` for `.pdf`
  - Plain text handling for `.txt`

**Optional Integration:**
 -  Provides structured JSON output with:
  - Contact information
  - Skills
  - Education
  - Experience
  - Certifications, etc.

---

### 2. 📑 Job Description Matching Module

**Functionality:**

- Accepts raw job descriptions (JD)
- Extracts critical elements using NLP:
  - **Skills**
  - **Roles and Responsibilities**
  - **Educational Requirements**
  - **Job Titles**
  - **Experience Requirements**
- Compares JD features with parsed resume data

**Tools/Tech:**
- `spaCy` / `BERT/SBERT`
- Custom keyword matching

---

### 3. 🧠 ATS Scoring Engine

| Feature                  | Description                             | Weight |
|--------------------------|-----------------------------------------|--------|
| **Keyword Match**        | Skill & responsibility overlap          | 30%    |
| **Title Match**          | Alignment of candidate's title          | 10%    |
| **Education Match**      | Degree/qualification comparison         | 10%    |
| **Experience Match**     | Relevant years and domain experience    | 15%    |
| **Format Compliance**    | Proper layout, sections, contact info   | 15%    |
| **Action Verbs & Grammar**| Usage of active language & correctness | 10%    |
| **Readability**          | Structure, tone, section clarity        | 10%    |

**Total Score:** 100 points

---

### 4. 📊 Scoring Report Generator

**Outputs:**

- **Total ATS Score** (out of 100)
- **Detailed Sectional Breakdown**
- **Improvement Recommendations**:
  - Missing technical/non-technical keywords
  - Formatting inconsistencies
  - Inadequate use of action verbs
  - Grammar or spelling issues
  - Role or experience misalignment

---

### 5. 🛠 Enhancement Suggestions Engine

**Enhancement Areas:**

- Add or emphasize missing skills and keywords
- Rephrase sentences using action verbs
- Improve formatting and structure
- Add missing sections (contact info, summary, etc.)
- Improve grammar and remove filler language

**Tools (Optional):**
- `LanguageTool` or `Grammarly` API for grammar checking

---

### 6. 🔧 CLI + API Access

#### CLI Tool

```bash
ats-score --resume resume.pdf --jd jd.txt
```