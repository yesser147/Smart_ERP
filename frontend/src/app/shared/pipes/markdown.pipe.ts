import { Pipe, PipeTransform } from '@angular/core';

/**
 * The LLM's lightweight markdown (**bold**, *italic*, "- " / "1. " lists,
 * "#" headings, blank-line paragraphs) -> safe HTML for [innerHTML].
 * The text is HTML-escaped first; Angular's sanitizer allows the tags used.
 */
export function markdownToHtml(text: string | null | undefined): string {
  if (!text) return '';

  const html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+?)\*/g, '$1<em>$2</em>');

  const out: string[] = [];
  let list: 'ul' | 'ol' | null = null;
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };

  for (const raw of html.split('\n')) {
    const line = raw.trim();
    const bullet = /^[-•*]\s+(.*)$/.exec(line);
    const numbered = /^[0-9]+[.)]\s+(.*)$/.exec(line);
    const heading = /^#{1,3}\s+(.*)$/.exec(line);

    if (bullet || numbered) {
      const kind = bullet ? 'ul' : 'ol';
      if (list !== kind) { closeList(); out.push(`<${kind}>`); list = kind; }
      out.push(`<li>${(bullet ?? numbered)![1]}</li>`);
    } else {
      closeList();
      if (heading) out.push(`<h3>${heading[1]}</h3>`);
      else if (line) out.push(`<p>${line}</p>`);
    }
  }
  closeList();
  return out.join('');
}

@Pipe({ name: 'markdown', standalone: true })
export class MarkdownPipe implements PipeTransform {
  transform(text: string | null | undefined): string {
    return markdownToHtml(text);
  }
}
