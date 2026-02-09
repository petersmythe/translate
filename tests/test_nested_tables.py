"""
Unit tests for nested table de-indentation preprocessing.

Tests the detect_nested_tables() and deindent_nested_table() functions
in mkdocs_translate/translate.py
"""
import unittest
from mkdocs_translate.translate import detect_nested_tables, deindent_nested_table


class TestDetectNestedTables(unittest.TestCase):
    """Tests for detect_nested_tables() function."""

    def test_detect_single_table(self):
        """Test detection of a single indented table."""
        rst_content = """Some text:

   .. list-table::
      :widths: 30 70
      
      * - Name
        - Value
      * - Test
        - Table
        
More text."""
        
        detections = detect_nested_tables(rst_content)
        
        # Should find exactly 1 table
        self.assertEqual(len(detections), 1)
        
        # Check detection tuple (start_line, end_line, indent_level)
        start, end, indent = detections[0]
        self.assertEqual(indent, 3)  # 3-space indentation
        self.assertGreater(end, start)  # End line after start line

    def test_detect_multiple_tables(self):
        """Test detection of multiple indented tables."""
        rst_content = """List with tables:

   .. list-table::
      
      * - Name
        - Value

#. Second item:

      .. list-table::
         
         * - A
           - B

Final:

    .. list-table::
       
       * - X
         - Y
"""
        
        detections = detect_nested_tables(rst_content)
        
        # Should find 3 tables
        self.assertEqual(len(detections), 3)
        
        # Check indentation levels
        indents = [d[2] for d in detections]
        self.assertEqual(indents, [3, 6, 4])

    def test_skip_non_indented_table(self):
        """Test that non-indented tables are not detected."""
        rst_content = """.. list-table::
   :widths: 30 70
   
   * - Name
     - Value
   * - Test
     - Table
"""
        
        detections = detect_nested_tables(rst_content)
        
        # Should find 0 tables (not indented)
        self.assertEqual(len(detections), 0)

    def test_skip_table_in_code_block(self):
        """Test that list-tables in code blocks are not detected."""
        rst_content = """Example::

   Some code
   
   .. list-table::
      
      * - Name
        - Value

Normal content."""
        
        detections = detect_nested_tables(rst_content)
        
        # Should find 0 tables (inside code block)
        self.assertEqual(len(detections), 0)

    def test_detect_deep_nesting(self):
        """Test detection of deeply nested tables (in admonitions in lists)."""
        rst_content = """#. Step one:

   .. note::
   
      Important information:
      
      .. list-table::
         :widths: 50 50
         
         * - Column 1
           - Column 2
         * - Data A
           - Data B
"""
        
        detections = detect_nested_tables(rst_content)
        
        # Should find exactly 1 table (inside note inside list)
        self.assertEqual(len(detections), 1)
        
        # Should be at 6 spaces indent (2 for list + 3 for note)
        self.assertEqual(detections[0][2], 6)

    def test_mixed_indented_and_non_indented(self):
        """Test with mix of indented and non-indented tables."""
        rst_content = """Non-indented table:

.. list-table::
   
   * - A
     - B

Indented table in list:

#. Item with table:

   .. list-table::
      
      * - X
        - Y

Another non-indented:

.. list-table::
   
   * - P
     - Q
"""
        
        detections = detect_nested_tables(rst_content)
        
        # Should find exactly 1 table (only the indented one)
        self.assertEqual(len(detections), 1)

    def test_empty_content(self):
        """Test with empty content."""
        detections = detect_nested_tables("")
        self.assertEqual(len(detections), 0)

    def test_content_without_tables(self):
        """Test content without any tables."""
        rst_content = """This is just regular RST content.

   Some indented text without tables.
   
   More content."""
        
        detections = detect_nested_tables(rst_content)
        self.assertEqual(len(detections), 0)


