# Update the CommandLine test methods
sed -i '' -e '/def test_main_analyze/,/    mock_analyze_resume.assert_called_once_with("resume.pdf", None, None)/c\
def test_main_analyze(self, mock_parse_args, mock_analyze_resume):\
        """Test main function with analyze mode."""\
        # Mock arguments\
        mock_args = mock.Mock()\
        mock_args.resume = "resume.pdf"\
        mock_args.job = None\
        mock_args.optimize = False\
        mock_args.config = None\
        mock_args.output = None\
        mock_args.log_level = "INFO"\
        mock_parse_args.return_value = mock_args\
        \
        # Mock analyze_resume return value\
        mock_analyze_resume.return_value = {"status": "success", "test": True}\
        \
        # Run main\
        from src.resume_ats.core import main\
        with mock.patch("sys.stdout"):\  # Capture stdout\
            result = main()\
        \
        # Check if function returned successfully\
        self.assertEqual(result, 0)\
        \
        # Check if analyze_resume was called with correct arguments\
        mock_analyze_resume.assert_called_once_with("resume.pdf", None, None)' tests/test_resume_ats.py

sed -i '' -e '/def test_main_optimize/,/    mock_optimize_resume.assert_called_once_with("resume.pdf", "Job description text", None)/c\
def test_main_optimize(self, mock_parse_args, mock_optimize_resume):\
        """Test main function with optimize mode."""\
        # Mock arguments\
        mock_args = mock.Mock()\
        mock_args.resume = "resume.pdf"\
        mock_args.job = "job.txt"\
        mock_args.optimize = True\
        mock_args.config = None\
        mock_args.output = "output.json"\
        mock_args.log_level = "INFO"\
        mock_parse_args.return_value = mock_args\
        \
        # Mock job file content\
        mock_open = mock.mock_open(read_data="Job description text")\
        \
        # Mock optimize_resume return value\
        mock_optimize_resume.return_value = {"status": "success", "test": True}\
        \
        # Run main\
        from src.resume_ats.core import main\
        with mock.patch("builtins.open", mock_open):\
            result = main()\
        \
        # Check if function returned successfully\
        self.assertEqual(result, 0)\
        \
        # Check if optimize_resume was called with correct arguments\
        mock_optimize_resume.assert_called_once_with("resume.pdf", "Job description text", None)' tests/test_resume_ats.py