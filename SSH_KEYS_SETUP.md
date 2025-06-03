# Setting Up SSH Keys for GitHub on Windows

This guide will walk you through the process of generating SSH keys and configuring them for use with GitHub on Windows.

## Why Use SSH Keys?

Using SSH keys for GitHub authentication offers several advantages over password or token-based authentication:

- More secure than password authentication
- No need to enter credentials each time
- No personal access tokens to manage
- Easier to revoke access if a key is compromised

## Prerequisites

- Windows 10 or later (with OpenSSH installed - included by default in recent Windows versions)
- PowerShell
- A GitHub account

## Step 1: Check for Existing SSH Keys

First, check if you already have any SSH keys:

```powershell
Get-ChildItem -Path "$env:USERPROFILE\.ssh" -Force
```

Look for files named `id_rsa` (private key) and `id_rsa.pub` (public key) or other key pairs like `id_ed25519` and `id_ed25519.pub`.

## Step 2: Generate a New SSH Key

If you don't have an existing key pair or want to create a new one specifically for GitHub:

1. Open PowerShell

2. Generate a new SSH key (Ed25519 is recommended for modern systems):

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Or if you need RSA (for legacy systems):

```powershell
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

3. When prompted for a file location, press Enter to accept the default location (`C:\Users\your_username\.ssh\id_ed25519` or `id_rsa`).

4. When prompted for a passphrase, enter a secure passphrase or press Enter for no passphrase. Using a passphrase is recommended for added security.

## Step 3: Start the SSH Agent

1. Check if the SSH agent service is running:

```powershell
Get-Service ssh-agent | Select-Object Name, Status
```

2. If the status is not "Running", start the service and set it to start automatically:

```powershell
# Start the service for the current session
Start-Service ssh-agent

# Set to start automatically (optional, but recommended)
Set-Service -Name ssh-agent -StartupType Automatic
```

## Step 4: Add Your SSH Key to the SSH Agent

Add your private key to the SSH agent:

```powershell
# For Ed25519 key
ssh-add $env:USERPROFILE\.ssh\id_ed25519

# For RSA key
# ssh-add $env:USERPROFILE\.ssh\id_rsa
```

If you set a passphrase, you'll be prompted to enter it.

## Step 5: Copy Your SSH Public Key

1. Display your public key:

```powershell
# For Ed25519 key
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub

# For RSA key
# Get-Content $env:USERPROFILE\.ssh\id_rsa.pub
```

2. Copy the entire output (it should start with `ssh-ed25519` or `ssh-rsa` and end with your email address).

## Step 6: Add the SSH Key to Your GitHub Account

1. Go to GitHub.com and sign in to your account

2. In the upper-right corner, click your profile photo, then click **Settings**

3. In the sidebar, click **SSH and GPG keys**

4. Click **New SSH key** or **Add SSH key**

5. In the "Title" field, add a descriptive label for the key (e.g., "Work Laptop Windows")

6. In the "Key" field, paste your public key

7. Click **Add SSH key**

8. If prompted, confirm your GitHub password

## Step 7: Test Your SSH Connection to GitHub

Verify that your SSH connection to GitHub is working:

```powershell
ssh -T git@github.com
```

You might see a warning about authenticity of host. Type `yes` to continue.

If successful, you should see a message like:
```
Hi username! You've successfully authenticated, but GitHub does not provide shell access.
```

## Step 8: Configure Git to Use SSH

When cloning new repositories, use the SSH URL instead of HTTPS:
```
git clone git@github.com:username/repository.git
```

For existing repositories configured with HTTPS, change the remote URL to SSH:

```powershell
# Check current remote
git remote -v

# Change remote URL to SSH
git remote set-url origin git@github.com:username/repository.git

# Verify the change
git remote -v
```

## Step 9: Using SSH Keys with Your Repository

For the Law repository, you would use:

```powershell
# Add the remote using SSH instead of HTTPS
git remote add origin git@github.com:tiation/Law.git

# Push your changes
git push -u origin main
```

## Troubleshooting

### SSH Agent Issues

If you encounter "Permission denied" errors:
```powershell
# Make sure the agent is running
Start-Service ssh-agent

# Re-add your key
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

### Key Permissions

If you get permission errors, ensure your key files have appropriate permissions:
```powershell
# Restrict access to your private key
icacls $env:USERPROFILE\.ssh\id_ed25519 /inheritance:r
icacls $env:USERPROFILE\.ssh\id_ed25519 /grant:r "$($env:USERNAME):R"
```

### Connection Testing

Test verbose SSH connection to see more detailed error messages:
```powershell
ssh -vT git@github.com
```

## Conclusion

You've now set up SSH keys for GitHub authentication on your Windows system. These keys will allow you to securely interact with GitHub repositories without needing to enter your username and password each time.

Remember to keep your private key secure and use a strong passphrase for additional protection.

