import ejs from 'ejs';
import { FileUtils } from '../utils/file-utils';
import { TemplateContext } from '../types';

export class TemplateEngine {
  /**
   * Render template string with context
   */
  async render(templateContent: string, context: TemplateContext): Promise<string> {
    return ejs.render(templateContent, context);
  }

  /**
   * Render template file with context
   */
  async renderFile(templatePath: string, context: TemplateContext): Promise<string> {
    const templateContent = await FileUtils.readFile(templatePath);
    return this.render(templateContent, context);
  }

  /**
   * Render template to output file
   */
  async renderToFile(
    templatePath: string,
    outputPath: string,
    context: TemplateContext
  ): Promise<void> {
    const content = await this.renderFile(templatePath, context);
    await FileUtils.writeFile(outputPath, content);
  }

  /**
   * Render multiple templates to a directory
   */
  async renderDirectory(
    templateDir: string,
    outputDir: string,
    context: TemplateContext,
    filePattern?: RegExp
  ): Promise<void> {
    const files = await FileUtils.listFiles(templateDir, filePattern);

    for (const file of files) {
      const templatePath = `${templateDir}/${file}`;
      const outputPath = `${outputDir}/${file.replace('.ejs', '')}`;

      if (file.endsWith('.ejs')) {
        await this.renderToFile(templatePath, outputPath, context);
      } else {
        await FileUtils.copyFile(templatePath, outputPath);
      }
    }
  }

  /**
   * Check if template exists
   */
  async templateExists(templatePath: string): Promise<boolean> {
    return FileUtils.fileExists(templatePath);
  }
}
