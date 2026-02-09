# Nested Table De-indentation Preprocessing

**Version:** 0.6.2  
**Date:** February 9, 2026  
**Status:** Implemented and Tested

## Executive Summary

This document describes the nested table de-indentation preprocessing feature added to mkdocs-translate. The feature automatically detects and fixes indented RST `.. list-table::` directives that fail to convert properly through Pandoc, ensuring clean table rendering in final Markdown output.

## Problem Description

### Symptom
RST documentation containing `.. list-table::` directives indented within numbered lists, admonitions, or other block structures fail to convert to proper Markdown tables via Pandoc. The indentation causes Pandoc's parser to misinterpret the table structure.

### Example Issue
```rst
#. Step one:

   .. list-table::
      :widths: 30 70
      
      * - Name:
        - :kbd:`airport0`
      * - Workspace:
        - (none specified)
```

The 3-space indentation prevents proper table parsing.

### Root Cause
Pandoc's RST parser expects list-table directives at the document root (unindented) or within specific contexts. Indentation from nesting in lists/admonitions confuses the parser, treating the entire table as literal text or breaking the structure entirely.

## Solution Architecture

### Strategy
Preprocess RST content before Pandoc conversion to detect indented tables, remove their indentation, and document the transformation with HTML comments.

### Processing Pipeline
```
Input RST File
    ↓
[Preprocessing - De-indent Nested Tables] ← NEW STEP
    ↓
[Existing Pandoc Conversion]
    ↓
Output Markdown
```

### Key Design Decisions

1. **Processing Stage:** Before Pandoc conversion
   - Removes structural issues before they reach Pandoc
   - Preserves RST semantics

2. **Scope:** Process ONLY indented list-tables (indent > 0)
   - Non-indented tables already render correctly
   - Reduces false positives

3. **Documentation:** Insert HTML comments after tables
   - Format: `<!-- mkdocs-translate: removed N spaces indentation -->`
   - Provides transparency for manual review

4. **Error Handling:** Fail migration on de-indentation errors
   - Ensures problematic tables receive manual attention
   - Prevents silent corruption

5. **Coverage:** Process ALL files during migration
   - Not limited to specific file lists or known problem files
   - Comprehensive solution for any nested tables

## Implementation Details

### File: `mkdocs_translate/translate.py`

#### Function 1: `detect_nested_tables()`
```python
def detect_nested_tables(rst_content: str, file_path: str = None) -> List[Tuple[int, int, int]]:
    """
    Detect indented list-table directives in RST content.
    
    Args:
        rst_content: RST file content as string
        file_path: Optional file path for logging
    
    Returns:
        List of tuples: (start_line, end_line, indent_level)
        - start_line/end_line: 0-based line numbers (inclusive)
        - indent_level: Number of spaces of indentation
    """
```

**Algorithm:**
1. Split content into lines
2. Track code block state (literal blocks marked by ending `::`)
3. For each line:
   - Skip lines inside code blocks
   - Skip empty and comment lines
   - Check if line is a directive (starts with `..` after whitespace)
   - If directive is `.. list-table::` with indentation > 0, mark start
   - Track indentation level
4. Find table end (next non-indented non-empty line after directive)
5. Return list of detected tables with line numbers and indentation

**False Positive Prevention:**
- Check for `.. list-table::` BEFORE general `::` check (list-table includes `::`)
- Exclude directive lines from code block tracking (directives start with `..`)
- Skip lines inside literal code blocks

#### Function 2: `deindent_nested_table()`
```python
def deindent_nested_table(rst_content: str, detections: List[Tuple[int, int, int]], 
                          file_path: str = None) -> str:
    """
    Remove indentation from detected nested list-tables.
    
    Args:
        rst_content: Original RST content
        detections: List from detect_nested_tables()
        file_path: Optional file path for error reporting
    
    Returns:
        Modified RST with de-indented tables and documentation comments
        
    Raises:
        ValueError: If a line lacks sufficient indentation (validation failure)
    """
```

**Algorithm:**
1. Split content into lines
2. **Process detections in REVERSE order** (preserves line numbers during modification)
3. For each detection:
   - Validate all lines in table have sufficient indentation
   - Remove exactly `indent_level` spaces from start of each line
   - Insert HTML comment after table: `<!-- mkdocs-translate: removed N spaces indentation -->`
4. Join lines and return modified content

**Validation:**
- Checks each line starts with at least `indent_level` spaces
- Raises `ValueError` with context (file, line number, content) on failure
- Failure causes migration to stop (as designed)

#### Integration: `preprocess_rst()`
De-indentation integrated as the **first preprocessing step**:
```python
def preprocess_rst(rst_file: str, rst_prep: str) -> str:
    # ... load file ...
    
    # NEW: De-indent nested tables (must be FIRST)
    try:
        nested_detections = detect_nested_tables(rst_content, rst_file)
        if nested_detections:
            logging.info(f"{rst_file}: Found {len(nested_detections)} nested table(s)")
            rst_content = deindent_nested_table(rst_content, nested_detections, rst_file)
            logging.info(f"{rst_file}: De-indented {len(nested_detections)} nested table(s)")
    except ValueError as e:
        logging.error(str(e))
        raise
    
    # ... continue with existing preprocessing ...
```

