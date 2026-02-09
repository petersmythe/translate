# Implementation Plan: Nested Table De-indentation Preprocessing

**Date:** February 9, 2026  
**Target Version:** 0.6.2  
**Status:** Approved - Ready for Implementation

## Problem Statement

RST `.. list-table::` directives that are indented (nested within numbered lists, admonitions, etc.) fail to convert properly to Markdown tables via Pandoc. The indentation causes Pandoc to misinterpret the table structure, resulting in malformed or missing tables in the final output.

**Example Issue:**
```rst
#. Step one:

   .. list-table::
      :widths: 30 70
      
      * - Name:
        - :kbd:`airport0`
      * - Workspace:
        - (none specified)
```

The 3-space indentation before `.. list-table::` prevents proper conversion.

## Solution Approach

**Strategy:** Preprocess RST files to detect indented list-tables, remove the indentation, and add hidden HTML comments documenting the transformation.

**Workflow:**
```
RST with indented tables 
  → Detect nested tables
  → Remove indentation  
  → Add documentation comment
  → Pandoc conversion
  → Markdown with proper pipe-tables
```

## Design Decisions (Approved)

1. **Scope:** Process only indented tables (indentation > 0 spaces)
   - Non-indented tables already render correctly
   
2. **Comment Placement:** After the table
   - Format: `<!-- mkdocs-translate: removed N spaces indentation -->`
   
3. **Processing Stage:** Preprocess RST before Pandoc conversion
   - RST → De-indented RST → Pandoc → Markdown
   
4. **Error Handling:** Log warning and **fail migration** if de-indentation fails
   - Ensures manual review of problematic tables
   
5. **File Scope:** Process **all files** during migration
   - Not limited to files in reports
   - Comprehensive solution

## Two Repository Context

**⚠️ CRITICAL:** We are working with TWO separate repositories:

1. **translate repo** (`d:\DATA\Projects\Geoserver\PSC\mkdocs-translate`)
   - The mkdocs-translate tool being modified
   - All code changes happen here
   - Current branch: `geoserver-minimal`
   - Last commit: `f4e1c22` "v0.6.1 increased logging"

2. **gs-vs repo** (`d:\DATA\Projects\Geoserver\ALL-SOURCE-CODE\gs-vs`)
   - GeoServer documentation being processed
   - Contains `reports/` folder with problematic file lists
   - NO CODE CHANGES HERE
   - Used only as test data source

## Implementation Phases

### Phase 1: Prepare Clean Branch ✅

**Objective:** Create new branch from last commit, preserve experimental work

**Steps:**
1. ✅ Confirm last clean commit: `f4e1c22`
2. Stash uncommitted changes with descriptive message
3. Create new branch: `nested-table-deindent`
4. Verify clean working tree

**Commands:**
```bash
cd mkdocs-translate
git stash push -m "WIP: list-table conversion experiments - preserving before nested-table-deindent work"
git checkout -b nested-table-deindent f4e1c22
git status  # verify clean
```

**Deliverable:** Clean branch ready for new implementation

---

### Phase 2: Implement Nested Table Detection

**File:** `mkdocs_translate/translate.py`

**New Function:**
```python
def detect_nested_tables(rst_content: str, file_path: str = None) -> List[Tuple[int, int, int]]:
    """
    Detect indented list-table directives in RST content.
    
    Args:
        rst_content: The RST file content as string
        file_path: Optional file path for logging
    
    Returns:
        List of (start_line, end_line, indent_level) tuples for each nested table
        Line numbers are 0-based
        
    Notes:
        - Only detects tables with indentation > 0
        - Skips tables inside literal code blocks (:: blocks)
        - Handles tabs (converted to 3 spaces)
    """
```

**Detection Logic:**
1. Scan line-by-line tracking code block state
2. When `.. list-table::` found:
   - Measure leading whitespace (indent_level)
   - If indent_level > 0: this is a nested table
   - Record start_line
3. Continue scanning while indentation >= indent_level
4. When dedent detected: record end_line
5. Skip if inside literal code block

**Edge Cases:**
- Mixed tabs/spaces (normalize tabs → 3 spaces)
- Code examples showing list-table syntax (inside `::`)
- Directive options (`:widths:`, `:header-rows:`, etc.)
- Empty lines within table (maintain indentation check)

**Logging:**
- DEBUG: Each detected table with location and indent
- INFO: Count of nested tables per file

---

### Phase 3: Implement Table De-indentation

