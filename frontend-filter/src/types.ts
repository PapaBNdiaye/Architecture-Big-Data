export interface Row {
  metric_date: string; // "YYYY-MM" ou "YYYY-MM-DD"
  location: string; // "City,CC"
  metric_name: string; // "avg_temp_c" | "sum_precip_mm" | "rainy_days" | "temp_amp_c"
  metric_value: number;
  source: "visualcrossing";
}

export interface RunPayload {
  locations: string[];
  startDate: string;
  endDate: string;
  granularity: "days" | "hours";
  metrics: string[];
  agg: "avg_by_month" | "sum_by_month" | "compare_locations";
}

export interface TaskStatus {
  state: "PENDING" | "RUNNING" | "SUCCESS" | "FAILURE";
}

export interface CityPosition {
  name: string;
  x: number; // pourcentage ou pixels
  y: number; // pourcentage ou pixels
}