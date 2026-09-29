import type { CodeSample } from "@/types/curriculum";

export function ts(filename: string, code: string): CodeSample {
  return { language: "typescript", filename, code: code.trim() };
}

export function py(filename: string, code: string): CodeSample {
  return { language: "python", filename, code: code.trim() };
}

export function js(filename: string, code: string): CodeSample {
  return { language: "javascript", filename, code: code.trim() };
}

export function yaml(filename: string, code: string): CodeSample {
  return { language: "yaml", filename, code: code.trim() };
}

export function sql(filename: string, code: string): CodeSample {
  return { language: "sql", filename, code: code.trim() };
}

export function bash(filename: string, code: string): CodeSample {
  return { language: "bash", filename, code: code.trim() };
}

export function dockerfile(filename: string, code: string): CodeSample {
  return { language: "dockerfile", filename, code: code.trim() };
}

export function plain(filename: string, code: string): CodeSample {
  return { language: "plaintext", filename, code: code.trim() };
}

/** Merge sample maps; later keys win on collision. */
export function mergeSamples(
  ...maps: ReadonlyArray<Readonly<Record<string, readonly CodeSample[]>>>
): Record<string, readonly CodeSample[]> {
  return Object.assign({}, ...maps);
}
