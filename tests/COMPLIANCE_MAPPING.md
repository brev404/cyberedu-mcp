# Compliance Tests → Checklist Mapping

These tests verify the codebase adheres to documented requirements.
When updating checklists or rules, update the corresponding test.

## cyberedu-client/docs/extending.md — Checklist for New Endpoints

| Checklist Item | Test |
|----------------|------|
| Method has docstring with Args/Returns | `TestClientExtendingChecklist::test_public_methods_with_params_have_args_section` |
| Uses `_make_request()` or explains why not | (Manual review; pattern in extending.md) |
| Handles expected error codes (400 for wrong flags) | `TestClientExtendingChecklist::test_flag_submission_handles_400` |
| Returns dict (not custom objects) for MCP | `TestClientExtendingChecklist::test_public_methods_return_dict_or_bytes` |

## docs/extending.md — Checklist for New Tools

| Checklist Item | Test |
|----------------|------|
| Returns JSON-serializable dict | `TestCustomToolsChecklist::test_custom_tools_return_json_serializable` |
| Parameters schema has type/properties/required | `TestCustomToolsChecklist::test_custom_tools_have_required_schema` |

## docs/extending.md — Project Standards (Client Methods)

| Requirement | Test |
|-------------|------|
| Type hints on all parameters | `TestClientExtendingChecklist::test_client_methods_have_type_hints` |
| Return JSON-serializable Dict | `TestClientExtendingChecklist::test_public_methods_return_dict_or_bytes` |

## docs/extending.md — Security Requirements

| Requirement | Test |
|-------------|------|
| Never return session_cookie in get_session_status | `TestSessionStatusSecurity::test_get_session_status_never_returns_cookie_value` |
| 401/403: Do NOT include response body in error output | `test_server::TestHandleCallTool::test_http_401_returns_error_without_response_body` |

## docs/extending.md — Testing Changes

| Doc Instruction | Test |
|-----------------|------|
| `python list_tools.py` works | `TestDocInstructionsWork::test_list_tools_script_imports` |

## Running Compliance Tests

```bash
pytest tests/test_compliance.py -v
```

All tests must pass before merging changes that affect the documented behavior.
