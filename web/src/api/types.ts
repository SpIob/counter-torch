export type Range = { min: number | null; max: number | null; unit: string };
export type Conf = "high" | "medium" | "low" | "inferred" | "unknown";
export type ReviewStatus = "seed" | "extracted" | "verified" | "disputed";
export type Dim = "o2_percent" | "pressure_psi" | "gravity_g" | "airflow";
export type SourceRef = { kind: string; url: string | null; note: string };

export type CoveragePoint = {
  id: string; name: string; family: string; status: string; review_status: ReviewStatus;
  psi_accession: string | null; project_type: string | null; psi_files: number | null; psi_size_mb: number | null;
  fuel_phase: string | null; safety_functions: string[] | null;
  o2_percent: Range | null; pressure_psi: Range | null; gravity_g: Range | null; airflow: Range | null;
  confidence: Record<Dim, Conf>; unplaced_dims: Dim[];
};
export type Habitat = { id: string; name: string; o2_percent: Range | null; pressure_psi: Range | null; gravity_g: Range | null; basis: string };
export type Gap = { habitat_id: string; dimension: string; message: string };
export type Coverage = { points: CoveragePoint[]; habitats: Habitat[]; gaps: Gap[]; facts: string[] };
export type ZoneCount = { habitat_id: string; name: string; count: number };
export type TestPoints = { total: number; zones: ZoneCount[]; investigations: { id: string; accession: string; name: string; points: [number, number][] }[] };

export type Sourced<T> = { value: T | null; confidence: Conf; sources: SourceRef[]; note?: string };
export type Investigation = {
  id: string; name: string; aliases: string[]; family: string; status: string;
  in_psi: boolean | null; psi_url: string | null; psi_accession?: string | null; project_type?: string | null;
  platform: Sourced<string>; objective: Sourced<string>; safety_functions: Sourced<string[]>; fuel_phase: Sourced<string>;
  fuel_materials: Sourced<string[]>; fuel_geometry: Sourced<string>;
  hardware: { facility: Sourced<string>; apparatus: Sourced<string>; shared_with: string[] };
  conditions: { o2_percent: Sourced<Range>; pressure_psi: Sourced<Range>; airflow: Sourced<Range>; gravity_g: Sourced<Range>; diluents: Sourced<string[]> };
  variables_swept: Sourced<string[]>; held_constant: Sourced<string[]>; sensors: Sourced<string[]>;
  relevance_notes: Sourced<string>; earth_applications: Sourced<string[]>;
  publications: { title?: string; url?: string | null; doi?: string | null }[];
  review: { status: ReviewStatus; extracted_by: string | null; verified_by: string | null; verified_at: string | null; notes: string[] };
};

export type Scenario = { habitat_id?: string | null; o2_percent?: Range | null; pressure_psi?: Range | null; gravity_g?: Range | null; airflow?: Range | null };
export type RankedItem = {
  id: string; name: string; score: number; components: { conditions: number; function: number; fuel: number; evidence: number };
  unknown_dims: Dim[]; bounding: boolean; review_status: ReviewStatus; why: string; sources: SourceRef[];
};
export type RankResponse = { items: RankedItem[]; coverage_note: string | null };
export type Citation = { id: string; field?: string | null; url: string | null; note: string };
export type AskResponse = { answer: string; citations: Citation[]; coverage_gap: boolean; mode: "live" | "offline" };
