"""
Test cases based on real GeoServer documentation examples that were failing.

These tests create nested tables from actual GeoServer source files to ensure
the preprocessing works correctly on real-world content.
"""

import unittest
from mkdocs_translate.translate import detect_nested_tables, deindent_nested_table


class TestRealWorldExamplesFromGeoServer(unittest.TestCase):
    """Test cases extracted from actual GeoServer documentation failures."""

    def test_wicket_pages_definition_list_8_spaces(self):
        """
        Test case from: doc/en/developer/source/programming-guide/wicket-pages/index.rst
        
        A nested list-table inside a definition list item with 8-space indentation.
        The table shows Bootstrap sizing classes.
        
        Original HTML output shows: <!-- mkdocs-translate: removed 8 spaces indentation -->
        This confirms the preprocessing was expected to handle 8-space indent.
        """
        rst_content = """    Sizing
        Bootstrap uses mostly ``em`` and ``rem`` as sizing units.

        Some other sizing used to set the width of an element and its pixel equivalent:

        .. list-table::

           * - **Class**
             - **Size in em**
             - **Size in pixels** (approximately)
           * - ``*-5-em``
             - 5em
             - 100px
           * - ``*-20-em``
             - 20em
             - 325px
           * - ``*-25-em``
             - 25em
             - 400px
           * - ``*-30-em``
             - 30em
             - 600px

        Avoid requiring special knowledge from the user.
"""
        
        # Detect nested tables
        detections = detect_nested_tables(rst_content, "wicket-pages/index.rst")
        
        # Should find 1 table at 8 spaces indentation
        self.assertEqual(len(detections), 1, 
                        f"Expected 1 nested table, found {len(detections)}")
        
        start_line, end_line, indent_level = detections[0]
        self.assertEqual(indent_level, 8, 
                        f"Expected 8-space indent, got {indent_level}")
        
        # De-indent it
        deindented = deindent_nested_table(rst_content, detections, "wicket-pages/index.rst")
        
        # Verify de-indented content
        lines = deindented.split('\n')
        
        # The list-table directive should now be at column 0 (after removing 8 spaces)
        list_table_line = None
        for i, line in enumerate(lines):
            if '.. list-table::' in line:
                list_table_line = i
                break
        
        self.assertIsNotNone(list_table_line, "list-table directive not found after de-indentation")
        
        # The line should start with .. (no leading spaces for directive)
        self.assertTrue(lines[list_table_line].startswith('.. list-table::'),
                       f"De-indented directive has wrong indentation: '{lines[list_table_line]}'")
        
        # Check that the HTML comment was added
        self.assertIn('removed 8 spaces indentation', deindented,
                     "HTML comment about indentation removal not found")
    
    def test_geopkg_quickstart_numbered_list_3_spaces(self):
        """
        Test case from: doc/en/user/source/gettingstarted/geopkg-quickstart/index.rst
        
        A nested list-table inside a numbered list item with 3-space indentation.
        Shows workspace configuration fields.
        
        Original HTML output shows: <!-- mkdocs-translate: removed 3 spaces indentation -->
        """
        rst_content = """#. Configure the new workspace:

   .. list-table::
      :header-rows: 1 

      * - Field
        - Value
      * - Name:
        - :kbd:`tutorial`
      * - Namespace URI
        - :kbd:`http://localhost:8080/geoserver/tutorial`

   .. note:: A workspace name is an identifier describing your project.
   
#. Press the :guilabel:`Submit` button.
"""
        
        # Detect nested tables
        detections = detect_nested_tables(rst_content, "geopkg-quickstart/index.rst")
        
        # Should find 1 table at 3 spaces indentation
        self.assertEqual(len(detections), 1, 
                        f"Expected 1 nested table, found {len(detections)}")
        
        start_line, end_line, indent_level = detections[0]
        self.assertEqual(indent_level, 3, 
                        f"Expected 3-space indent, got {indent_level}")
        
        # De-indent it
        deindented = deindent_nested_table(rst_content, detections, "geopkg-quickstart/index.rst")
        
        # Verify de-indented content
        lines = deindented.split('\n')
        
        # The list-table directive should now be at column 0
        list_table_line = None
        for i, line in enumerate(lines):
            if '.. list-table::' in line:
                list_table_line = i
                break
        
        self.assertIsNotNone(list_table_line, "list-table directive not found after de-indentation")
        
        # The directive should start at column 0
        self.assertTrue(lines[list_table_line].startswith('.. list-table::'),
                       f"De-indented directive has wrong indentation: '{lines[list_table_line]}'")
        
        # Check that the HTML comment was added
        self.assertIn('removed 3 spaces indentation', deindented,
                     "HTML comment about indentation removal not found")
    
    def test_datadirectory_location_2_spaces(self):
        """
        Test case from: doc/en/user/source/datadirectory/location/index.rst
        
        A nested list-table with 3-space indentation inside bullet list items.
        
        Original HTML output shows: <!-- mkdocs-translate: removed 3 spaces indentation -->
        (appears 3 times in the file, so there are multiple 3-space indented tables)
        """
        rst_content = """* Platform Independent Binary: The data directory is located at example location.

   .. list-table::
      :header-rows: 1
      
      * - Platform
        - Default location
      * - Linux 
        - /usr/share/geoserver/data_dir
      * - Windows
        - C:\\Program Files\\GeoServer\\data_dir

   The windows location above is not ideal.
"""
        
        # Detect nested tables
        detections = detect_nested_tables(rst_content, "datadirectory/location.rst")
        
        # Should find 1 table at 3 spaces indentation (inside bullet list)
        self.assertEqual(len(detections), 1, 
                        f"Expected 1 nested table, found {len(detections)}")
        
        start_line, end_line, indent_level = detections[0]
        self.assertEqual(indent_level, 3, 
                        f"Expected 3-space indent, got {indent_level}")
        
        # De-indent it
        deindented = deindent_nested_table(rst_content, detections, "datadirectory/location.rst")
        
        # Verify the directive is de-indented
        lines = deindented.split('\n')
        
        # Find the list-table line
        list_table_line = None
        for i, line in enumerate(lines):
            if '.. list-table::' in line:
                list_table_line = i
                break
        
        self.assertIsNotNone(list_table_line, "list-table directive not found")
        
        # Should start at column 0
        self.assertTrue(lines[list_table_line].startswith('.. list-table::'),
                       f"De-indented directive not at column 0: '{lines[list_table_line]}'")
        
        # Check comment
        self.assertIn('removed 3 spaces indentation', deindented,
                     "HTML comment about indentation removal not found")
    
    def test_wicket_blank_line_after_table_removed(self):
        """
        Test that blank lines immediately after the table are removed to prevent 
        Pandoc definition list misinterpretation.
        
        Issue: If there's a blank line after the table, and we add a comment + blank line,
        we get double blank lines that break definition list syntax.
        
        Fix: Detect and remove the original blank line after the table.
        """
        rst_content = """    Sizing:
        Some intro.

        .. list-table::

           * - **Class**
             - **Size**
           * - ``*-30-em``
             - 30em

        Avoid requiring special knowledge from the user.
            For example, provide widgets.
"""
        
        # Detect and de-indent the nested table
        detections = detect_nested_tables(rst_content, "test.rst")
        self.assertEqual(len(detections), 1, "Should find 1 nested table")
        
        deindented = deindent_nested_table(rst_content, detections, "test.rst")
        lines = deindented.split('\n')
        
        # Find the comment line
        comment_line_idx = None
        for i, line in enumerate(lines):
            if 'mkdocs-translate: removed' in line:
                comment_line_idx = i
                break
        
        self.assertIsNotNone(comment_line_idx, "Comment not found")
        
        # The next line after comment should be blank (our separator)
        self.assertLess(comment_line_idx + 1, len(lines))
        self.assertEqual(lines[comment_line_idx + 1].strip(), '',
                        "Line immediately after comment should be blank")
        
        # The line after the blank line should be the indented content
        # (NOT another blank line)
        self.assertLess(comment_line_idx + 2, len(lines))
        next_content = lines[comment_line_idx + 2]
        # Should start with indentation and the text "Avoid"
        self.assertTrue(next_content.lstrip().startswith('Avoid'),
                       f"Expected content after comment, got: '{next_content}'")
        
        # Verify we don't have double blank lines
        double_blank_found = False
        for i in range(len(lines) - 1):
            if lines[i].strip() == '' and lines[i+1].strip() == '':
                double_blank_found = True
                break
        
        self.assertFalse(double_blank_found,
                        "Found double blank lines - original blank line after table not removed")


if __name__ == '__main__':
    unittest.main()
