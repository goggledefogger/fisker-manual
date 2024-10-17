# Fisker Ocean Manual Downloader

This project provides a Python script to download the publicly available Fisker Ocean Owner's Manual and convert it into a PDF file for offline reading.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You have installed Python 3.8
- You have a macOS machine (for Homebrew installation)

## Installing Fisker Ocean Manual Downloader

To install the Fisker Ocean Manual Downloader, follow these steps:

1. Clone the repository:

   ```
   git clone https://github.com/goggledefogger/fisker-manual.git
   cd fisker-manual
   ```

2. Install Homebrew if you haven't already:

   ```
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

3. Install the required system dependencies:

   ```
   brew install python
   ```

4. Create a virtual environment (optional but recommended):

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

5. Install the required Python packages:

   ```
   pip install -r requirements.txt
   ```

6. Install the Playwright browsers:
   ```
   playwright install
   ```

7. Install the WeasyPrint library:
   ```
   pip install weasyprint
   ```

8. Install the Pango library to resolve the error:
   ```
   brew install pango
   ```

## Using Fisker Ocean Manual Downloader

To use the Fisker Ocean Manual Downloader, follow these steps:

1. Ensure you're in the project directory and your virtual environment is activated (if you're using one)

2. Run the script:

   ```
   python download_manual.py
   ```

3. The script will open a browser, navigate through the manual, and create a PDF file named `fisker_ocean_manual.pdf` in the same directory

## Contributing to Fisker Ocean Manual Downloader

To contribute to Fisker Ocean Manual Downloader, follow these steps:

1. Fork this repository.
2. Create a branch: `git checkout -b <branch_name>`.
3. Make your changes and commit them: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create the pull request.

Alternatively, see the GitHub documentation on [creating a pull request](https://help.github.com/articles/creating-a-pull-request/)

## Acknowledgements

We extend our gratitude to Fisker Inc. for making the Ocean Owner's Manual publicly available online. This tool is designed to enhance accessibility to this public information for Fisker owners and enthusiasts.

Special thanks to the Fisker Owners Association (https://www.fiskeroa.com/) for fostering a community of Fisker enthusiasts and owners.

## Legal Note

This tool is intended for personal use only, to access publicly available information. Users should respect Fisker Inc.'s copyright and terms of service when using this tool and the resulting PDF.

## License

This project uses the MIT License - see the [LICENSE.md](LICENSE.md) file for details. In simple terms, this means you can do whatever you want with this code as long as you provide attribution back to us and don't hold us liable.

## Contact

If you want to contact me, you can reach me at `<dannybauman@gmail.com>`.
