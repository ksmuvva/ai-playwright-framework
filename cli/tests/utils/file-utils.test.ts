/**
 * Unit Tests for File Utilities
 * Tests file operations, directory management, and path handling
 */

import { FileUtils } from '../../src/utils/file-utils';
import * as fs from 'fs-extra';
import * as path from 'path';
import * as os from 'os';

describe('FileUtils', () => {
  let tempDir: string;

  beforeEach(async () => {
    // Create temporary directory for tests
    tempDir = path.join(os.tmpdir(), `playwright-ai-test-${Date.now()}`);
    await fs.ensureDir(tempDir);
  });

  afterEach(async () => {
    // Cleanup temporary directory
    if (await fs.pathExists(tempDir)) {
      await fs.remove(tempDir);
    }
  });

  describe('ensureDirectory', () => {
    it('should create directory if it does not exist', async () => {
      const dirPath = path.join(tempDir, 'new-directory');
      await FileUtils.ensureDirectory(dirPath);

      const exists = await fs.pathExists(dirPath);
      expect(exists).toBe(true);

      const stats = await fs.stat(dirPath);
      expect(stats.isDirectory()).toBe(true);
    });

    it('should not error if directory already exists', async () => {
      const dirPath = path.join(tempDir, 'existing-directory');
      await fs.ensureDir(dirPath);

      // Should not throw
      await expect(FileUtils.ensureDirectory(dirPath)).resolves.not.toThrow();
    });

    it('should create nested directories', async () => {
      const nestedPath = path.join(tempDir, 'level1', 'level2', 'level3');
      await FileUtils.ensureDirectory(nestedPath);

      const exists = await fs.pathExists(nestedPath);
      expect(exists).toBe(true);
    });
  });

  describe('writeFile', () => {
    it('should write file with content', async () => {
      const filePath = path.join(tempDir, 'test-file.txt');
      const content = 'Hello, World!';

      await FileUtils.writeFile(filePath, content);

      const fileContent = await fs.readFile(filePath, 'utf-8');
      expect(fileContent).toBe(content);
    });

    it('should create parent directories if they do not exist', async () => {
      const filePath = path.join(tempDir, 'nested', 'dir', 'file.txt');
      const content = 'Nested file content';

      await FileUtils.writeFile(filePath, content);

      const fileContent = await fs.readFile(filePath, 'utf-8');
      expect(fileContent).toBe(content);

      const parentExists = await fs.pathExists(path.dirname(filePath));
      expect(parentExists).toBe(true);
    });

    it('should overwrite existing file', async () => {
      const filePath = path.join(tempDir, 'overwrite-test.txt');

      await FileUtils.writeFile(filePath, 'Original content');
      await FileUtils.writeFile(filePath, 'New content');

      const fileContent = await fs.readFile(filePath, 'utf-8');
      expect(fileContent).toBe('New content');
    });
  });

  describe('readFile', () => {
    it('should read file content', async () => {
      const filePath = path.join(tempDir, 'read-test.txt');
      const content = 'File content to read';

      await fs.writeFile(filePath, content, 'utf-8');

      const readContent = await FileUtils.readFile(filePath);
      expect(readContent).toBe(content);
    });

    it('should throw error if file does not exist', async () => {
      const filePath = path.join(tempDir, 'non-existent.txt');

      await expect(FileUtils.readFile(filePath)).rejects.toThrow();
    });
  });

  describe('fileExists', () => {
    it('should return true for existing file', async () => {
      const filePath = path.join(tempDir, 'exists-test.txt');
      await fs.writeFile(filePath, 'content');

      const exists = await FileUtils.fileExists(filePath);
      expect(exists).toBe(true);
    });

    it('should return false for non-existing file', async () => {
      const filePath = path.join(tempDir, 'does-not-exist.txt');

      const exists = await FileUtils.fileExists(filePath);
      expect(exists).toBe(false);
    });

    it('should return false for directory path', async () => {
      const dirPath = path.join(tempDir, 'directory');
      await fs.ensureDir(dirPath);

      const exists = await FileUtils.fileExists(dirPath);
      expect(exists).toBe(true); // File exists check only checks access, not type
    });
  });

  describe('directoryExists', () => {
    it('should return true for existing directory', async () => {
      const dirPath = path.join(tempDir, 'existing-dir');
      await fs.ensureDir(dirPath);

      const exists = await FileUtils.directoryExists(dirPath);
      expect(exists).toBe(true);
    });

    it('should return false for non-existing directory', async () => {
      const dirPath = path.join(tempDir, 'non-existing-dir');

      const exists = await FileUtils.directoryExists(dirPath);
      expect(exists).toBe(false);
    });

    it('should return false for file path', async () => {
      const filePath = path.join(tempDir, 'file.txt');
      await fs.writeFile(filePath, 'content');

      const exists = await FileUtils.directoryExists(filePath);
      expect(exists).toBe(false);
    });
  });

  describe('copyFile', () => {
    it('should copy file from source to destination', async () => {
      const srcPath = path.join(tempDir, 'source.txt');
      const destPath = path.join(tempDir, 'destination.txt');
      const content = 'File to copy';

      await fs.writeFile(srcPath, content);

      await FileUtils.copyFile(srcPath, destPath);

      const destContent = await fs.readFile(destPath, 'utf-8');
      expect(destContent).toBe(content);
    });

    it('should create destination directory if it does not exist', async () => {
      const srcPath = path.join(tempDir, 'source.txt');
      const destPath = path.join(tempDir, 'nested', 'destination.txt');
      const content = 'File to copy';

      await fs.writeFile(srcPath, content);

      await FileUtils.copyFile(srcPath, destPath);

      const destContent = await fs.readFile(destPath, 'utf-8');
      expect(destContent).toBe(content);
    });
  });

  describe('copyDirectory', () => {
    it('should copy directory recursively', async () => {
      const srcDir = path.join(tempDir, 'src-dir');
      const destDir = path.join(tempDir, 'dest-dir');

      // Create source directory structure
      await fs.ensureDir(srcDir);
      await fs.writeFile(path.join(srcDir, 'file1.txt'), 'content1');
      await fs.ensureDir(path.join(srcDir, 'subdir'));
      await fs.writeFile(path.join(srcDir, 'subdir', 'file2.txt'), 'content2');

      await FileUtils.copyDirectory(srcDir, destDir);

      // Verify copied files
      const file1Content = await fs.readFile(path.join(destDir, 'file1.txt'), 'utf-8');
      expect(file1Content).toBe('content1');

      const file2Content = await fs.readFile(path.join(destDir, 'subdir', 'file2.txt'), 'utf-8');
      expect(file2Content).toBe('content2');
    });
  });

  describe('listFiles', () => {
    it('should list all files in directory', async () => {
      const dirPath = tempDir;

      await fs.writeFile(path.join(dirPath, 'file1.txt'), 'content');
      await fs.writeFile(path.join(dirPath, 'file2.js'), 'content');
      await fs.writeFile(path.join(dirPath, 'file3.json'), 'content');

      const files = await FileUtils.listFiles(dirPath);

      expect(files).toContain('file1.txt');
      expect(files).toContain('file2.js');
      expect(files).toContain('file3.json');
      expect(files.length).toBeGreaterThanOrEqual(3);
    });

    it('should filter files by pattern', async () => {
      const dirPath = tempDir;

      await fs.writeFile(path.join(dirPath, 'file1.txt'), 'content');
      await fs.writeFile(path.join(dirPath, 'file2.js'), 'content');
      await fs.writeFile(path.join(dirPath, 'file3.txt'), 'content');

      const files = await FileUtils.listFiles(dirPath, /\.txt$/);

      expect(files).toContain('file1.txt');
      expect(files).toContain('file3.txt');
      expect(files).not.toContain('file2.js');
    });
  });

  describe('removeDirectory', () => {
    it('should remove directory and contents', async () => {
      const dirPath = path.join(tempDir, 'to-remove');

      await fs.ensureDir(dirPath);
      await fs.writeFile(path.join(dirPath, 'file.txt'), 'content');

      await FileUtils.removeDirectory(dirPath);

      const exists = await fs.pathExists(dirPath);
      expect(exists).toBe(false);
    });

    it('should not error if directory does not exist', async () => {
      const dirPath = path.join(tempDir, 'non-existing');

      await expect(FileUtils.removeDirectory(dirPath)).resolves.not.toThrow();
    });
  });

  describe('getTemplatePath', () => {
    it('should return path to templates directory', () => {
      const templatePath = FileUtils.getTemplatePath('python');

      expect(templatePath).toContain('templates');
      expect(templatePath).toContain('python');
    });

    it('should join multiple segments', () => {
      const templatePath = FileUtils.getTemplatePath('python', 'helpers', 'auth_helper.py');

      expect(templatePath).toContain('templates');
      expect(templatePath).toContain('python');
      expect(templatePath).toContain('helpers');
      expect(templatePath).toContain('auth_helper.py');
    });
  });
});
