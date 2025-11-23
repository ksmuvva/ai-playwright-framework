import fs from 'fs-extra';
import path from 'path';

export class FileUtils {
  /**
   * Validate path to prevent path traversal attacks (SEC-003 fix)
   */
  private static validatePath(filePath: string, baseDir?: string): string {
    const resolved = path.resolve(filePath);
    const projectRoot = baseDir ? path.resolve(baseDir) : path.resolve(process.cwd());

    // Prevent path traversal outside project root
    if (!resolved.startsWith(projectRoot)) {
      throw new Error(`Path traversal detected: ${filePath} is outside the project directory`);
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
    const validatedDest = this.validatePath(dest);
    await fs.copy(src, validatedDest);
  }

  /**
   * Create directory if it doesn't exist
   */
  static async ensureDirectory(dirPath: string): Promise<void> {
    this.validatePathSafety(dirPath);
    const validatedPath = this.validatePath(dirPath);
    await fs.ensureDir(validatedPath);
  }

  /**
   * Write file with directory creation
   */
  static async writeFile(filePath: string, content: string): Promise<void> {
    this.validatePathSafety(filePath);
    const validatedPath = this.validatePath(filePath);
    await fs.ensureDir(path.dirname(validatedPath));
    await fs.writeFile(validatedPath, content, 'utf-8');
  }

  /**
   * Write file with secure permissions (for sensitive data like .env files)
   * Sets file mode to 0o600 (owner read/write only)
   */
  static async writeSecureFile(filePath: string, content: string): Promise<void> {
    this.validatePathSafety(filePath);
    const validatedPath = this.validatePath(filePath);
    await fs.ensureDir(path.dirname(validatedPath));
    await fs.writeFile(validatedPath, content, {
      encoding: 'utf-8',
      mode: 0o600 // Owner read/write only - prevents API key exposure
    });
  }

  /**
   * Read file
   */
  static async readFile(filePath: string): Promise<string> {
    this.validatePathSafety(filePath);
    const validatedPath = this.validatePath(filePath);
    return await fs.readFile(validatedPath, 'utf-8');
  }

  /**
   * Check if file exists
   */
  static async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if directory exists
   */
  static async directoryExists(dirPath: string): Promise<boolean> {
    try {
      const stat = await fs.stat(dirPath);
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
    const validatedPath = this.validatePath(dirPath);
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
    const validatedDest = this.validatePath(dest);
    await fs.ensureDir(path.dirname(validatedDest));
    await fs.copyFile(src, validatedDest);
  }

  /**
   * Remove directory
   */
  static async removeDirectory(dirPath: string): Promise<void> {
    this.validatePathSafety(dirPath);
    const validatedPath = this.validatePath(dirPath);
    await fs.remove(validatedPath);
  }
}