## Testing Results

### Test Coverage
All test cases created and verified to pass:

| Test Case | Scenario | Result |
|-----------|----------|--------|
| **test_nested_table_simple.rst** | Single 3-space indented table in list | ✅ PASS |
| **test_nested_table_multiple.rst** | 3 tables at different indents (3, 6, 4 spaces) | ✅ PASS |
| **test_nested_table_deep.rst** | Deep nesting in admonition inside list (6+ spaces) | ✅ PASS |
| **test_nested_table_mixed.rst** | Mix of indented and non-indented tables | ✅ PASS |
| **test_nested_table_code_example.rst** | List-table in code block (should skip) | ✅ PASS |
| **test_non_indented_table.rst** | Baseline non-indented table (no processing) | ✅ PASS |

### Real-World Testing
✅ **gs-vs/doc/en/user/source/styling/workshop/css/css.rst**
- File size: Large realistic documentation
- Nested tables found: 1 (at line 242)
- De-indentation: Success
- Migration result: Complete Markdown file generated

### Test Metrics
- **Detection Accuracy:** 100% (all indented tables found, no false positives)
- **De-indentation Success:** 100% (all tables processed without validation errors)
- **Comment Insertion:** 100% (all comments present with correct indentation values)
- **False Positive Rate:** 0% (code examples correctly avoided)

## Known Behaviors

### What Gets Fixed
- ✅ Single indented list-tables
- ✅ Multiple nested tables in same file
- ✅ Deep nesting (admonitions containing lists with tables)
- ✅ Mixed files (some indented, some not)
- ✅ Various indentation levels (3, 4, 6+ spaces)

### What Doesn't Get Processed (Correct)
- ❌ Non-indented tables (already work in Pandoc)
- ❌ List-tables inside literal code blocks (preserved as examples)
- ❌ Tables already formatted with proper indentation context

## Migration Workflow

When user runs `mkdocs-translate migrate`:

1. **Detection Phase** (Pre-Pandoc)
   - Scans RST file for indented `.. list-table::` directives
   - Logs: `INFO: file.rst: Found N nested table(s)`

2. **De-indentation Phase** (Pre-Pandoc)
   - Removes indentation from detected tables
   - Adds documentation comments
   - Logs: `INFO: file.rst: De-indented N nested table(s)`

3. **Pandoc Conversion** (Existing)
   - Processes de-indented RST normally
   - Tables now parse correctly

4. **Output** (Existing)
   - Markdown file with proper pipe-tables
   - HTML comments document transformation

## Backward Compatibility

- ✅ **No breaking changes** - Non-indented tables unchanged
- ✅ **Graceful degradation** - Fails with clear error message (as designed)
- ✅ **Hidden transformation** - HTML comments visible only in processed file
- ✅ **Reversible** - Comments indicate exactly how much indentation was removed

## Future Improvements

1. **Configuration:** Allow disabling by file pattern
   - Usefulness: Skip files that have been pre-processed
   - Implementation: Add `exclude_patterns` to config

2. **Statistics:** Track de-indentation across all files
   - Usefulness: Report on how many tables fixed
   - Implementation: Accumulate counts in migration summary

3. **Strict Mode:** Validate table structure after de-indentation
   - Usefulness: Catch malformed tables before Pandoc
   - Implementation: Parse table structure, validate alignment markers

4. **Custom CSS:** Generate class markers for de-indented tables
   - Usefulness: Apply special styling to formerly-nested tables
   - Implementation: Add `{: .nested-table }` markers

## Troubleshooting

### Migration Fails with ValueError
**Symptom:** `ValueError: Line X in file.rst lacks sufficient indentation`

**Cause:** Table structure is different from expected (mixed indentation, partial indent removal)

**Resolution:**
1. Examine file at indicated line
2. Check table indentation is consistent
3. Report issue if file structure is valid

### Tables Still Don't Render
**Symptom:** Tables missing or malformed in final Markdown

**Cause:** De-indentation removed too much or too little; Pandoc issue unrelated to indentation

**Resolution:**
1. Check HTML comment in preprocessed file
2. Verify comment shows correct indentation value
3. Check final Markdown pipe-table format (`| --- |`)
4. Report for manual review

## References

- **RST Specification:** https://docutils.sourceforge.io/docs/user/rst/quickref.html#lists-and-quote-like-blocks
- **Pandoc RST Support:** https://pandoc.org/MANUAL.html#extension-definition_lists
- **GeoServer Documentation:** gs-vs repository, doc/en/ and doc/zhCN/ folders

## Version Information

- **Feature Added:** Version 0.6.2
- **Branch:** `nested-table-deindent`
- **Implementation Commit:** `439505b`
- **Files Modified:** `mkdocs_translate/translate.py` (158 insertions)

---

**Last Updated:** February 9, 2026  
**Status:** Ready for Production
