import fs from 'fs-extra';
import path from 'path';

export class FileUtils {
  /**
   * Copy directory recursively
   */
  static async copyDirectory(src: string, dest: string): Promise<void> {
    await fs.copy(src, dest);
  }

  /**
   * Create directory if it doesn't exist
   */
  static async ensureDirectory(dirPath: string): Promise<void> {
    await fs.ensureDir(dirPath);
  }

  /**
   * Write file with directory creation
   */
  static async writeFile(filePath: string, content: string): Promise<void> {
    await fs.ensureDir(path.dirname(filePath));
    await fs.writeFile(filePath, content, 'utf-8');
  }

  /**
   * Read file
   */
  static async readFile(filePath: string): Promise<string> {
    return await fs.readFile(filePath, 'utf-8');
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
    await fs.ensureDir(path.dirname(dest));
    await fs.copyFile(src, dest);
  }

  /**
   * Remove directory
   */
  static async removeDirectory(dirPath: string): Promise<void> {
    await fs.remove(dirPath);
  }
}
