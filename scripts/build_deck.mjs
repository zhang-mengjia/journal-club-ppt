import fs from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

const listHeaders = { outline: 'Outline', summary: 'Summary', discussion: 'Discussion' };

function argumentsFromCommandLine() {
  const args = process.argv.slice(2);
  const result = {};
  for (let index = 0; index < args.length; index += 2) {
    const key = args[index];
    if (!['--plan', '--output', '--project-root'].includes(key) || !args[index + 1]) {
      throw new Error('Usage: node build_deck.mjs --plan deck.json --output deck.raw.pptx [--project-root project]');
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
    geometry: options.geometry || 'rect',
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
      ...(options.bold === undefined ? {} : { bold: options.bold }),
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
  const style = { typeface: 'Arial', fontSize: '18pt', color: item.color || '#000000' };
  const runs = [];
  if (item.label) {
    runs.push({ run: `${item.label} | `, style: { ...style, bold: true, italic: true } });
  }
  runs.push({ run: item.text, style });
  return { runs };
}

function addCitation(slide, citation, index) {
  const {
    authors,
    first_authors: firstAuthors = authors,
    corresponding_authors: correspondingAuthors = [],
    journal, year, box,
  } = citation;
  if (!Array.isArray(firstAuthors) || !firstAuthors.length || !Array.isArray(correspondingAuthors)
      || !journal || !year || !box) {
    throw new Error('A citation needs an author list, a journal abbreviation, a year, and a box.');
  }
  const uniqueFirst = new Set(firstAuthors);
  const uniqueCorresponding = [...new Set(correspondingAuthors)].filter((name) => !uniqueFirst.has(name));
  const first = [...uniqueFirst].join(', ');
  const names = uniqueCorresponding.length ? `${first} & ${uniqueCorresponding.join(', ')}` : first;
  rectangle(slide, `Figure citation ${index + 1}`, [{ runs: [
    { run: `${names}, ` },
    { run: journal, style: { italic: true } },
    { run: `, ${year}` },
  ] }], box, { geometry: 'textbox', size_pt: 14, align: 'right', valign: 'middle' });
}

function headingRuns(value) {
  if (!value.includes('|')) return value;
  return value.split(/\r?\n/).map(line => ({
    runs: line.split(/(\|)/).filter(Boolean).map(run => (
      run === '|' ? { run, style: { bold: true, italic: true } } : { run }
    )),
  }));
}

function checkHeadingPrefixes(slides) {
  const pagesByPrefix = new Map();
  for (const [index, slide] of slides.entries()) {
    const fields = ['cover', 'thanks', 'question'].includes(slide.type)
      ? [slide.title, ...(slide.type === 'question' ? [slide.header] : [])]
      : [slide.header, slide.subtitle];
    for (const title of fields.filter(Boolean)) {
      if (!title.includes('|')) continue;
      const parts = title.split('|').map(part => part.trim().replace(/\s+/g, ' '));
      if (parts.length !== 2 || parts.some(part => !part)) {
        throw new Error(`Slide ${index + 1}: use one shared left-hand heading and one specific right-hand heading.`);
      }
      if (!pagesByPrefix.has(parts[0])) pagesByPrefix.set(parts[0], new Set());
      pagesByPrefix.get(parts[0]).add(index + 1);
    }
  }
  for (const [prefix, pages] of pagesByPrefix) {
    if (pages.size === 1) {
      throw new Error(`Slide ${[...pages][0]}: "${prefix}" is a one-off heading prefix. Use a standalone heading.`);
    }
  }
}

function addTitleBar(slide, header, sizePt) {
  const headingSize = sizePt ?? (header.length > 85 ? 21.75 : header.length > 75 ? 23 : 24);
  rectangle(slide, 'Black title bar', headingRuns(header), [0, 0, 1280, 60.4724], {
    fill: '#000000', color: '#FFFFFF', size_pt: headingSize,
    align: 'center', valign: 'middle',
    insets: { left: 36, right: 36, top: 0, bottom: 0 },
  });
}

function addChrome(slide, item, number) {
  let header = item.header || listHeaders[item.type] || 'Results';
  if (item.author_names?.length) {
    header = item.author_names.length === 1 ? 'Corresponding author' : 'Corresponding authors';
    if (item.header && item.header !== header) {
      throw new Error(`Slide ${number}: use "${header}" for the featured corresponding author(s).`);
    }
  }
  addTitleBar(slide, header, item.header_size_pt);
  if (item.show_marker !== false) {
    rectangle(slide, 'Outline square', null, [18, 79, 45, 35], { fill: '#FFFFFF', stroke: '#000000' });
    rectangle(slide, 'Black square', null, [43, 96, 35, 25], { fill: '#000000' });
  }
  const subtitle = item.subtitle || '';
  rectangle(slide, 'Slide subject', headingRuns(subtitle), [96.6215, 79.6253, 1165.4144, 41.5527], {
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

function isInsideDirectory(directory, file) {
  const relative = path.relative(directory, file);
  return relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

async function addImages(slide, images, planDirectory, projectRoot) {
  for (const item of images || []) {
    const relativePath = item.path.replaceAll('\\', '/');
    if (path.posix.isAbsolute(relativePath) || /^[a-z][a-z\d+.-]*:/i.test(relativePath)) {
      throw new Error(`Use an image path relative to the deck plan: ${item.path}`);
    }
    const imagePath = path.resolve(planDirectory, relativePath);
    const scopeError = `Image path must stay inside the project directory: ${item.path}`;
    if (!isInsideDirectory(projectRoot, imagePath)) throw new Error(scopeError);
    const resolvedImage = await fs.realpath(imagePath);
    if (!isInsideDirectory(projectRoot, resolvedImage)) throw new Error(scopeError);
    const bytes = await fs.readFile(resolvedImage);
    const blob = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
    const [left, top, width, height] = item.box;
    slide.images.add({
      blob,
      contentType: imageType(bytes, imagePath),
      position: { left, top, width, height },
      alt: item.alt || '',
      fit: item.fit || 'contain',
      geometry: item.geometry,
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
const inputDirectory = path.dirname(args.plan);
const defaultRoot = path.basename(inputDirectory).toLowerCase() === 'source'
  ? path.dirname(inputDirectory)
  : inputDirectory;
const projectRoot = await fs.realpath(args['project-root'] || defaultRoot);
const planPath = await fs.realpath(args.plan);
if (!isInsideDirectory(projectRoot, planPath)) {
  throw new Error('The deck plan must be inside the project directory.');
}
const planDirectory = path.dirname(planPath);
const plan = JSON.parse(await fs.readFile(planPath, 'utf8'));
if (!Array.isArray(plan.slides) || !plan.slides.length) throw new Error('The plan has no slides.');
checkHeadingPrefixes(plan.slides);
const { Presentation, PresentationFile } = await artifactLibrary();
const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });

for (const [index, item] of plan.slides.entries()) {
  if (!['cover', 'content', 'question', 'figure', 'thanks'].includes(item.type) && !Object.hasOwn(listHeaders, item.type)) {
    throw new Error(`Slide ${index + 1} has an unsupported type.`);
  }
  if (!item.notes || typeof item.notes !== 'string') throw new Error(`Slide ${index + 1} needs speaker notes.`);
  const figureRefs = item.figure_refs ?? [];
  const figureRefPattern = /^(?:(?:Extended Data|Supplementary) )?Fig\.S?[1-9]\d*(?:[A-Z](?:, [A-Z])*)?$/;
  if (!Array.isArray(figureRefs) || figureRefs.some(ref => typeof ref !== 'string' || !figureRefPattern.test(ref))) {
    throw new Error(`Slide ${index + 1} needs figure_refs in the form of ["Fig.1A, B", "Extended Data Fig.2D"].`);
  }
  const slide = presentation.slides.add();
  slide.background.fill = '#FFFFFF';
  const pageNumber = item.page_number ?? index + 1;
  if (item.type === 'cover') {
    rectangle(slide, 'Cover title', headingRuns(item.title), [0, 135, 1280, 310], {
      fill: '#F2F2F2', size_pt: item.title_size_pt || 30,
      align: 'center', valign: 'middle',
      insets: { left: 65, right: 65, top: 0, bottom: 0 },
    });
    const byline = Array.isArray(item.byline) ? item.byline.join('\n') : item.byline || '';
    rectangle(slide, 'Cover byline', byline, [80, 505, 1120, 118], {
      size_pt: 17.25, align: 'center', valign: 'middle',
    });
  } else if (item.type === 'thanks') {
    rectangle(slide, 'Closing band', headingRuns(item.title || 'Thanks!'), [0, 220, 1280, 250], {
      fill: '#F2F2F2', size_pt: 34.5, align: 'center', valign: 'middle',
    });
    const label = item.closing_label ?? 'Journal Club';
    if (label) {
      rectangle(slide, 'Closing label', label, [80, 545, 1120, 40], {
        size_pt: 18, align: 'center', valign: 'middle',
      });
    }
    addPageNumber(slide, pageNumber);
  } else if (item.type === 'question') {
    addTitleBar(slide, item.header || 'Question', item.header_size_pt);
    rectangle(slide, 'Question body', headingRuns(item.title), [110.867, 60.4724, 1058.266, 601.889], {
      size_pt: 20, align: 'center', valign: 'middle',
    });
    addPageNumber(slide, pageNumber);
  } else if (item.type === 'figure') {
    await addImages(slide, item.images, planDirectory, projectRoot);
  } else {
    addChrome(slide, item, pageNumber);
    await addImages(slide, item.images, planDirectory, projectRoot);
    const textShapes = new Map();
    for (const [textIndex, text] of (item.texts || []).entries()) {
      const name = text.name || `Content text ${textIndex + 1}`;
      if (textShapes.has(name)) throw new Error(`Slide ${index + 1}: duplicate text shape name "${name}".`);
      textShapes.set(name, rectangle(slide, name, text.text, text.box, text));
    }
    for (const { from, to } of item.connections || []) {
      if (!textShapes.has(from) || !textShapes.has(to) || from === to) {
        throw new Error(`Slide ${index + 1}: connection "${from}" to "${to}" needs two distinct text shapes.`);
      }
      slide.shapes.connect(textShapes.get(from), textShapes.get(to), {
        kind: 'straight', fromSide: 'bottom', toSide: 'top',
        line: { style: 'solid', fill: '#555555', width: 1.5 },
      });
    }
    for (const [citationIndex, citation] of (item.citations || []).entries()) {
      addCitation(slide, citation, citationIndex);
    }
    const listHeader = listHeaders[item.type];
    const paragraphs = listHeader ? item.items : item.paragraphs;
    if (paragraphs) {
      rectangle(slide, listHeader ? `${listHeader} body` : 'Body text', paragraphs.map(richParagraph),
        item.body_box || [33.8427, 134.9249, 1211.3957, 454.722], {
          insets: { left: 9.6, top: 4.8, right: 9.6, bottom: 4.8 },
        });
    }
  }
  const figureLine = figureRefs.map(ref => `[${ref}]`).join(' ');
  slide.speakerNotes.text = figureLine ? [figureLine, ...item.notes.split(/\r?\n/)] : item.notes;
}

await fs.mkdir(path.dirname(args.output), { recursive: true });
await (await PresentationFile.exportPptx(presentation)).save(args.output);
console.log(JSON.stringify({ output: args.output, slides: presentation.slides.items.length }));
