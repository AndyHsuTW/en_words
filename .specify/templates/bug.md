# 🐞 Bug Specification Template

## 🧾 Bug Summary
**Title**: {{title}}
**Reported Version**: {{version}}
**Environment**: {{environment}}
**Date Reported**: {{date}}
**Reported By**: {{reporter}}

---

## 🧩 Description
{{description}}

---

## 🔁 Steps to Reproduce
1. {{step_1}}
2. {{step_2}}
3. {{step_3}}

---

## ✅ Expected Behavior
{{expected_behavior}}

---

## ❌ Actual Behavior
{{actual_behavior}}

---

## 📊 Impact Assessment
- **Severity**: {{severity}} (Critical / High / Medium / Low)
- **Frequency**: {{frequency}} (Always / Intermittent / Rare)
- **Affected Modules**: {{affected_modules}}
- **Regression Introduced By**: {{source_commit_or_feature}}

---

## 🧠 Root Cause Analysis (optional)
{{root_cause}}

---

## 🔧 Proposed Fix
- {{fix_strategy}}
- {{test_strategy}}
- {{acceptance_criteria}}

---

## 🧪 Test Cases
| Case ID | Description | Expected Result |
|----------|--------------|-----------------|
| TC-1 | {{test_case_1}} | {{expected_result_1}} |
| TC-2 | {{test_case_2}} | {{expected_result_2}} |

---

## 🔄 Dependencies
- Related Spec: {{related_spec}}
- Related Plan: {{related_plan}}
- Related Task: {{related_task}}

---

## 🏁 Status
| Field | Value |
|-------|--------|
| Assigned To | {{assignee}} |
| Fix Version | {{fix_version}} |
| Status | {{status}} (Open / In Progress / Fixed / Verified / Closed) |
| QA Verified By | {{qa_tester}} |

---

> 🪶 **Notes**
> - 本文件由 `/specify bug:` 自動生成。  
> - 修正完成後請執行 `/plan` → `/tasks` → `/implement`。  
> - 驗證後可新增 `/specify review:` 文件進行回歸報告。