**New Function:**
```python
def deindent_nested_table(rst_content: str, detections: List[Tuple[int, int, int]], 
                          file_path: str = None) -> str:
    """
    Remove indentation from detected nested list-tables and add documentation comments.
    
    Args:
        rst_content: Original RST content
        detections: List from detect_nested_tables()
        file_path: Optional file path for logging/error messages
    
    Returns:
        Modified RST content with de-indented tables
        
    Raises:
        ValueError: If de-indentation fails (malformed table structure)
        
    Notes:
        - Processes tables in reverse order (preserve line numbers)
        - Adds HTML comment after each table
        - Validates table structure before/after
    """
```

**De-indentation Logic:**
1. Process detections in reverse (end → start) to preserve line numbers
2. For each table:
   - Extract lines [start_line:end_line+1]
   - Remove indent_level spaces from each line
   - Validate: all lines had sufficient indentation
   - Create comment: `<!-- mkdocs-translate: removed {indent_level} spaces indentation -->`
   - Insert comment after table block
   - Replace original block with de-indented version

**Comment Format:**
```html
<!-- mkdocs-translate: removed 3 spaces indentation -->
```

**Validation:**
- Check each line has >= indent_level leading spaces
- If not: raise ValueError with line number
- Migration will fail with clear error message

**Error Messages:**
```
File {file_path}, line {line_num}: Cannot remove {indent_level} spaces - line only has {actual} spaces
```

---

### Phase 4: Integrate into Preprocessing Pipeline

**Location:** `preprocess_rst()` function in `translate.py`

**Integration Point:** After existing block directive preprocessing, before writing prep file

**Modified Function:**
```python
def preprocess_rst(rst_file: str, rst_prep: str) -> str:
    """
    Preprocess RST file before pandoc conversion.
    
    Existing preprocessing:
    - Block directives (figure, code-block, etc.)
    - Link resolution
    - etc.
    
    NEW: Nested table de-indentation
    """
    # ... existing preprocessing ...
    
    # De-indent nested list-tables for proper Pandoc conversion
    try:
        nested_tables = detect_nested_tables(text, rst_file)
        if nested_tables:
            logger.info(f"{rst_file}: Found {len(nested_tables)} nested table(s), de-indenting...")
            text = deindent_nested_table(text, nested_tables, rst_file)
    except ValueError as e:
        logger.error(f"{rst_file}: Failed to de-indent nested tables: {e}")
        raise  # Fail migration as approved
    
    # Write preprocessed file
    # ... rest of function ...
```

**Logging Strategy:**
- INFO: Count of nested tables found
- DEBUG: Details of each table location/indent
- ERROR: De-indentation failures with line numbers
- Migration aborts on error (approved behavior)

---

### Phase 5: Testing Strategy

**Test Files Location:** `mkdocs-translate/source/test_nested_*.rst`

**Test Suite:**

1. **`test_nested_table_simple.rst`**
   ```rst
   Test Simple Nested Table
   =========================
   
   Steps:
   
   #. First step:
   
      .. list-table::
         :widths: 30 70
         
         * - Name
           - Description
         * - Value
           - Details
   
   #. Second step
   ```
   **Expected:** Table de-indented by 3 spaces, comment added

2. **`test_nested_table_multiple.rst`**
   - 3 nested tables at different indents (3, 6, 4 spaces)
   **Expected:** All tables processed correctly

3. **`test_nested_table_deep.rst`**
   - Table inside admonition inside list (9+ spaces)
   **Expected:** Deep indentation handled

4. **`test_nested_table_code_example.rst`**
   ```rst
   Example usage::
   
      .. list-table::
         * - This is example code
   ```
   **Expected:** NOT processed (inside literal block)

5. **`test_nested_table_mixed_indent.rst`**
   - One indented, one non-indented in same file
   **Expected:** Only indented one processed

**Validation Process:**
```bash
# For each test file:
python -m mkdocs_translate migrate source/test_nested_*.rst

# Check output markdown
cat docs/test_nested_*.md

# Verify:
# - Tables rendered as pipe-tables
# - Comments present with correct indent values
# - Non-indented content unchanged
```

---

### Phase 6: Real-World Testing

**Data Source:** `gs-vs/reports/` folder

**Test Candidates:**
1. `doc/en/user/source/styling/workshop/css/css.rst`
   - Confirmed nested table at line 242 (3-space indent)
2. `doc/en/user/source/styling/workshop/css/polygon.rst`
3. `doc/en/user/source/styling/workshop/ysld/ysld.rst`
4. `doc/en/user/source/styling/workshop/mbstyle/mbstyle.rst`
5. `doc/en/docguide/source/sphinx.rst`
   - Nested table in code example (should skip)

