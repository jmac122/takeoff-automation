export const MEASUREMENT_COLORS = {
  foundation: '#E57373',
  slab: '#FFB74D',
  wall: '#FFF176',
  footing: '#A1887F',
  curb: '#4FC3F7',
  beam: '#7986CB',
  column: '#BA68C8',
  flatwork: '#81C784',
  pavement: '#AED581',
  default: '#90A4AE',
  selected: '#2196F3',
  hover: '#64B5F6',
  approved: '#4CAF50',
  rejected: '#F44336',
  pending: '#FF9800',
} as const;

export function withOpacity(hex: string, opacity: number): string {
  const clamped = Math.max(0, Math.min(1, opacity));
  return `${hex}${Math.round(clamped * 255)
    .toString(16)
    .padStart(2, '0')}`;
}
