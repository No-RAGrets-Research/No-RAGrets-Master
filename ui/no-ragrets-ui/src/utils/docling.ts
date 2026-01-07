/**
 * Utilities for loading and parsing Docling JSON files
 */

export interface DoclingDocument {
  schema_name: "DoclingDocument";
  version: string;
  name: string;
  origin: {
    mimetype: string;
    binary_hash: string;
    filename: string;
  };
  furniture: {
    self_ref: string;
    children: Array<{ $ref: string }>;
    name: string;
    label: string;
  };
  body: {
    self_ref: string;
    children: Array<{ $ref: string }>;
    name: string;
    label: string;
  };
  texts: DoclingText[];
  pictures: DoclingPicture[];
  tables: DoclingTable[];
  groups?: DoclingGroup[];
  key_value_items?: any[];
}

export interface DoclingGroup {
  self_ref: string; // "#/groups/0"
  children: Array<{ $ref: string }>;
  name: string;
  label: string;
}

export interface DoclingText {
  self_ref: string; // "#/texts/42"
  text: string;
  label: "text" | "section_header" | "caption" | "page_header" | "page_footer";
  prov: DoclingProvenance[];
}

export interface DoclingPicture {
  self_ref: string; // "#/pictures/5"
  prov: DoclingProvenance[];
  label?: "figure" | "image";
  data?: {
    width?: number;
    height?: number;
    mimetype?: string;
    image?: string;
  };
}

export interface DoclingTable {
  self_ref: string; // "#/tables/2"
  prov: DoclingProvenance[];
  label?: "table";
  data?: {
    grid: DoclingTableCell[][];
    num_rows: number;
    num_cols: number;
    table_cells: DoclingTableCell[];
  };
}

export interface DoclingTableCell {
  bbox?: {
    l: number;
    t: number;
    r: number;
    b: number;
    coord_origin: string;
  };
  row_span: number;
  col_span: number;
  start_row_offset_idx: number;
  end_row_offset_idx: number;
  start_col_offset_idx: number;
  end_col_offset_idx: number;
  text: string;
  column_header: boolean;
  row_header: boolean;
  row_section: boolean;
  fillable: boolean;
}

export interface DoclingProvenance {
  page_no: number; // 1-indexed
  bbox: {
    l: number; // Left (normalized 0-1)
    t: number; // Top (normalized 0-1)
    r: number; // Right (normalized 0-1)
    b: number; // Bottom (normalized 0-1)
    coord_origin: string; // "TOPLEFT"
  };
  charspan?: [number, number];
}

export type DoclingItem =
  | { type: "text"; data: DoclingText }
  | { type: "picture"; data: DoclingPicture }
  | { type: "table"; data: DoclingTable };

export interface ParsedDocument {
  items: DoclingItem[];
  texts: DoclingText[];
  pictures: DoclingPicture[];
  tables: DoclingTable[];
}

/**
 * Load docling JSON for a given paper filename
 * @param paperFilename - e.g., "A. Priyadarsini et al. 2023.pdf"
 * @returns Parsed DoclingDocument
 */
export async function loadDoclingData(
  paperFilename: string
): Promise<DoclingDocument> {
  // Remove .pdf extension and add .json
  const jsonFilename = paperFilename.replace(/\.pdf$/i, ".json");

  const response = await fetch(`/docling_json/${jsonFilename}`);

  if (!response.ok) {
    throw new Error(
      `Failed to load docling JSON: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Parse docling document structure by resolving $ref pointers
 * @param docling - Raw DoclingDocument
 * @returns ParsedDocument with resolved items in body order
 */
export function parseDoclingDocument(
  docling: DoclingDocument
): ParsedDocument {
  const { body, texts, pictures, tables, groups = [] } = docling;

  /**
   * Recursively resolve a $ref pointer
   */
  function resolveRef(path: string): DoclingItem | DoclingItem[] | null {
    // Remove the leading "#/" if present
    const cleanPath = path.startsWith("#/") ? path.substring(2) : path;
    const parts = cleanPath.split("/"); // ["texts", "0"] or ["groups", "3"]

    if (parts.length !== 2) {
      console.warn(`Invalid $ref format: ${path}`);
      return null;
    }

    const [type, indexStr] = parts;
    const index = parseInt(indexStr, 10);

    if (isNaN(index)) {
      console.warn(`Invalid index in $ref: ${path}`);
      return null;
    }

    switch (type) {
      case "texts":
        if (texts[index]) {
          return { type: "text" as const, data: texts[index] };
        }
        break;
      case "pictures":
        if (pictures[index]) {
          return { type: "picture" as const, data: pictures[index] };
        }
        break;
      case "tables":
        if (tables[index]) {
          return { type: "table" as const, data: tables[index] };
        }
        break;
      case "groups":
        // Groups contain children - recursively resolve them
        if (groups[index]) {
          const group = groups[index];
          const groupItems = group.children
            .map((childRef) => resolveRef(childRef.$ref))
            .flat()
            .filter((item): item is DoclingItem => item !== null);
          return groupItems;
        }
        break;
      default:
        console.warn(`Unknown type in $ref: ${type}`);
    }

    return null;
  }

  // Resolve $ref pointers from body.children
  const items: DoclingItem[] = body.children
    .map((ref) => resolveRef(ref.$ref))
    .flat()
    .filter((item): item is DoclingItem => item !== null);

  return {
    items,
    texts,
    pictures,
    tables,
  };
}

/**
 * Get page number from provenance data
 */
export function getPageNumber(prov: DoclingProvenance[]): number | null {
  return prov.length > 0 ? prov[0].page_no : null;
}

/**
 * Check if two bounding boxes intersect
 */
export function doesBboxIntersect(
  bbox1: DoclingProvenance["bbox"],
  bbox2: DoclingProvenance["bbox"]
): boolean {
  return !(
    bbox1.r < bbox2.l ||
    bbox1.l > bbox2.r ||
    bbox1.b < bbox2.t ||
    bbox1.t > bbox2.b
  );
}
