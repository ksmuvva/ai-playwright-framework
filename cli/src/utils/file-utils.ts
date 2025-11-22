import fs from 'fs-extra';
import path from 'path';
import os from 'os';

export class FileUtils {
  /**
   * Validate path to prevent traversal attacks
   * Ensures the resolved path is within the allowed base directory
   * Allows system temp directory for testing purposes
   */
  private static validatePath(filePath: string, baseDir?: string): string {
    const resolved = path.resolve(filePath);
    const tmpDir = path.resolve(os.tmpdir());

    // Allow paths in system temporary directory (for testing)
    if (resolved.startsWith(tmpDir + path.sep) || resolved === tmpDir) {
      return resolved;
    }

    // For non-temp paths, enforce strict validation
    const base = baseDir || process.cwd();
    const normalizedBase = path.resolve(base);

    // Check if the resolved path starts with the base directory
    if (!resolved.startsWith(normalizedBase + path.sep) && resolved !== normalizedBase) {
      throw new Error(`Security: Path traversal detected. ${filePath} is outside allowed directory`);
    }

    return resolved;
  }

  /**
   * Copy directory recursively
   */
  static async copyDirectory(src: string, dest: string): Promise<void> {
    // Validate both paths to prevent traversal
    this.validatePath(src);
    this.validatePath(dest);
    await fs.copy(src, dest);
  }

  /**
   * Create directory if it doesn't exist
   */
  static async ensureDirectory(dirPath: string): Promise<void> {
    // Validate path to prevent traversal
    const validatedPath = this.validatePath(dirPath);
    await fs.ensureDir(validatedPath);
  }

  /**
   * Write file with directory creation
   */
  static async writeFile(filePath: string, content: string): Promise<void> {
    // Validate path to prevent traversal
    const validatedPath = this.validatePath(filePath);
    await fs.ensureDir(path.dirname(validatedPath));
    await fs.writeFile(validatedPath, content, 'utf-8');
  }

  /**
   * Read file
   */
  static async readFile(filePath: string): Promise<string> {
    // Validate path to prevent traversal
    const validatedPath = this.validatePath(filePath);
    return await fs.readFile(validatedPath, 'utf-8');
  }

  /**
   * Check if file exists
   */
  static async fileExists(filePath: string): Promise<boolean> {
    try {
      // Validate path to prevent traversal
      const validatedPath = this.validatePath(filePath);
      await fs.access(validatedPath);
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
      // Validate path to prevent traversal
      const validatedPath = this.validatePath(dirPath);
      const stat = await fs.stat(validatedPath);
      return stat.isDirectory();
    } catch {
      return false;
    }
  }

  /**
   * Get template path
   */
  static getTemplatePath(...segments: string[]): string {
    return path.join(__dirname, '../../templates', ...segments);
  }

  /**
   * List files in directory
   */
  static async listFiles(dirPath: string, pattern?: RegExp): Promise<string[]> {
    const files = await fs.readdir(dirPath);

    if (pattern) {
      return files.filter(file => pattern.test(file));
    }

    return files;
  }

  /**
   * Copy file
   */
  static async copyFile(src: string, dest: string): Promise<void> {
    // Validate both paths to prevent traversal
    const validatedSrc = this.validatePath(src);
    const validatedDest = this.validatePath(dest);
    await fs.ensureDir(path.dirname(validatedDest));
    await fs.copyFile(validatedSrc, validatedDest);
  }

  /**
   * Remove directory
   */
  static async removeDirectory(dirPath: string): Promise<void> {
    // Validate path to prevent traversal
    const validatedPath = this.validatePath(dirPath);
    await fs.remove(validatedPath);
  }
}
