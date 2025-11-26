import fs from 'fs-extra';
import path from 'path';

export class FileUtils {
  /**
   * Validate path to prevent path traversal attacks (SEC-003 fix)
   * FAILURE-001 FIX: Allow absolute paths and external directories when explicitly requested
   *
   * @param filePath - Path to validate
   * @param options - Validation options
   * @param options.allowExternal - Allow paths outside project root (default: false)
   * @param options.baseDir - Custom base directory (default: process.cwd())
   */
  private static validatePath(
    filePath: string,
    options?: {
      allowExternal?: boolean;
      baseDir?: string;
    }
  ): string {
    const resolved = path.resolve(filePath);
    const projectRoot = options?.baseDir ? path.resolve(options.baseDir) : path.resolve(process.cwd());

    // Allow absolute paths if explicitly requested
    if (path.isAbsolute(filePath) && options?.allowExternal) {
      return resolved;
    }

    // For relative paths, enforce project root restriction
    if (!path.isAbsolute(filePath) && !resolved.startsWith(projectRoot)) {
      throw new Error(
        `Relative path traversal detected: ${filePath} resolves outside project directory.\n` +
        `Use absolute paths or set allowExternal: true for paths outside the project.`
      );
    }

    // Absolute paths within project root are always allowed
    if (path.isAbsolute(filePath) && resolved.startsWith(projectRoot)) {
      return resolved;
    }

    // Allow test directories (temp, /tmp, etc.) for test environments
    const safePaths = [
      projectRoot,
      '/tmp',
      require('os').tmpdir(),
      process.env.TMPDIR || '',
    ].filter(Boolean);

    if (safePaths.some(safePath => resolved.startsWith(safePath))) {
      return resolved;
    }

    // If none of the conditions match, block the path
    if (!options?.allowExternal) {
      throw new Error(
        `Path traversal detected: ${filePath} is outside the project directory.\n` +
        `Resolved to: ${resolved}\n` +
        `Project root: ${projectRoot}\n` +
        `To allow this path, use an absolute path with allowExternal option.`
      );
    }

    return resolved;
  }

  /**
   * Validate that path does not contain dangerous patterns
   */
  private static validatePathSafety(filePath: string): void {
    // Check for null bytes (directory traversal attempt)
    if (filePath.includes('\0')) {
      throw new Error('Invalid path: contains null bytes');
    }

    // Normalize path to check for traversal attempts
    const normalized = path.normalize(filePath);
    if (normalized.includes('..')) {
      throw new Error('Invalid path: contains parent directory references');
    }
  }
  /**
   * Copy directory recursively
   */
  static async copyDirectory(src: string, dest: string): Promise<void> {
    this.validatePathSafety(dest);
    const validatedDest = this.validatePath(dest, {
      allowExternal: path.isAbsolute(dest)
    });
    await fs.copy(src, validatedDest);
  }

  /**
   * Create directory if it doesn't exist
   * FAILURE-001 FIX: Allow absolute paths for output directories
   */
  static async ensureDirectory(dirPath: string): Promise<void> {
    this.validatePathSafety(dirPath);
    const validatedPath = this.validatePath(dirPath, {
      allowExternal: path.isAbsolute(dirPath)  // Allow absolute paths
    });
    await fs.ensureDir(validatedPath);
  }

  /**
   * Write file with directory creation
   */
  static async writeFile(filePath: string, content: string): Promise<void> {
    this.validatePathSafety(filePath);
    const validatedPath = this.validatePath(filePath, {
      allowExternal: path.isAbsolute(filePath)
    });
    await fs.ensureDir(path.dirname(validatedPath));
    await fs.writeFile(validatedPath, content, 'utf-8');
  }

  /**
   * Write file with secure permissions (for sensitive data like .env files)
   * Sets file mode to 0o600 (owner read/write only)
   */
  static async writeSecureFile(filePath: string, content: string): Promise<void> {
    this.validatePathSafety(filePath);
    const validatedPath = this.validatePath(filePath, {
      allowExternal: path.isAbsolute(filePath)
    });
    await fs.ensureDir(path.dirname(validatedPath));
    await fs.writeFile(validatedPath, content, {
      encoding: 'utf-8',
      mode: 0o600 // Owner read/write only - prevents API key exposure
    });
  }

  /**
   * Read file
   * FAILURE-015 FIX: Handle non-UTF-8 files with fallback encoding
   */
  static async readFile(filePath: string): Promise<string> {
    this.validatePathSafety(filePath);
    const validatedPath = this.validatePath(filePath, {
      allowExternal: path.isAbsolute(filePath)
    });

    try {
      return await fs.readFile(validatedPath, 'utf-8');
    } catch (error: any) {
      // Check if it's an encoding error
      if (error.message && error.message.includes('UTF-8')) {
        // Try latin1 encoding as fallback
        const buffer = await fs.readFile(validatedPath);
        return buffer.toString('latin1');
      }
      throw error;
    }
  }

  /**
   * Check if file exists
   * Includes path validation for security
   */
  static async fileExists(filePath: string): Promise<boolean> {
    try {
      this.validatePathSafety(filePath);
      const validatedPath = this.validatePath(filePath, {
        allowExternal: path.isAbsolute(filePath)
      });
      await fs.access(validatedPath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if directory exists
   * Includes path validation for security
   */
  static async directoryExists(dirPath: string): Promise<boolean> {
    try {
      this.validatePathSafety(dirPath);
      const validatedPath = this.validatePath(dirPath, {
        allowExternal: path.isAbsolute(dirPath)
      });
      const stat = await fs.stat(validatedPath);
      return stat.isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * Get template path (BUG-008 fix)
   * Handles compiled code and global npm installations
   */
  static getTemplatePath(...segments: string[]): string {
    // Try to find templates relative to the current file
    let templatesDir = path.join(__dirname, '../../templates');

    // If templates don't exist there, try relative to package root
    if (!fs.existsSync(templatesDir)) {
      // When installed globally, templates should be in node_modules/@ai-playwright/cli/templates
      templatesDir = path.join(__dirname, '../../../templates');
    }

    // Fallback to process.cwd() if still not found (development mode)
    if (!fs.existsSync(templatesDir)) {
      templatesDir = path.join(process.cwd(), 'cli/templates');
    }

    return path.join(templatesDir, ...segments);
  }

  /**
   * List files in directory
   */
  static async listFiles(dirPath: string, pattern?: RegExp): Promise<string[]> {
    this.validatePathSafety(dirPath);
    const validatedPath = this.validatePath(dirPath, {
      allowExternal: path.isAbsolute(dirPath)
    });
    const files = await fs.readdir(validatedPath);

    if (pattern) {
      return files.filter(file => pattern.test(file));
    }

    return files;
  }

  /**
   * Copy file
   */
  static async copyFile(src: string, dest: string): Promise<void> {
    this.validatePathSafety(dest);
    const validatedDest = this.validatePath(dest, {
      allowExternal: path.isAbsolute(dest)
    });
    await fs.ensureDir(path.dirname(validatedDest));
    await fs.copyFile(src, validatedDest);
  }

  /**
   * Remove directory
   */
  static async removeDirectory(dirPath: string): Promise<void> {
    this.validatePathSafety(dirPath);
    const validatedPath = this.validatePath(dirPath, {
      allowExternal: path.isAbsolute(dirPath)
    });
    await fs.remove(validatedPath);
  }
}
