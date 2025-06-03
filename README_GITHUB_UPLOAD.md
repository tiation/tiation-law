# Uploading Sentiment Analysis Project to GitHub

This guide will walk you through the process of installing Git, setting up your repository, and uploading your sentiment analysis project to GitHub.

## 1. Install Git for Windows

1. The download for Git should have started in your browser. If not, visit: https://git-scm.com/download/win
2. Run the downloaded installer (e.g., `Git-2.41.0-64-bit.exe`)
3. Installation options:
   - Accept the license agreement
   - Choose installation location (default is fine)
   - Select components (recommended defaults)
   - Choose the default editor (Notepad is simplest for beginners)
   - For "Adjusting the name of the initial branch," select "Override the default branch name" and use "main"
   - For PATH environment, select "Git from the command line and also from 3rd-party software"
   - For HTTPS transport, select "Use the OpenSSL library"
   - For line ending conversions, select "Checkout Windows-style, commit Unix-style line endings"
   - For terminal emulator, select "Use MinTTY"
   - For git pull, select "Default (fast-forward or merge)"
   - For credential helper, select "Git Credential Manager"
   - Accept the remaining default options and complete the installation

4. After installation, restart your PowerShell window to ensure Git is recognized in your PATH

## 2. Configure Your Git Repository

1. Open PowerShell and navigate to your project directory (you're already in the correct directory if you see this file):
   ```
   cd "C:\Users\admin\Documents\sentiment_analysis"
   ```

2. Verify Git is installed:
   ```
   git --version
   ```

3. Initialize a new Git repository:
   ```
   git init
   ```

4. Set your Git identity (replace with your actual information):
   ```
   git config user.name "Your Name"
   git config user.email "your.email@example.com"
   ```

## 3. Prepare Your Files for GitHub

1. A `.gitignore` file has already been created for you to exclude sensitive and unnecessary files

2. Review the contents of the `.gitignore` file:
   ```
   type .gitignore
   ```

3. Add all your project files to Git staging:
   ```
   git add .
   ```

4. Commit your changes:
   ```
   git commit -m "Initial commit of sentiment analysis project"
   ```

## 4. Connect to GitHub

1. In your web browser, sign in to your GitHub account at https://github.com/

2. Navigate to the repository: https://github.com/tiation/Law

3. You need to generate a Personal Access Token (PAT) for authentication:
   - Click your profile photo in the top right
   - Go to Settings > Developer settings > Personal access tokens > Tokens (classic)
   - Click "Generate new token"
   - Give it a descriptive name like "Sentiment Analysis Upload"
   - Select scopes: at minimum, select "repo" for full repository access
   - Click "Generate token"
   - **IMPORTANT**: Copy the token immediately and save it somewhere secure - you won't be able to see it again!

4. In PowerShell, add the remote repository:
   ```
   git remote add origin https://github.com/tiation/Law.git
   ```

5. Verify the remote was added:
   ```
   git remote -v
   ```

## 5. Push Your Code to GitHub

1. If you're uploading to a subdirectory called "Messages" in the main branch, you have two options:

   **Option A**: Create the directory structure locally first:
   ```
   mkdir -p Messages
   git add .
   git commit -m "Create Messages directory"
   git push -u origin main
   ```

   **Option B**: Push to the main branch and then use GitHub's web interface to create the directory:
   ```
   git push -u origin main
   ```
   Then visit the repository on GitHub, click "Add file" > "Upload files", and choose "Messages/" as the target directory.

2. When prompted for credentials:
   - For username: enter your GitHub username
   - For password: use the Personal Access Token you generated earlier (not your GitHub password)

3. If you encounter authentication issues, you can store your credentials:
   ```
   git config credential.helper store
   ```
   Then try pushing again.

## 6. Verify Your Upload

1. After pushing, visit https://github.com/tiation/Law in your web browser
2. Navigate to the "Messages" directory (if applicable)
3. Confirm that your files appear in the repository
4. Double-check that sensitive data (like .env files and logs) are not visible in the repository

## Troubleshooting

- If Git commands aren't recognized after installation, restart your PowerShell terminal
- If you see "fatal: remote origin already exists" when adding the remote, use:
  ```
  git remote remove origin
  ```
  Then try adding the remote again

- If you encounter authentication issues, make sure you're using the Personal Access Token as your password
- If you need help with the GitHub interface, refer to GitHub's documentation: https://docs.github.com/

## Additional Resources

- GitHub Documentation: https://docs.github.com/
- Git Documentation: https://git-scm.com/doc