class TestDeindentNestedTable(unittest.TestCase):
    """Tests for deindent_nested_table() function."""

    def test_deindent_single_table(self):
        """Test de-indentation of a single table."""
        rst_content = """Some text:

   .. list-table::
      
      * - Name
        - Value
        
More text."""
        
        detections = detect_nested_tables(rst_content)
        result = deindent_nested_table(rst_content, detections)
        
        # Check that result contains de-indented directive
        self.assertIn(".. list-table::", result)
        
        # Check that comment is inserted
        self.assertIn("<!-- mkdocs-translate: removed 3 spaces indentation -->", result)
        
        # Check that indentation is removed from first content line
        lines = result.split('\n')
        for i, line in enumerate(lines):
            if '.. list-table::' in line:
                # This line and following should not be indented
                self.assertFalse(lines[i].startswith('   '))
                break

    def test_deindent_multiple_tables(self):
        """Test de-indentation of multiple tables."""
        rst_content = """List:

   .. list-table::
      
      * - A
        - B

#. Item:

      .. list-table::
         
         * - X
           - Y

End:

    .. list-table::
       
       * - P
         - Q
"""
        
        detections = detect_nested_tables(rst_content)
        result = deindent_nested_table(rst_content, detections)
        
        # Should have 3 HTML comments (one per table)
        comment_count = result.count("<!-- mkdocs-translate: removed")
        self.assertEqual(comment_count, 3)
        
        # Check specific indentation values in comments
        self.assertIn("removed 3 spaces", result)  # First table
        self.assertIn("removed 6 spaces", result)  # Second table
        self.assertIn("removed 4 spaces", result)  # Third table

    def test_deindent_preserves_non_indented(self):
        """Test that non-indented tables are not affected."""
        rst_content = """.. list-table::
   
   * - A
     - B

Text with indented table:

   .. list-table::
      
      * - X
        - Y
"""
        
        detections = detect_nested_tables(rst_content)
        result = deindent_nested_table(rst_content, detections)
        
        # Should have exactly 1 comment (only indented table processed)
        comment_count = result.count("<!-- mkdocs-translate: removed")
        self.assertEqual(comment_count, 1)
        
        # First table should be unchanged
        self.assertIn("\n.. list-table::\n", result)

    def test_deindent_comment_placement(self):
        """Test that HTML comment is placed after table."""
        rst_content = """#. Step:

   .. list-table::
      :widths: 50 50
      
      * - A
        - B
      * - C
        - D

Next paragraph."""
        
        detections = detect_nested_tables(rst_content)
        result = deindent_nested_table(rst_content, detections)
        
        # Comment should appear after the table rows
        comment_pos = result.find("<!-- mkdocs-translate: removed")
        table_start = result.find(".. list-table::")
        last_row = result.rfind("* - C")
        
        # Comment should be after table content
        self.assertGreater(comment_pos, last_row)

    def test_validation_error_insufficient_indent(self):
        """Test that ValueError is raised for invalid indentation."""
        rst_content = """#. Step:

   .. list-table::
      :widths: 50 50
      
      * - A
        - B
      * - C
        - D

More text."""
        
        # Manually create a detection that expects 6-space indent
        # but lines only have 3 spaces (will fail validation)
        detections = [(2, 9, 6)]  # Expect 6-space indent but lines have 3
        
        # Should raise ValueError due to insufficient indentation
        with self.assertRaises(ValueError):
            deindent_nested_table(rst_content, detections)

    def test_integration_detect_and_deindent(self):
        """Integration test: detect and de-indent in one flow."""
        rst_content = """Documentation:

#. First step:

   .. list-table::
      :widths: 25 75
      
      * - Option
        - Description
      * - :kbd:`key1`
        - First option
      * - :kbd:`key2`
        - Second option

#. Second step with another table:

   .. list-table::
      
      * - X
        - Y

End."""
        
        # Detect
        detections = detect_nested_tables(rst_content)
        self.assertEqual(len(detections), 2)
        
        # De-indent
        result = deindent_nested_table(rst_content, detections)
        
        # Verify structure
        self.assertIn(".. list-table::", result)
        self.assertIn(":widths: 25 75", result)
        self.assertIn(":kbd:`key1`", result)
        
        # Verify comments
        comment_count = result.count("<!-- mkdocs-translate: removed")
        self.assertEqual(comment_count, 2)


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and special scenarios."""

    def test_table_with_tab_indentation(self):
        """Test handling of tab indentation."""
        rst_content = "\t.. list-table::\n\t\t* - A\n\t\t  - B"
        
        detections = detect_nested_tables(rst_content)
        
        # Should detect table (tabs normalized to spaces)
        self.assertEqual(len(detections), 1)

    def test_table_with_mixed_indentation(self):
        """Test handling of mixed spaces and content."""
        rst_content = """List:

   .. list-table::
      :header-rows: 1
      
      * - Header 1
        - Header 2
      * - Row 1 A
        - Row 1 B
      * - Row 2 A
        - Row 2 B

Paragraph."""
        
        detections = detect_nested_tables(rst_content)
        result = deindent_nested_table(rst_content, detections)
        
        # Check structure is preserved
        self.assertIn(":header-rows: 1", result)
        self.assertIn("Header 1", result)

    def test_consecutive_tables(self):
        """Test processing of two consecutive indented tables."""
        rst_content = """#. Item 1:

   .. list-table::
      
      * - A
        - B

   .. list-table::
      
      * - X
        - Y

End."""
        
        detections = detect_nested_tables(rst_content)
        
        # Second table is not indented (at same level as preceding blank line after first table)
        # Only the first table is truly indented
        self.assertEqual(len(detections), 1)
        
        result = deindent_nested_table(rst_content, detections)
        
        # First table should be de-indented with comment
        self.assertEqual(result.count("<!-- mkdocs-translate: removed"), 1)


if __name__ == '__main__':
    unittest.main()
