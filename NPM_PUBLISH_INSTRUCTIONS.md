# 📦 npm Publish Instructions

## How to Publish playwright-ai-framework to npm

This document provides step-by-step instructions to publish the `playwright-ai-framework` package to npm, fixing **Bug #1** from the E2E test report.

---

## ✅ Pre-Publish Checklist

Before publishing, ensure all these are complete:

- [x] All critical bugs fixed (#2, #3, #5, #6, #7)
- [x] CLI builds successfully (`npm run build`)
- [x] Template structure corrected (`features/environment.py`)
- [x] README installation instructions updated
- [x] All changes merged to main branch
- [ ] npm account configured
- [ ] Package version updated (if needed)

---

## 📋 Publishing Steps

### Step 1: Verify You're on Main Branch

```bash
cd /home/user/ai-playwright-framework
git checkout main
git pull origin main
```

### Step 2: Navigate to CLI Directory

```bash
cd cli/
```

### Step 3: Ensure Latest Build

```bash
npm install
npm run build
```

**Expected Output:**
```
> playwright-ai-framework@1.0.0 build
> tsc
```

✅ Should complete without errors

### Step 4: Test Package Locally

```bash
# Link globally to test
npm link

# Verify CLI works
playwright-ai --version
# Should output: 1.0.0

# Test init command
playwright-ai init --help
# Should show all options
```

### Step 5: Login to npm

```bash
npm login
```

**You'll be prompted for:**
- Username: Your npm username
- Password: Your npm password
- Email: Your npm email
- OTP (if 2FA enabled): Your authenticator code

### Step 6: Publish to npm

```bash
# Dry run first (see what will be published)
npm publish --dry-run

# If dry run looks good, publish for real
npm publish
```

**Expected Output:**
```
npm notice
npm notice 📦  playwright-ai-framework@1.0.0
npm notice === Tarball Contents ===
npm notice 1.5kB  package.json
npm notice 7.8kB  README.md
npm notice XXkB   dist/
npm notice XXkB   templates/
npm notice === Tarball Details ===
npm notice name:          playwright-ai-framework
npm notice version:       1.0.0
npm notice package size:  XXX kB
npm notice unpacked size: XXX kB
npm notice total files:   XXX
npm notice
+ playwright-ai-framework@1.0.0
```

---

## 🎯 Post-Publish Verification

### Step 1: Wait 1-2 Minutes

npm registry needs time to propagate the package.

### Step 2: Verify Package is Available

```bash
npm view playwright-ai-framework
```

**Should show:**
```
playwright-ai-framework@1.0.0 | MIT | deps: XX | versions: 1
AI-powered Playwright test automation framework generator
https://github.com/ksmuvva/ai-playwright-framework#readme

dist
.tarball: https://registry.npmjs.org/playwright-ai-framework/-/playwright-ai-framework-1.0.0.tgz
.shasum: XXXXX
.integrity: sha512-XXXXX==
```

### Step 3: Test Global Installation

```bash
# Unlink local version
npm unlink -g playwright-ai-framework

# Install from npm registry
npm install -g playwright-ai-framework

# Verify it works
playwright-ai --version
# Should output: 1.0.0

playwright-ai init --help
# Should show all options
```

---

## 🐛 Bug #1 Status Update

Once published:

- ✅ **Bug #1 FIXED:** Package published to npm
- ✅ Users can install via `npm install -g playwright-ai-framework`
- ✅ README Quick Start instructions now work
- ✅ No more 404 errors

---

## 📝 Update README After Publishing

After successful publish, update `README.md`:

```diff
### Installation

- **From Source (Current Method):**
+ **From npm (Recommended):**

+ ```bash
+ npm install -g playwright-ai-framework
+ ```
+
+ **From Source:**

  ```bash
  git clone https://github.com/ksmuvva/ai-playwright-framework.git
  cd ai-playwright-framework/cli
  npm install
  npm run build
  npm link
-
- **From npm (Coming Soon):**
-
- ```bash
- npm install -g playwright-ai-framework
- ```
```

---

## 🚨 Troubleshooting

### Error: "You do not have permission to publish"

**Solution:**
```bash
# Check if you're logged in
npm whoami

# If not logged in
npm login

# Check package name availability
npm view playwright-ai-framework
# If it says "404", name is available
```

### Error: "Package name too similar to existing package"

**Solution:**
- Change package name in `package.json` to something unique
- Example: `@your-org/playwright-ai-framework`

### Error: "Version 1.0.0 already published"

**Solution:**
```bash
# Bump version
npm version patch  # 1.0.0 -> 1.0.1
# OR
npm version minor  # 1.0.0 -> 1.1.0
# Then publish again
```

---

## 📊 Impact After Publishing

### Before Publishing
- ❌ `npm install -g playwright-ai-framework` fails (404)
- ❌ Users must clone from GitHub
- ❌ README Quick Start doesn't work
- ❌ 5-10 minute setup process

### After Publishing
- ✅ `npm install -g playwright-ai-framework` works
- ✅ One command installation
- ✅ README Quick Start works perfectly
- ✅ **30-second setup process**

---

## 🎯 Success Criteria

Framework can be considered **fully functional** when:

- [x] CLI builds successfully
- [x] Template structure is correct
- [x] Tests run successfully after generation
- [ ] **Package published to npm** ← THIS STEP
- [ ] Global installation works
- [ ] README Quick Start works end-to-end

**Current: 5/7 complete**
**After npm publish: 7/7 complete ✅**

---

## 📞 Need Help?

- npm documentation: https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry
- npm support: https://www.npmjs.com/support
- Check npm status: https://status.npmjs.org/

---

## ✅ Final Checklist Before Publishing

```bash
# 1. On main branch
git branch --show-current  # Should show: main

# 2. Latest code
git pull origin main

# 3. Clean build
cd cli/
rm -rf dist/ node_modules/
npm install
npm run build

# 4. Tests pass
npm test  # If tests exist

# 5. Version is correct
cat package.json | grep version  # Should show: "version": "1.0.0"

# 6. Logged into npm
npm whoami  # Should show your npm username

# 7. Ready to publish!
npm publish
```

---

**Status:** Ready to publish
**Estimated Time:** 5 minutes
**Impact:** Fixes Bug #1, completes 75% → 100% functionality