**Testing Process:**
```bash
# Copy test files to translate repo
cp gs-vs/doc/en/user/source/styling/workshop/css/css.rst mkdocs-translate/source/

# Run migration
cd mkdocs-translate
python -m mkdocs_translate migrate source/css.rst

# Inspect output
cat docs/css.md | grep -A 20 "| Name"

# Check for comment
grep "mkdocs-translate: removed" docs/css.md

# Build and verify rendering (if mkdocs configured)
mkdocs build
# Open site/css/index.html and verify tables
```

**Success Criteria:**
- All nested tables convert to proper pipe-tables
- Comments document indentation removal
- Tables render correctly in HTML output
- No false positives (code examples unchanged)

---

### Phase 7: Documentation & Cleanup

**Files to Create/Update:**

1. **`NESTED_TABLE_FIX.md`** - Technical documentation
   ```markdown
   # Fix: Nested Table De-indentation Preprocessing
   
   ## Problem
   ## Solution  
   ## Implementation
   ## Testing Results
   ## Usage
   ```

2. **`CHANGES`** - Update changelog
   ```
   Version 0.6.2
   -------------
   
   - Added preprocessing to detect and de-indent nested list-tables
   - Nested tables now convert properly to Markdown pipe-tables
   - Added HTML comments documenting indentation removal
   - Migration fails with clear error if table structure is malformed
   ```

3. **`mkdocs_translate/__init__.py`** - Bump version
   ```python
   __version__ = "0.6.2"
   ```

4. **Unit Tests:** `tests/test_nested_tables.py`
   ```python
   class TestNestedTables(unittest.TestCase):
       def test_detect_simple_nested(self):
       def test_detect_multiple(self):
       def test_detect_skip_code_block(self):
       def test_deindent_simple(self):
       def test_deindent_error_insufficient_indent(self):
       def test_integration_preprocessing(self):
   ```

---

### Phase 8: Commit Strategy

**Branch:** `nested-table-deindent`

**Commits:**

1. Initial implementation:
   ```
   git commit -m "Add nested table detection and de-indentation preprocessing
   
   - Detect list-table directives with indentation > 0
   - Remove indentation to enable proper Pandoc conversion
   - Add HTML comments documenting transformation
   - Fail migration if de-indentation impossible"
   ```

2. Add tests:
   ```
   git commit -m "Add test suite for nested table preprocessing"
   ```

3. Update documentation:
   ```
   git commit -m "Document nested table fix and bump version to 0.6.2"
   ```

**Merge Strategy:**
- After testing: merge to `geoserver-minimal` branch
- Tag as `v0.6.2`
- Push to origin

---

## Success Metrics

**Functional:**
- ✅ All indented list-tables detected
- ✅ Indentation removed correctly
- ✅ Comments document transformation
- ✅ Tables render as proper pipe-tables
- ✅ Migration fails gracefully on errors

**Quality:**
- ✅ No false positives (code examples unchanged)
- ✅ All test files pass
- ✅ Real-world GeoServer files migrate successfully
- ✅ Unit tests achieve >90% coverage

**Documentation:**
- ✅ Implementation documented
- ✅ Testing results recorded
- ✅ Changelog updated
- ✅ Version bumped

---

## Risk Mitigation

**Risk:** Breaking existing functionality
- **Mitigation:** Only process indented tables, non-indented tables unchanged

**Risk:** False positives in code examples
- **Mitigation:** Skip literal code blocks (:: syntax)

**Risk:** Complex nested structures
- **Mitigation:** Fail migration with clear error, manual review

**Risk:** Lost experimental work
- **Mitigation:** Stash changes before branching, can recover later

---

## Timeline Estimate

- Phase 1 (Branch setup): 5 minutes
- Phase 2 (Detection): 30 minutes
- Phase 3 (De-indent): 30 minutes
- Phase 4 (Integration): 15 minutes
- Phase 5 (Test files): 30 minutes
- Phase 6 (Real-world test): 20 minutes
- Phase 7 (Documentation): 30 minutes
- Phase 8 (Commit/cleanup): 10 minutes

**Total:** ~3 hours

---

## Approval Status

**Approved by:** User  
**Date:** February 9, 2026  
**Authorization:** Proceed with implementation

**Approved Design Decisions:**
1. ✅ Process only indented tables (indent > 0)
2. ✅ Comment after table
3. ✅ Preprocess RST before Pandoc
4. ✅ Fail migration on de-indentation errors
5. ✅ Process all files

**Ready to Execute:** YES

---

## Notes

- Track progress in this file (update phase completion)
- Log any deviations from plan
- Document unexpected issues encountered
- Record any additional test cases needed

**Next Step:** Execute Phase 1 - Prepare Clean Branch
