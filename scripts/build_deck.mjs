import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

function argumentsFromCommandLine() {
  const args = process.argv.slice(2);
  const result = {};
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index];
    if (!['--plan', '--output'].includes(key) || !args[index + 1]) {
      throw new Error('Usage: node build_deck.mjs --plan deck.json --output deck.raw.pptx');
    }
    result[key.slice(2)] = path.resolve(args[index + 1]);
  }
  if (!result.plan || !result.output) throw new Error('Both --plan and --output are required.');
  return result;
}

async function artifactLibrary() {
  const require = createRequire(import.meta.url);
  try {
    return await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
  } catch (error) {
    const modules = process.env.RUNTIME_NODE_MODULES || process.env.NODE_PATH;
    if (!modules) {
      throw new Error('Set RUNTIME_NODE_MODULES to the Node package directory returned by load_workspace_dependencies.');
    }
    const runtimeRequire = createRequire(path.join(modules, '@oai/artifact-tool/package.json'));
    return import(pathToFileURL(runtimeRequire.resolve('@oai/artifact-tool')).href);
  }
}

function rectangle(slide, name, value, box, options = {}) {
  const [left, top, width, height] = box;
  const shape = slide.shapes.add({
    name,
    geometry: 'rect',
    position: { left, top, width, height },
    fill: options.fill || 'none',
    line: { fill: options.stroke || 'none', width: options.stroke ? 1 : 0 },
  });
  if (value !== null) {
    shape.text = value;
    shape.text.style = {
      typeface: 'Arial',
      fontSize: (options.size_pt || 18) * 4 / 3,
      color: options.color || '#000000',
      bold: options.bold || false,
      alignment: options.align || 'left',
      verticalAlignment: options.valign || 'top',
      insets: options.insets || 0,
      wrap: 'square',
      autoFit: 'none',
    };
  }
  return shape;
}

function richParagraph(item) {
  return {
    runs: [{
      run: item.text,
      style: { typeface: 'Arial', fontSize: '18pt', color: item.color || '#000000' },
    }],
  };
}

function addChrome(slide, item, number) {
  const headingSize = item.header.length > 65 ? 20.25 : item.header.length > 54 ? 21.75 : 24;
  rectangle(slide, 'Black title bar', item.header, [0, 0, 1280, 60.4724], {
    fill: '#000000', color: '#FFFFFF', size_pt: headingSize,
    align: 'center', valign: 'middle',
    insets: { left: 36, right: 36, top: 0, bottom: 0 },
  });
  rectangle(slide, 'Outline square', null, [18, 79, 45, 35], { fill: '#FFFFFF', stroke: '#000000' });
  rectangle(slide, 'Black square', null, [43, 96, 35, 25], { fill: '#000000' });
  rectangle(slide, 'Slide subject', item.subtitle || '', [96.6215, 79.6253, 1165.4144, 41.5527], {
    size_pt: 20, bold: true, valign: 'middle',
    insets: { left: 9.6, right: 9.6, top: 0, bottom: 0 },
  });
  addPageNumber(slide, number);
}

function addPageNumber(slide, number) {
  rectangle(slide, 'Slide number', String(number), [1147, 675, 65, 30], {
    size_pt: 12, color: '#888888', align: 'right', valign: 'middle',
  });
}

function imageType(bytes, imagePath) {
  if (bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) return 'image/png';
  if (bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'image/jpeg';
  if (bytes.subarray(0, 3).toString() === 'GIF') return 'image/gif';
  throw new Error(`Convert this image to PNG or JPEG before embedding: ${imagePath}`);
}

async function addImages(slide, images, planDirectory) {
  for (const item of images || []) {
    const imagePath = path.resolve(planDirectory, item.path);
    const bytes = await fs.readFile(imagePath);
    const blob = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const [left, top, width, height] = item.box;
    slide.images.add({
      blob,
      contentType: imageType(bytes, imagePath),
      position: { left, top, width, height },
      alt: item.alt || '',
      fit: 'contain',
    });
  }
}

const args = argumentsFromCommandLine();
try {
  await fs.access(args.output);
  throw new Error(`Output already exists: ${args.output}`);
} catch (error) {
  if (error.code !== 'ENOENT') throw error;
}
const plan = JSON.parse(await fs.readFile(args.plan, 'utf8'));
if (!Array.isArray(plan.slides) || !plan.slides.length) throw new Error('The plan has no slides.');
const { Presentation, PresentationFile } = await artifactLibrary();
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

for (const [index, item] of plan.slides.entries()) {
  if (!['cover', 'content', 'summary', 'thanks'].includes(item.type)) {
    throw new Error(`Slide ${index + 1} has an unsupported type.`);
  }
  if (!item.notes || typeof item.notes !== 'string') throw new Error(`Slide ${index + 1} needs speaker notes.`);
  const slide = presentation.slides.add();
  slide.background.fill = '#FFFFFF';
  if (item.type === 'cover') {
    rectangle(slide, 'Cover title', item.title, [0, 135, 1280, 310], {
      fill: '#F2F2F2', size_pt: item.title_size_pt || 30,
      align: 'center', valign: 'middle',
      insets: { left: 65, right: 65, top: 0, bottom: 0 },
    });
    const byline = Array.isArray(item.byline) ? item.byline.join('\n') : item.byline || '';
    rectangle(slide, 'Cover byline', byline, [80, 505, 1120, 118], {
      size_pt: 17.25, align: 'center', valign: 'middle',
    });
  } else if (item.type === 'thanks') {
    rectangle(slide, 'Closing band', item.title || 'Thanks!', [0, 220, 1280, 250], {
      fill: '#F2F2F2', size_pt: 34.5, align: 'center', valign: 'middle',
    });
    addPageNumber(slide, index + 1);
  } else {
    addChrome(slide, { ...item, header: item.header || (item.type === 'summary' ? 'Summary' : 'Results') }, index + 1);
    await addImages(slide, item.images, path.dirname(args.plan));
    for (const [textIndex, text] of (item.texts || []).entries()) {
      rectangle(slide, text.name || `Content text ${textIndex + 1}`, text.text, text.box, text);
    }
    const paragraphs = item.type === 'summary' ? item.items : item.paragraphs;
    if (paragraphs) {
      rectangle(slide, item.type === 'summary' ? 'Summary body' : 'Body text', paragraphs.map(richParagraph),
        item.body_box || [33.8427, 134.9249, 1211.3957, 454.2], {
          insets: { left: 9.6, top: 4.8, right: 9.6, bottom: 4.8 },
        });
    }
  }
  slide.speakerNotes.text = item.notes;
}

await fs.mkdir(path.dirname(args.output), { recursive: true });
await (await PresentationFile.exportPptx(presentation)).save(args.output);
console.log(JSON.stringify({ output: args.output, slides: presentation.slides.items.length }));
